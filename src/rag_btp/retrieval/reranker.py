"""Reranking des résultats de la recherche vectorielle.

La recherche vectorielle (bi-encoder) est rapide mais approximative : la question
et les chunks sont encodés séparément. Un *cross-encoder* lit la question et le
chunk ensemble et produit un score de pertinence bien plus fin, mais il est trop
lent pour parcourir tout le corpus. On l'applique donc seulement aux ``top_k``
candidats de la recherche vectorielle pour n'en garder que les ``top_n`` meilleurs.

Modèle par défaut : ``cross-encoder/mmarco-mMiniLMv2-L12-H384-v1``, multilingue
(entraîné sur mMARCO, dont le français), léger et exécutable sur CPU.
"""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Protocol, runtime_checkable

from langchain_core.documents import Document

from rag_btp.config import get_settings


@runtime_checkable
class Reranker(Protocol):
    """Interface commune : permet de remplacer le modèle (ou de le simuler en test)."""

    def score(self, query: str, documents: list[Document]) -> list[float]:
        """Score de pertinence de chaque document pour la requête (plus haut = meilleur)."""
        ...


class CrossEncoderReranker:
    """Reranker basé sur un cross-encoder sentence-transformers (local)."""

    def __init__(self, model_name: str | None = None, max_length: int = 512) -> None:
        from sentence_transformers import CrossEncoder  # import lourd (torch)

        self.model_name = model_name or get_settings().reranker_model
        self._model = CrossEncoder(self.model_name, device="cpu", max_length=max_length)

    def score(self, query: str, documents: list[Document]) -> list[float]:
        if not documents:
            return []
        pairs = [(query, doc.page_content) for doc in documents]
        logits = self._model.predict(pairs, show_progress_bar=False)
        # Le modèle renvoie un score brut (logit, éventuellement négatif) : la sigmoïde
        # le convertit en probabilité de pertinence entre 0 et 1, sans changer l'ordre.
        return [1.0 / (1.0 + math.exp(-float(x))) for x in logits]


@lru_cache
def get_reranker(model_name: str | None = None) -> Reranker:
    """Instance unique du reranker (modèle chargé une seule fois)."""
    return CrossEncoderReranker(model_name)
