"""Modèle d'embeddings local (sentence-transformers via Hugging Face).

Le modèle par défaut, ``paraphrase-multilingual-MiniLM-L12-v2``, est multilingue
(le corpus est en français), léger (~470 Mo, vecteurs de dimension 384) et tourne
sur CPU : aucune clé API n'est nécessaire. Il est téléchargé au premier appel
puis mis en cache par Hugging Face.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.embeddings import Embeddings

from rag_btp.config import get_settings


@lru_cache
def get_embeddings(model_name: str | None = None) -> Embeddings:
    """Instance unique du modèle d'embeddings (chargé une seule fois)."""
    from langchain_huggingface import HuggingFaceEmbeddings  # import lourd (torch)

    return HuggingFaceEmbeddings(
        model_name=model_name or get_settings().embedding_model,
        model_kwargs={"device": "cpu"},
        # Vecteurs normalisés : la similarité cosinus devient un simple produit scalaire.
        encode_kwargs={"normalize_embeddings": True},
    )
