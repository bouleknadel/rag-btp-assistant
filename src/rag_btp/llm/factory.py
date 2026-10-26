"""Fabrique de modèles de chat multi-fournisseurs (Groq, OpenAI, Gemini).

Le fournisseur principal et l'ordre des fallbacks viennent de la configuration
(``LLM_PROVIDER``, ``LLM_FALLBACKS``). Les fournisseurs sans clé API sont ignorés :
on peut donc faire tourner le projet avec une seule clé, quelle qu'elle soit.

En cas d'erreur du fournisseur principal (quota, indisponibilité, timeout),
LangChain bascule automatiquement sur le suivant grâce à ``with_fallbacks``.
"""

from __future__ import annotations

import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable

from rag_btp.config import LLMProviderName, Settings, get_settings

logger = logging.getLogger(__name__)

_API_KEY_FIELD: dict[str, str] = {
    "groq": "groq_api_key",
    "openai": "openai_api_key",
    "gemini": "google_api_key",
}


class NoLLMConfiguredError(RuntimeError):
    """Aucun fournisseur LLM n'a de clé API configurée."""


def has_api_key(provider: LLMProviderName, settings: Settings) -> bool:
    key = getattr(settings, _API_KEY_FIELD[provider])
    return key is not None and bool(key.get_secret_value().strip())


def provider_chain(settings: Settings | None = None) -> list[LLMProviderName]:
    """Fournisseur principal puis fallbacks, sans doublon, limités à ceux qui ont une clé."""
    settings = settings or get_settings()
    ordered: list[LLMProviderName] = []
    for provider in [settings.llm_provider, *settings.llm_fallbacks]:
        if provider not in ordered and has_api_key(provider, settings):
            ordered.append(provider)
    return ordered


def model_name(provider: LLMProviderName, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    return {
        "groq": settings.groq_model,
        "openai": settings.openai_model,
        "gemini": settings.gemini_model,
    }[provider]


def build_chat_model(provider: LLMProviderName, settings: Settings | None = None) -> BaseChatModel:
    """Instancie le modèle de chat d'un fournisseur donné."""
    settings = settings or get_settings()
    api_key = getattr(settings, _API_KEY_FIELD[provider])
    common = {
        "temperature": settings.llm_temperature,
        "max_retries": settings.llm_max_retries,
    }

    if provider == "groq":
        from langchain_groq import ChatGroq

        extra = {}
        if settings.groq_model.startswith("openai/gpt-oss"):
            extra["reasoning_effort"] = settings.groq_reasoning_effort
        return ChatGroq(
            model=settings.groq_model,
            api_key=api_key,
            timeout=settings.llm_timeout,
            **extra,
            **common,
        )
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.openai_model, api_key=api_key, timeout=settings.llm_timeout, **common
        )
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        extra = {}
        if settings.gemini_model.startswith("gemini-3"):
            # Réflexion réduite : beaucoup plus rapide, suffisant pour du RAG.
            extra["thinking_level"] = settings.gemini_thinking_level
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=api_key,
            timeout=settings.llm_timeout,
            **extra,
            **common,
        )
    raise ValueError(f"Fournisseur LLM inconnu : {provider}")


def _log_failures(model: BaseChatModel, provider: LLMProviderName, settings: Settings) -> Runnable:
    """Journalise l'échec d'un fournisseur (sinon masqué par la bascule de fallback)."""
    name = f"{provider}/{model_name(provider, settings)}"

    def on_error(run) -> None:
        logger.warning("Échec du LLM %s : %s", name, str(run.error).splitlines()[0][:300])

    return model.with_listeners(on_error=on_error)


def get_llm(settings: Settings | None = None) -> Runnable:
    """Modèle principal, avec bascule automatique sur les fournisseurs suivants."""
    settings = settings or get_settings()
    providers = provider_chain(settings)
    if not providers:
        raise NoLLMConfiguredError(
            "Aucune clé API LLM trouvée : renseignez GROQ_API_KEY, OPENAI_API_KEY "
            "ou GOOGLE_API_KEY dans le fichier .env."
        )
    models = [_log_failures(build_chat_model(p, settings), p, settings) for p in providers]
    logger.info(
        "LLM : %s (fallbacks : %s)",
        f"{providers[0]}/{model_name(providers[0], settings)}",
        ", ".join(providers[1:]) or "aucun",
    )
    return models[0].with_fallbacks(models[1:]) if len(models) > 1 else models[0]
