"""Retriever en deux temps : recherche vectorielle (ChromaDB) puis reranking.

Le retriever hérite de ``BaseRetriever`` de LangChain : il s'intègre donc
directement dans les chaînes / graphes LangChain et apparaît comme une étape
« retriever » dans les traces LangSmith.
"""

from __future__ import annotations

from typing import Any

from langchain_chroma import Chroma
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict

from rag_btp.retrieval.reranker import Reranker


def build_filter(chantier: str | None = None, doc_type: str | None = None) -> dict | None:
    """Construit un filtre de métadonnées Chroma (``None`` si aucun critère)."""
    conditions = [
        {key: value} for key, value in (("chantier", chantier), ("doc_type", doc_type)) if value
    ]
    if not conditions:
        return None
    return conditions[0] if len(conditions) == 1 else {"$and": conditions}


class BTPRetriever(BaseRetriever):
    """Recherche vectorielle ``top_k`` puis reranking cross-encoder ``top_n``.

    Les scores sont ajoutés aux métadonnées de chaque document retourné :
    ``vector_score`` (similarité cosinus) et ``rerank_score`` (cross-encoder).
    Filtres optionnels à l'appel : ``retriever.invoke(q, chantier="tilleuls")``.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    vector_store: Chroma
    reranker: Reranker | None = None
    top_k: int = 20
    top_n: int = 5

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        chantier: str | None = None,
        doc_type: str | None = None,
        **kwargs: Any,
    ) -> list[Document]:
        # Chroma renvoie une distance cosinus (0 = identique) : similarité = 1 - distance.
        candidates = self.vector_store.similarity_search_with_score(
            query, k=self.top_k, filter=build_filter(chantier, doc_type)
        )
        documents = []
        for doc, distance in candidates:
            meta = {**doc.metadata, "vector_score": round(1.0 - float(distance), 4)}
            documents.append(Document(page_content=doc.page_content, metadata=meta, id=doc.id))

        if self.reranker is None or not documents:
            return documents[: self.top_n]

        scores = self.reranker.score(query, documents)
        for doc, score in zip(documents, scores, strict=True):
            doc.metadata["rerank_score"] = round(score, 4)
        documents.sort(key=lambda d: d.metadata["rerank_score"], reverse=True)
        return documents[: self.top_n]
