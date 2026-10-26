"""Graphe RAG correctif orchestré avec LangGraph.

Contrairement à une chaîne linéaire (recherche → réponse), le graphe vérifie la
pertinence des documents avant de répondre et se corrige si besoin :

    START → retrieve → grade ─┬─(documents pertinents)──────────→ generate → END
                 ▲            ├─(aucun, essais restants)→ rewrite ─┐
                 └────────────┼────────────────────────────────────┘
                              └─(aucun, essais épuisés)──────────→ not_found → END

- ``retrieve``  : recherche vectorielle + reranking (``BTPRetriever``) ;
- ``grade``     : le LLM sélectionne les extraits réellement utiles (un seul appel) ;
- ``rewrite``   : reformule la question si rien de pertinent n'a été trouvé ;
- ``generate``  : rédige la réponse en citant ses sources [n] ;
- ``not_found`` : réponse explicite plutôt qu'une hallucination.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Literal, TypedDict

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import Runnable
from langgraph.graph import END, START, StateGraph

from rag_btp.prompts import PromptSet

logger = logging.getLogger(__name__)

NOT_FOUND_MESSAGE = (
    "Je n'ai pas trouvé cette information dans les documents de chantier disponibles."
)


class RAGState(TypedDict, total=False):
    """État partagé entre les nœuds du graphe."""

    question: str
    chantier: str | None
    doc_type: str | None
    search_query: str
    attempts: int
    documents: list[Document]
    relevant_documents: list[Document]
    answer: str
    sources: list[dict[str, Any]]
    status: Literal["answered", "not_found"]


# --- Utilitaires --------------------------------------------------------------------
def format_context(documents: list[Document]) -> str:
    """Extraits numérotés [1], [2]… avec leur source, pour le LLM."""
    blocks = []
    for i, doc in enumerate(documents, start=1):
        meta = doc.metadata
        header = f"[{i}] {meta.get('title', '')} — {meta.get('source', '')}, p. {meta.get('page')}"
        body = doc.page_content.split("\n", 1)[-1]  # retire l'en-tête de contexte du chunk
        blocks.append(f"{header}\n{body}")
    return "\n\n".join(blocks)


def parse_relevant_indices(text: str, n_documents: int) -> list[int] | None:
    """Extrait la liste des numéros pertinents de la réponse JSON du LLM.

    Retourne ``None`` si la réponse est illisible (le graphe garde alors tous les documents).
    """
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
        values = data.get("pertinents", data.get("relevant", []))
        indices = sorted({int(v) for v in values})
    except (ValueError, TypeError, AttributeError):
        return None
    return [i for i in indices if 1 <= i <= n_documents]


def extract_citations(answer: str) -> set[int]:
    """Numéros cités dans la réponse : [1], [2, 3], [1][4]…"""
    cited: set[int] = set()
    for group in re.findall(r"\[(\d+(?:\s*[,;]\s*\d+)*)\]", answer):
        cited.update(int(n) for n in re.split(r"[,;]", group))
    return cited


def source_info(index: int, doc: Document, cited: set[int]) -> dict[str, Any]:
    meta = doc.metadata
    return {
        "index": index,
        "source": meta.get("source"),
        "title": meta.get("title"),
        "page": meta.get("page"),
        "chantier": meta.get("chantier"),
        "doc_type": meta.get("doc_type"),
        "rerank_score": meta.get("rerank_score"),
        "cited": index in cited,
        "excerpt": doc.page_content.split("\n", 1)[-1][:300],
    }


# --- Construction du graphe ----------------------------------------------------------
def build_rag_graph(
    retriever: BaseRetriever,
    llm: Runnable,
    prompts: PromptSet,
    max_query_rewrites: int = 1,
):
    """Compile le graphe RAG avec ses dépendances (injectées : testable sans API)."""
    to_text = StrOutputParser()

    def retrieve(state: RAGState) -> RAGState:
        query = state.get("search_query") or state["question"]
        documents = retriever.invoke(
            query, chantier=state.get("chantier"), doc_type=state.get("doc_type")
        )
        return {"documents": documents, "attempts": state.get("attempts", 0) + 1}

    def grade(state: RAGState) -> RAGState:
        documents = state.get("documents", [])
        if not documents:
            return {"relevant_documents": []}
        chain = prompts.grade | llm | to_text
        response = chain.invoke(
            {"question": state["question"], "context": format_context(documents)}
        )
        indices = parse_relevant_indices(response, len(documents))
        if indices is None:
            logger.warning("Réponse de pertinence illisible, documents conservés : %r", response)
            return {"relevant_documents": documents}
        return {"relevant_documents": [documents[i - 1] for i in indices]}

    def route_after_grade(state: RAGState) -> str:
        if state.get("relevant_documents"):
            return "generate"
        if state.get("attempts", 0) <= max_query_rewrites:
            return "rewrite"
        return "not_found"

    def rewrite(state: RAGState) -> RAGState:
        chain = prompts.rewrite | llm | to_text
        query = chain.invoke({"question": state["question"]}).strip().strip('"«» ')
        return {"search_query": query or state["question"]}

    def generate(state: RAGState) -> RAGState:
        documents = state["relevant_documents"]
        chain = prompts.answer | llm | to_text
        answer = chain.invoke(
            {"question": state["question"], "context": format_context(documents)}
        ).strip()
        cited = extract_citations(answer)
        sources = [source_info(i, doc, cited) for i, doc in enumerate(documents, start=1)]
        return {"answer": answer, "sources": sources, "status": "answered"}

    def not_found(state: RAGState) -> RAGState:
        return {"answer": NOT_FOUND_MESSAGE, "sources": [], "status": "not_found"}

    graph = StateGraph(RAGState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("grade", grade)
    graph.add_node("rewrite", rewrite)
    graph.add_node("generate", generate)
    graph.add_node("not_found", not_found)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges(
        "grade",
        route_after_grade,
        {"generate": "generate", "rewrite": "rewrite", "not_found": "not_found"},
    )
    graph.add_edge("rewrite", "retrieve")
    graph.add_edge("generate", END)
    graph.add_edge("not_found", END)
    return graph.compile()
