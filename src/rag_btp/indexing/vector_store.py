"""Vector store ChromaDB persistant et indexation idempotente des chunks.

L'indexation est conçue pour être relancée sans risque :
- les chunks ont des identifiants déterministes, l'écriture est un *upsert* ;
- pour chaque document réindexé, les anciens chunks qui n'existent plus
  (document modifié) sont supprimés, ce qui évite les doublons obsolètes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from rag_btp.config import get_settings

logger = logging.getLogger(__name__)

BATCH_SIZE = 128


@dataclass
class IndexingReport:
    """Bilan d'une indexation."""

    documents: int = 0
    chunks_upserted: int = 0
    chunks_deleted: int = 0
    total_in_collection: int = 0


def get_vector_store(
    embeddings: Embeddings | None = None,
    persist_dir: Path | None = None,
    collection_name: str | None = None,
) -> Chroma:
    """Ouvre (ou crée) la collection Chroma persistante."""
    settings = get_settings()
    if embeddings is None:
        from rag_btp.indexing.embeddings import get_embeddings

        embeddings = get_embeddings()

    path = Path(persist_dir or settings.chroma_persist_dir)
    path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(path), settings=ChromaSettings(anonymized_telemetry=False)
    )
    return Chroma(
        client=client,
        collection_name=collection_name or settings.chroma_collection,
        embedding_function=embeddings,
        collection_metadata={"hnsw:space": "cosine"},
    )


def collection_count(store: Chroma) -> int:
    return store._collection.count()


def index_chunks(chunks: list[Document], store: Chroma) -> IndexingReport:
    """Indexe des chunks (upsert) et supprime les chunks obsolètes de leurs sources."""
    report = IndexingReport()
    by_source: dict[str, list[Document]] = {}
    for chunk in chunks:
        by_source.setdefault(chunk.metadata["source"], []).append(chunk)
    report.documents = len(by_source)

    for source, source_chunks in by_source.items():
        new_ids = {c.id for c in source_chunks}
        existing = store.get(where={"source": source}, include=[])["ids"]
        stale = [chunk_id for chunk_id in existing if chunk_id not in new_ids]
        if stale:
            store.delete(ids=stale)
            report.chunks_deleted += len(stale)
            logger.info("%s : %d chunk(s) obsolète(s) supprimé(s)", source, len(stale))

    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start : start + BATCH_SIZE]
        store.add_documents(batch, ids=[c.id for c in batch])
        report.chunks_upserted += len(batch)

    report.total_in_collection = collection_count(store)
    return report


def reset_collection(store: Chroma) -> None:
    """Vide entièrement la collection (réindexation complète)."""
    store.reset_collection()
