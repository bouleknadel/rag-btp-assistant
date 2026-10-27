"""Schémas Pydantic des requêtes et réponses de l'API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from rag_btp.summary import ReportSummary

PromptVersion = Literal["v1", "v2", "v3"]


# --- Santé --------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    documents_indexed: int = Field(description="Nombre de chunks dans ChromaDB")
    llm_providers: list[str] = Field(description="Fournisseur principal puis fallbacks")
    prompt_version: str
    embedding_model: str
    reranker_model: str


# --- Ingestion ------------------------------------------------------------------------
class IngestResponse(BaseModel):
    files: list[str] = Field(description="Fichiers enregistrés et indexés")
    documents: int
    chunks_upserted: int
    chunks_deleted: int
    total_in_collection: int


# --- Questions / réponses ---------------------------------------------------------------
class AskRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=1000,
        examples=["À partir de quelle vitesse de vent faut-il arrêter la grue ?"],
    )
    chantier: str | None = Field(None, examples=["tilleuls"], description="Filtre chantier")
    doc_type: str | None = Field(None, examples=["securite"], description="Filtre type")
    prompt_version: PromptVersion | None = Field(None, description="Défaut : PROMPT_VERSION")
    debug: bool = Field(False, description="Ajoute le détail de la recherche et du tri")


class Source(BaseModel):
    index: int
    source: str | None
    title: str | None
    page: int | None
    chantier: str | None
    doc_type: str | None
    rerank_score: float | None
    cited: bool = Field(description="Extrait cité dans la réponse")
    excerpt: str


class RetrievedDocument(BaseModel):
    index: int
    source: str | None
    page: int | None
    rerank_score: float | None
    kept: bool = Field(description="Conservé par le tri de pertinence du LLM")


class AskResponse(BaseModel):
    question: str
    answer: str
    status: Literal["answered", "not_found"]
    sources: list[Source]
    search_query: str | None = Field(None, description="Requête reformulée, le cas échéant")
    attempts: int
    prompt_version: str
    duration_ms: int
    retrieved: list[RetrievedDocument] | None = None
    grade_raw: str | None = None


# --- Synthèse de rapport -------------------------------------------------------------------
class SummarizeRequest(BaseModel):
    text: str = Field(
        min_length=50,
        max_length=50_000,
        description="Texte du rapport de chantier à synthétiser",
    )
    prompt_version: PromptVersion | None = None


class SummarizeResponse(BaseModel):
    summary: ReportSummary | None = Field(None, description="Synthèse structurée (prompts v3)")
    markdown: str | None = Field(None, description="Synthèse texte (prompts v1 / v2)")
    prompt_version: str
    report_characters: int
    duration_ms: int
