"""Prompts versionnés (questions-réponses et synthèse de rapports).

Chaque version est un module ``vN.py`` dont l'en-tête documente les problèmes
observés avec la version précédente et les changements apportés.
La version active est choisie par ``PROMPT_VERSION`` dans le ``.env`` (défaut : v3),
ce qui permet de comparer les versions avec le script d'évaluation.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import ModuleType

from langchain_core.prompts import ChatPromptTemplate

from rag_btp.prompts import v1, v2, v3

VERSIONS: dict[str, ModuleType] = {"v1": v1, "v2": v2, "v3": v3}
LATEST_VERSION = "v3"


@dataclass(frozen=True)
class PromptSet:
    """Jeu de prompts utilisé par le graphe RAG et la synthèse de rapports."""

    version: str
    grade: ChatPromptTemplate
    rewrite: ChatPromptTemplate
    answer: ChatPromptTemplate
    summary: ChatPromptTemplate


def get_prompts(version: str | None = None) -> PromptSet:
    """Jeu de prompts d'une version donnée (par défaut : celle de la configuration)."""
    if version is None:
        from rag_btp.config import get_settings

        version = get_settings().prompt_version
    if version not in VERSIONS:
        raise ValueError(f"Version de prompts inconnue : {version} ({', '.join(VERSIONS)})")
    module = VERSIONS[version]
    return PromptSet(
        version=module.VERSION,
        grade=module.GRADE_PROMPT,
        rewrite=module.REWRITE_PROMPT,
        answer=module.ANSWER_PROMPT,
        summary=module.SUMMARY_PROMPT,
    )


__all__ = ["LATEST_VERSION", "VERSIONS", "PromptSet", "get_prompts"]
