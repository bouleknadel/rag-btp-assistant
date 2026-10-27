"""Tracing LangSmith.

Le tracing est natif dans LangChain / LangGraph : il suffit de définir dans ``.env`` :

    LANGSMITH_TRACING=true
    LANGSMITH_API_KEY=lsv2_...
    LANGSMITH_PROJECT=rag-btp-assistant

Chaque question devient alors une trace « rag_btp_question » dans LangSmith, avec le
détail de chaque nœud du graphe (retrieve, grade, rewrite, generate), les documents
retrouvés, les prompts envoyés, les tokens et la latence de chaque appel au LLM.
Les traces sont étiquetées avec la version des prompts (tag ``prompts-v3``…).
"""

from __future__ import annotations

import os

_TRUE = {"1", "true", "yes", "on"}


def tracing_enabled() -> bool:
    """Vrai si les traces sont envoyées à LangSmith (variable activée + clé présente)."""
    flag = os.getenv("LANGSMITH_TRACING") or os.getenv("LANGCHAIN_TRACING_V2") or ""
    key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    return flag.strip().lower() in _TRUE and bool(key)


def langsmith_project() -> str:
    return os.getenv("LANGSMITH_PROJECT") or os.getenv("LANGCHAIN_PROJECT") or "default"
