"""Synthèse automatique de rapports de chantier.

Le prompt v3 demande une sortie JSON, validée ici par un schéma Pydantic
(``ReportSummary``) : la synthèse est donc directement exploitable par l'API,
un tableau de bord ou une notification n8n. Les prompts v1/v2 produisent du
texte libre / Markdown, renvoyé tel quel dans le champ ``markdown``.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field, ValidationError, field_validator

from rag_btp.prompts import PromptSet

MAX_REPORT_CHARS = 50_000


class ActionItem(BaseModel):
    action: str
    responsable: str | None = None
    echeance: str | None = None

    @field_validator("responsable", "echeance", mode="before")
    @classmethod
    def _null_strings(cls, value: Any) -> Any:
        if isinstance(value, str) and value.strip().lower() in {"", "null", "none", "n/a"}:
            return None
        return value


class ReportSummary(BaseModel):
    """Synthèse structurée d'un rapport de chantier."""

    resume: str = Field("", description="Résumé en 2 phrases maximum")
    avancement: str | None = Field(None, description="État d'avancement")
    points_cles: list[str] = []
    problemes: list[str] = Field([], description="Retards, non-conformités, aléas")
    securite: list[str] = Field([], description="Incidents, observations, mesures")
    actions: list[ActionItem] = []
    chiffres_cles: list[str] = []

    @field_validator("avancement", mode="before")
    @classmethod
    def _join_list(cls, value: Any) -> Any:
        if isinstance(value, list):
            return "; ".join(str(v) for v in value)
        return value

    @field_validator(
        "points_cles", "problemes", "securite", "chiffres_cles", "actions", mode="before"
    )
    @classmethod
    def _as_list(cls, value: Any) -> Any:
        if value is None:
            return []
        if isinstance(value, str | dict):
            return [value]
        return value


class SummaryResult(BaseModel):
    """Résultat d'une synthèse : structurée (v3) ou texte libre (v1/v2)."""

    summary: ReportSummary | None = None
    markdown: str | None = None
    prompt_version: str
    report_characters: int


def parse_summary(text: str) -> ReportSummary | None:
    """Extrait et valide le JSON de la réponse du LLM (``None`` si absent ou invalide)."""
    cleaned = re.sub(r"```(?:json)?", "", text)
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        return None
    try:
        return ReportSummary.model_validate(json.loads(match.group(0)))
    except (json.JSONDecodeError, ValidationError):
        return None


def summarize_report(report: str, llm: Runnable, prompts: PromptSet) -> SummaryResult:
    """Synthétise un rapport de chantier avec le prompt ``summary`` de la version donnée."""
    report = report.strip()
    if not report:
        raise ValueError("Le rapport est vide.")
    if len(report) > MAX_REPORT_CHARS:
        raise ValueError(f"Rapport trop long ({len(report)} caractères, max {MAX_REPORT_CHARS}).")

    chain = prompts.summary | llm | StrOutputParser()
    raw = chain.invoke(
        {"report": report},
        config={
            "run_name": "rag_btp_summary",
            "tags": ["summary", f"prompts-{prompts.version}"],
            "metadata": {"prompt_version": prompts.version},
        },
    ).strip()

    summary = parse_summary(raw)
    return SummaryResult(
        summary=summary,
        markdown=None if summary else raw,
        prompt_version=prompts.version,
        report_characters=len(report),
    )
