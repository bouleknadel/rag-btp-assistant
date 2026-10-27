"""Modèle d'embeddings local (sentence-transformers via Hugging Face).

Modèle par défaut : ``intfloat/multilingual-e5-small``
- multilingue (le corpus est en français) et entraîné pour la *recherche*
  documentaire (question → passage), pas seulement pour la similarité de phrases ;
- lit jusqu'à 512 tokens : un chunk de 800 caractères est encodé en entier ;
- léger (~470 Mo, vecteurs de dimension 384), exécutable sur CPU, sans clé API.

Les modèles E5 attendent un préfixe : ``query: `` pour les questions et
``passage: `` pour les documents indexés (configurables dans ``.env``).

Historique : la première version utilisait ``paraphrase-multilingual-MiniLM-L12-v2``,
qui tronque les textes à 128 tokens (~80 mots) : la fin des chunks n'était jamais
encodée et certaines réponses étaient introuvables (voir docs/iterations.md).
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.embeddings import Embeddings

from rag_btp.config import get_settings


@lru_cache
def get_embeddings(model_name: str | None = None) -> Embeddings:
    """Instance unique du modèle d'embeddings (chargé une seule fois)."""
    from langchain_huggingface import HuggingFaceEmbeddings  # import lourd (torch)

    settings = get_settings()
    # Vecteurs normalisés : la similarité cosinus devient un simple produit scalaire.
    passage_kwargs = {"normalize_embeddings": True}
    query_kwargs = {"normalize_embeddings": True}
    if settings.embedding_passage_prefix:
        passage_kwargs["prompt"] = settings.embedding_passage_prefix
    if settings.embedding_query_prefix:
        query_kwargs["prompt"] = settings.embedding_query_prefix

    return HuggingFaceEmbeddings(
        model_name=model_name or settings.embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs=passage_kwargs,
        query_encode_kwargs=query_kwargs,
    )
