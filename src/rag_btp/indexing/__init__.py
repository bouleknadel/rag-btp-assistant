"""Indexation : génération des embeddings et stockage dans ChromaDB."""

from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma

from rag_btp.config import get_settings
from rag_btp.indexing.vector_store import (
    IndexingReport,
    collection_count,
    get_vector_store,
    index_chunks,
    reset_collection,
)
from rag_btp.ingestion import ingest_directory, load_file, split_documents


def index_directory(
    directory: Path | None = None,
    store: Chroma | None = None,
    reset: bool = False,
) -> IndexingReport:
    """Pipeline complet : chargement → chunking → embeddings → ChromaDB."""
    store = store or get_vector_store()
    if reset:
        reset_collection(store)
    chunks = ingest_directory(directory or get_settings().raw_data_dir)
    return index_chunks(chunks, store)


def index_files(paths: list[Path], base_dir: Path, store: Chroma) -> IndexingReport:
    """Indexe une liste de fichiers (ex. documents envoyés via l'API ou n8n).

    ``base_dir`` sert à calculer la ``source`` (chemin relatif), identique à celle
    d'une indexation complète du dossier : réindexer un fichier remplace ses chunks.
    """
    settings = get_settings()
    documents = []
    for path in paths:
        documents.extend(load_file(path, base_dir=base_dir))
    chunks = split_documents(documents, settings.chunk_size, settings.chunk_overlap)
    return index_chunks(chunks, store)


__all__ = [
    "index_files",
    "IndexingReport",
    "collection_count",
    "get_vector_store",
    "index_chunks",
    "index_directory",
    "reset_collection",
]
