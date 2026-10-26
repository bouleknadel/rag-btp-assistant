"""Recherche : recherche vectorielle puis reranking des résultats."""

from __future__ import annotations

from rag_btp.config import get_settings
from rag_btp.retrieval.reranker import CrossEncoderReranker, Reranker, get_reranker
from rag_btp.retrieval.retriever import BTPRetriever, build_filter


def get_retriever(use_reranker: bool = True) -> BTPRetriever:
    """Retriever configuré à partir des paramètres (``.env``)."""
    from rag_btp.indexing import get_vector_store

    settings = get_settings()
    return BTPRetriever(
        vector_store=get_vector_store(),
        reranker=get_reranker() if use_reranker else None,
        top_k=settings.retrieval_top_k,
        top_n=settings.rerank_top_n,
    )


__all__ = [
    "BTPRetriever",
    "CrossEncoderReranker",
    "Reranker",
    "build_filter",
    "get_reranker",
    "get_retriever",
]
