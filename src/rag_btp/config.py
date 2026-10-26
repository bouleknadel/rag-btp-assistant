"""Configuration centralisée, chargée depuis les variables d'environnement / `.env`.

Toutes les clés API et tous les paramètres réglables passent par ici :
aucun secret n'est écrit en dur dans le code.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from dotenv import load_dotenv
from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Charge `.env` dans os.environ : nécessaire pour que LangSmith / LangChain
# lisent directement LANGSMITH_* sans passer par l'objet Settings.
load_dotenv(PROJECT_ROOT / ".env")

LLMProviderName = Literal["groq", "openai", "gemini"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM ---------------------------------------------------------------
    llm_provider: LLMProviderName = "groq"
    # NoDecode : la valeur brute ("openai,gemini") est passée au validateur
    # au lieu d'être interprétée comme du JSON.
    llm_fallbacks: Annotated[list[LLMProviderName], NoDecode] = Field(
        default_factory=lambda: ["openai", "gemini"]
    )
    llm_temperature: float = 0.1

    groq_api_key: SecretStr | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4o-mini"
    # Accepte les deux noms usuels de la clé Gemini.
    google_api_key: SecretStr | None = Field(
        default=None, validation_alias=AliasChoices("GOOGLE_API_KEY", "GEMINI_API_KEY")
    )
    gemini_model: str = "gemini-2.0-flash"

    # --- Embeddings & reranking ----------------------------------------------
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    reranker_model: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

    # --- Vector store ---------------------------------------------------------
    chroma_persist_dir: Path = PROJECT_ROOT / "data" / "chroma"
    chroma_collection: str = "btp_documents"

    # --- Ingestion & retrieval --------------------------------------------------
    raw_data_dir: Path = PROJECT_ROOT / "data" / "raw"
    chunk_size: int = 800
    chunk_overlap: int = 120
    retrieval_top_k: int = 20
    rerank_top_n: int = 5

    # --- LangSmith --------------------------------------------------------------
    langsmith_tracing: bool = False
    langsmith_project: str = "rag-btp-assistant"

    @field_validator("llm_fallbacks", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        """Autorise `LLM_FALLBACKS=openai,gemini` dans le `.env`."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("chroma_persist_dir", "raw_data_dir", mode="after")
    @classmethod
    def _resolve_path(cls, value: Path) -> Path:
        """Les chemins relatifs sont résolus depuis la racine du projet."""
        return value if value.is_absolute() else PROJECT_ROOT / value


@lru_cache
def get_settings() -> Settings:
    """Instance unique des paramètres (mise en cache)."""
    return Settings()
