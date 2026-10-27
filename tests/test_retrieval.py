from pathlib import Path

import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

from rag_btp.config import PROJECT_ROOT
from rag_btp.indexing import get_vector_store, index_chunks
from rag_btp.ingestion import ingest_directory
from rag_btp.retrieval import BTPRetriever, build_filter

RAW_DIR = PROJECT_ROOT / "data" / "raw"


class KeywordReranker:
    """Faux reranker : proportion des mots de la requête présents dans le chunk."""

    def score(self, query: str, documents: list[Document]) -> list[float]:
        words = set(query.lower().split())
        return [
            len(words & set(doc.page_content.lower().split())) / len(words) for doc in documents
        ]


@pytest.fixture(scope="module")
def store(tmp_path_factory):
    """Index des 20 documents de base avec des embeddings factices."""
    store = get_vector_store(
        embeddings=DeterministicFakeEmbedding(size=64),
        persist_dir=tmp_path_factory.mktemp("chroma"),
        collection_name="test-retrieval",
    )
    chunks = [
        c for c in ingest_directory(RAW_DIR) if not c.metadata["source"].startswith("generated/")
    ]
    index_chunks(chunks, store)
    return store


# --- Filtres -----------------------------------------------------------------------
def test_build_filter():
    assert build_filter() is None
    assert build_filter(chantier="tilleuls") == {"chantier": "tilleuls"}
    assert build_filter("tilleuls", "essais") == {
        "$and": [{"chantier": "tilleuls"}, {"doc_type": "essais"}]
    }


# --- Recherche vectorielle seule ------------------------------------------------------
def test_vector_only_returns_top_n_with_scores(store):
    retriever = BTPRetriever(vector_store=store, reranker=None, top_k=10, top_n=3)
    docs = retriever.invoke("béton")
    assert len(docs) == 3
    assert all("vector_score" in d.metadata for d in docs)
    assert all("rerank_score" not in d.metadata for d in docs)


def test_filters_are_applied(store):
    retriever = BTPRetriever(vector_store=store, top_k=10, top_n=10)
    docs = retriever.invoke("réception", chantier="jean-moulin", doc_type="pv_reception")
    assert docs
    assert {(d.metadata["chantier"], d.metadata["doc_type"]) for d in docs} == {
        ("jean-moulin", "pv_reception")
    }


# --- Reranking -------------------------------------------------------------------------
def test_reranking_sorts_by_score(store):
    # top_k = tout le corpus : le bon chunk est forcément parmi les candidats,
    # c'est donc le reranker qui doit le faire remonter en tête.
    retriever = BTPRetriever(vector_store=store, reranker=KeywordReranker(), top_k=60, top_n=5)
    docs = retriever.invoke("vent 72 km/h grue")
    scores = [d.metadata["rerank_score"] for d in docs]
    assert scores == sorted(scores, reverse=True)
    assert docs[0].metadata["doc_type"] == "securite"
    assert "72 km/h" in docs[0].page_content


def test_reranker_does_not_mutate_store_documents(store):
    retriever = BTPRetriever(vector_store=store, reranker=KeywordReranker(), top_k=5, top_n=2)
    retriever.invoke("béton")
    stored = store.get(limit=5, include=["metadatas"])["metadatas"]
    assert all("rerank_score" not in meta for meta in stored)


def test_empty_index_returns_nothing(tmp_path: Path):
    empty = get_vector_store(
        embeddings=DeterministicFakeEmbedding(size=64),
        persist_dir=tmp_path,
        collection_name="empty",
    )
    retriever = BTPRetriever(vector_store=empty, reranker=KeywordReranker())
    assert retriever.invoke("béton") == []


# --- Test d'intégration : vrais modèles (embeddings + cross-encoder) --------------------
@pytest.mark.integration
def test_real_reranker_improves_ranking(tmp_path: Path):
    from rag_btp.indexing.embeddings import get_embeddings
    from rag_btp.retrieval import get_reranker

    real_store = get_vector_store(
        embeddings=get_embeddings(), persist_dir=tmp_path, collection_name="integration"
    )
    chunks = [
        c for c in ingest_directory(RAW_DIR) if not c.metadata["source"].startswith("generated/")
    ]
    index_chunks(chunks, real_store)
    retriever = BTPRetriever(vector_store=real_store, reranker=get_reranker(), top_k=20, top_n=3)

    docs = retriever.invoke("À partir de quelle vitesse de vent faut-il arrêter la grue ?")
    assert "72 km/h" in docs[0].page_content
    assert 0.0 <= docs[0].metadata["rerank_score"] <= 1.0

    # Régression : réponse située en fin de chunk (introuvable avec un modèle à 128 tokens).
    docs = retriever.invoke("Quel est le délai de levée des réserves du lot plâtrerie ?")
    assert docs[0].metadata["doc_type"] == "pv_reception"
    assert "30 jours" in docs[0].page_content
