"""Graphe RAG orchestré avec LangGraph."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import BaseModel

from rag_btp.config import get_settings
from rag_btp.graph.rag_graph import NOT_FOUND_MESSAGE, RAGState, build_rag_graph
from rag_btp.prompts import get_prompts


class RAGAnswer(BaseModel):
    """Résultat d'une question posée au graphe RAG."""

    question: str
    answer: str
    status: str
    sources: list[dict[str, Any]]
    search_query: str | None = None
    attempts: int = 1
    prompt_version: str
    # Détail de la dernière recherche (pour le débogage et l'évaluation).
    retrieved: list[dict[str, Any]] = []
    grade_raw: str | None = None


@lru_cache
def get_rag_graph(prompt_version: str | None = None):
    """Graphe configuré à partir des paramètres (un graphe par version de prompts)."""
    from rag_btp.llm import get_llm
    from rag_btp.retrieval import get_retriever

    return build_rag_graph(
        retriever=get_retriever(),
        llm=get_llm(),
        prompts=get_prompts(prompt_version),
        max_query_rewrites=get_settings().max_query_rewrites,
    )


def answer_question(
    question: str,
    chantier: str | None = None,
    doc_type: str | None = None,
    prompt_version: str | None = None,
    graph=None,
) -> RAGAnswer:
    """Pose une question au graphe RAG et retourne la réponse avec ses sources."""
    version = get_prompts(prompt_version).version
    graph = graph or get_rag_graph(version)
    state = graph.invoke(
        {"question": question, "chantier": chantier, "doc_type": doc_type},
        config={
            "run_name": "rag_btp_question",
            "tags": ["rag", "qa", f"prompts-{version}"],
            "metadata": {"prompt_version": version, "chantier": chantier},
        },
    )

    def key(doc) -> str:
        return doc.id or doc.page_content

    kept = {key(doc) for doc in state.get("relevant_documents", [])}
    retrieved = [
        {
            "index": i,
            "source": doc.metadata.get("source"),
            "page": doc.metadata.get("page"),
            "rerank_score": doc.metadata.get("rerank_score"),
            "kept": key(doc) in kept,
        }
        for i, doc in enumerate(state.get("documents", []), start=1)
    ]
    return RAGAnswer(
        question=question,
        answer=state["answer"],
        status=state["status"],
        sources=state.get("sources", []),
        search_query=state.get("search_query"),
        attempts=state.get("attempts", 1),
        prompt_version=version,
        retrieved=retrieved,
        grade_raw=state.get("grade_raw"),
    )


__all__ = [
    "NOT_FOUND_MESSAGE",
    "RAGAnswer",
    "RAGState",
    "answer_question",
    "build_rag_graph",
    "get_rag_graph",
]
