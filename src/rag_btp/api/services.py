"""Services partagés par l'API, créés une seule fois au démarrage.

Charger les modèles (embeddings, reranker) prend plusieurs secondes : ils sont
initialisés au lancement du serveur, puis réutilisés par toutes les requêtes.
Le conteneur est injectable, ce qui permet de tester l'API avec des modèles factices.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from langchain_chroma import Chroma
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import Runnable

from rag_btp.config import Settings, get_settings
from rag_btp.graph import build_rag_graph
from rag_btp.prompts import get_prompts

logger = logging.getLogger(__name__)


@dataclass
class Services:
    store: Chroma
    retriever: BaseRetriever
    llm: Runnable | None
    settings: Settings
    llm_providers: list[str] = field(default_factory=list)
    _graphs: dict = field(default_factory=dict, repr=False)

    def graph(self, prompt_version: str | None = None):
        """Graphe RAG pour une version de prompts (compilé une fois puis mis en cache)."""
        version = get_prompts(prompt_version).version
        if version not in self._graphs:
            self._graphs[version] = build_rag_graph(
                retriever=self.retriever,
                llm=self.llm,
                prompts=get_prompts(version),
                max_query_rewrites=self.settings.max_query_rewrites,
            )
        return self._graphs[version]

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> Services:
        from rag_btp.indexing import get_vector_store
        from rag_btp.llm import NoLLMConfiguredError, get_llm, provider_chain
        from rag_btp.retrieval import BTPRetriever, get_reranker

        settings = settings or get_settings()
        store = get_vector_store()
        retriever = BTPRetriever(
            vector_store=store,
            reranker=get_reranker(),
            top_k=settings.retrieval_top_k,
            top_n=settings.rerank_top_n,
        )
        try:
            llm = get_llm(settings)
        except NoLLMConfiguredError as exc:
            logger.warning("%s — /ask et /summarize seront indisponibles.", exc)
            llm = None
        return cls(
            store=store,
            retriever=retriever,
            llm=llm,
            settings=settings,
            llm_providers=provider_chain(settings),
        )
