"""Prompts versionnés (questions-réponses et synthèse de rapports)."""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate

from rag_btp.prompts import v1


@dataclass(frozen=True)
class PromptSet:
    """Jeu de prompts utilisé par le graphe RAG."""

    version: str
    grade: ChatPromptTemplate
    rewrite: ChatPromptTemplate
    answer: ChatPromptTemplate


def get_prompts() -> PromptSet:
    return PromptSet(
        version=v1.VERSION,
        grade=v1.GRADE_PROMPT,
        rewrite=v1.REWRITE_PROMPT,
        answer=v1.ANSWER_PROMPT,
    )


__all__ = ["PromptSet", "get_prompts"]
