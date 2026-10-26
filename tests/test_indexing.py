from pathlib import Path

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding

from rag_btp.config import PROJECT_ROOT
from rag_btp.indexing import collection_count, get_vector_store, index_chunks, index_directory
from rag_btp.ingestion import ingest_directory

RAW_DIR = PROJECT_ROOT / "data" / "raw"

DOC_V1 = "# Rapport n° 1\n\n## Avancement\n\nDalle du R+1 coulée.\n\n## Sécurité\n\nRAS."
DOC_V2 = "# Rapport n° 1\n\n## Avancement\n\nDalle du R+1 coulée et décoffrée."


@pytest.fixture
def store(tmp_path: Path):
    """Collection Chroma temporaire avec des embeddings factices (rapides, sans modèle)."""
    return get_vector_store(
        embeddings=DeterministicFakeEmbedding(size=64),
        persist_dir=tmp_path / "chroma",
        collection_name="test",
    )


def test_index_demo_corpus(store):
    report = index_directory(RAW_DIR, store=store)
    # 20 documents de base, + les rapports générés éventuels (--daily-reports).
    assert report.documents >= 20
    assert report.chunks_upserted == report.total_in_collection > 0


def test_reindexing_is_idempotent(store):
    first = index_directory(RAW_DIR, store=store)
    second = index_directory(RAW_DIR, store=store)
    assert second.total_in_collection == first.total_in_collection
    assert second.chunks_deleted == 0


def test_modified_document_replaces_stale_chunks(store, tmp_path: Path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    path = docs_dir / "tilleuls__rapport_journalier__test.md"

    path.write_text(DOC_V1, encoding="utf-8")
    index_chunks(ingest_directory(docs_dir), store)
    path.write_text(DOC_V2, encoding="utf-8")
    report = index_chunks(ingest_directory(docs_dir), store)

    assert report.chunks_deleted >= 1
    stored = store.get(where={"source": path.name})["documents"]
    assert all("RAS" not in text for text in stored)
    assert any("décoffrée" in text for text in stored)


def test_reset_empties_collection(store):
    index_directory(RAW_DIR, store=store)
    report = index_directory(RAW_DIR, store=store, reset=True)
    assert report.total_in_collection == report.chunks_upserted
    assert collection_count(store) == report.chunks_upserted


def test_metadata_filter(store):
    index_directory(RAW_DIR, store=store)
    results = store.similarity_search("planning", k=5, filter={"chantier": "jean-moulin"})
    assert results
    assert all(doc.metadata["chantier"] == "jean-moulin" for doc in results)


# --- Test d'intégration : vrai modèle d'embeddings (téléchargé au 1er lancement) ---
@pytest.mark.integration
def test_real_embeddings_retrieve_relevant_document(tmp_path: Path):
    from rag_btp.indexing.embeddings import get_embeddings

    store = get_vector_store(
        embeddings=get_embeddings(), persist_dir=tmp_path / "chroma", collection_name="integration"
    )
    # Uniquement les 20 documents de base (sans les rapports générés).
    chunks = [
        c for c in ingest_directory(RAW_DIR) if not c.metadata["source"].startswith("generated/")
    ]
    index_chunks(chunks, store)
    results = store.similarity_search("résistance à 28 jours de la dalle du R+2", k=3)
    assert any("essais" in doc.metadata["doc_type"] for doc in results)
