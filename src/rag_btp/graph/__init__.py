"""Graphe RAG orchestré avec LangGraph."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import BaseModel

from rag_btp.config import get_settings
from rag_btp.graph.rag_graph import NOT_FOUND_MESSAGE, RAGState, build_rag_graph


class RAGAnswer(BaseModel):
    """Résultat d'une question posée au graphe RAG."""

    question: str
    answer: str
    status: str
    sources: list[dict[str, Any]]
    search_query: str | None = None
    attempts: int = 1
    prompt_version: str


@lru_cache
def get_rag_graph():
    """Graphe configuré à partir des paramètres (modèles chargés une seule fois)."""
    from rag_btp.llm import get_llm
    from rag_btp.prompts import get_prompts
    from rag_btp.retrieval import get_retriever

    return build_rag_graph(
        retriever=get_retriever(),
        llm=get_llm(),
        prompts=get_prompts(),
        max_query_rewrites=get_settings().max_query_rewrites,
    )


def answer_question(
    question: str,
    chantier: str | None = None,
    doc_type: str | None = None,
    graph=None,
) -> RAGAnswer:
    """Pose une question au graphe RAG et retourne la réponse avec ses sources."""
    from rag_btp.prompts import get_prompts

    graph = graph or get_rag_graph()
    state = graph.invoke(
        {"question": question, "chantier": chantier, "doc_type": doc_type},
        config={"run_name": "rag_btp_question", "tags": ["rag", "qa"]},
    )
    return RAGAnswer(
        question=question,
        answer=state["answer"],
        status=state["status"],
        sources=state.get("sources", []),
        search_query=state.get("search_query"),
        attempts=state.get("attempts", 1),
        prompt_version=get_prompts().version,
    )


__all__ = [
    "NOT_FOUND_MESSAGE",
    "RAGAnswer",
    "RAGState",
    "answer_question",
    "build_rag_graph",
    "get_rag_graph",
]
