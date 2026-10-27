"""Évaluation du système RAG sur le dataset de référence.

Pour chaque question, trois mesures :

- **pertinence** (métrique principale) : la réponse est jugée pertinente ET correcte
  par le juge LLM au regard de la réponse de référence. Pour une question hors corpus,
  la réponse est réussie si l'assistant indique qu'il n'a pas trouvé l'information
  (aucun appel au juge : vérification déterministe).
- **retrieval_hit** : un document attendu fait partie des extraits retrouvés
  (évalue la recherche + reranking, indépendamment du LLM) ;
- **citation_hit** : un document attendu est cité dans la réponse.

Taux de pertinence = questions réussies / questions évaluées (hors erreurs d'API).
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Literal

from langchain_core.runnables import Runnable
from pydantic import BaseModel

from rag_btp.evaluation.judge import judge_answer
from rag_btp.graph import RAGAnswer

Category = Literal["factuel", "evolution", "hors_corpus"]


class EvalExample(BaseModel):
    id: str
    question: str
    reference: str
    sources: list[str] = []
    category: Category = "factuel"
    chantier: str | None = None


class EvalRecord(BaseModel):
    id: str
    question: str
    category: Category
    reference: str
    answer: str | None = None
    status: str | None = None
    success: bool = False
    pertinent: bool | None = None
    correct: bool | None = None
    judge_reason: str | None = None
    retrieval_hit: bool | None = None
    citation_hit: bool | None = None
    attempts: int | None = None
    latency_ms: int | None = None
    error: str | None = None


class EvalMetrics(BaseModel):
    total: int
    evaluated: int
    errors: int
    pertinence_rate: float | None
    correct_rate: float | None
    retrieval_hit_rate: float | None
    citation_hit_rate: float | None
    out_of_corpus_accuracy: float | None
    avg_latency_ms: float | None
    by_category: dict[str, float | None]


class EvalReport(BaseModel):
    created_at: str
    prompt_version: str
    config: dict[str, str]
    metrics: EvalMetrics
    records: list[EvalRecord]


def load_dataset(path: Path) -> list[EvalExample]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [EvalExample.model_validate(e) for e in data["examples"]]


# --- Évaluation d'une question ---------------------------------------------------------------
def score_example(example: EvalExample, result: RAGAnswer, judge_llm: Runnable) -> EvalRecord:
    """Calcule les mesures d'une question à partir de la réponse du graphe RAG."""
    expected = set(example.sources)
    retrieved = {d["source"] for d in result.retrieved}
    cited = {s["source"] for s in result.sources if s.get("cited")}
    record = EvalRecord(
        id=example.id,
        question=example.question,
        category=example.category,
        reference=example.reference,
        answer=result.answer,
        status=result.status,
        attempts=result.attempts,
        retrieval_hit=bool(expected & retrieved) if expected else None,
        citation_hit=bool(expected & cited) if expected else None,
    )

    if example.category == "hors_corpus":
        refused = result.status == "not_found"
        record.success = record.pertinent = record.correct = refused
        record.judge_reason = "Refus attendu" if refused else "A répondu au lieu de refuser"
    elif result.status == "not_found":
        record.success = record.pertinent = record.correct = False
        record.judge_reason = "Information présente dans le corpus mais non trouvée"
    else:
        verdict = judge_answer(judge_llm, example.question, example.reference, result.answer)
        record.pertinent, record.correct = verdict.pertinent, verdict.correct
        record.success = verdict.success
        record.judge_reason = verdict.raison
    return record


def run_evaluation(
    examples: list[EvalExample],
    answer_fn: Callable[[EvalExample], RAGAnswer],
    judge_llm: Runnable,
    delay: float = 0.0,
    on_record: Callable[[int, EvalRecord], None] | None = None,
) -> list[EvalRecord]:
    """Évalue chaque question ; une erreur d'API est enregistrée sans interrompre la série."""
    records = []
    for i, example in enumerate(examples, start=1):
        start = time.perf_counter()
        try:
            result = answer_fn(example)
            latency = int((time.perf_counter() - start) * 1000)
            record = score_example(example, result, judge_llm)
            record.latency_ms = latency
        except Exception as exc:
            record = EvalRecord(
                id=example.id,
                question=example.question,
                category=example.category,
                reference=example.reference,
                error=f"{type(exc).__name__}: {str(exc).splitlines()[0][:200] if str(exc) else ''}",
            )
        records.append(record)
        if on_record:
            on_record(i, record)
        if delay and i < len(examples):
            time.sleep(delay)  # limite de débit des offres gratuites (Groq, Gemini)
    return records


# --- Agrégation et rapport ------------------------------------------------------------------
def _rate(values: list[bool]) -> float | None:
    return round(sum(values) / len(values), 4) if values else None


def compute_metrics(records: list[EvalRecord]) -> EvalMetrics:
    ok = [r for r in records if r.error is None]
    in_corpus = [r for r in ok if r.category != "hors_corpus"]
    latencies = [r.latency_ms for r in ok if r.latency_ms is not None]
    categories = sorted({r.category for r in records})
    return EvalMetrics(
        total=len(records),
        evaluated=len(ok),
        errors=len(records) - len(ok),
        pertinence_rate=_rate([r.success for r in ok]),
        correct_rate=_rate([bool(r.correct) for r in in_corpus]),
        retrieval_hit_rate=_rate(
            [r.retrieval_hit for r in in_corpus if r.retrieval_hit is not None]
        ),
        citation_hit_rate=_rate([r.citation_hit for r in in_corpus if r.citation_hit is not None]),
        out_of_corpus_accuracy=_rate([r.success for r in ok if r.category == "hors_corpus"]),
        avg_latency_ms=round(sum(latencies) / len(latencies)) if latencies else None,
        by_category={c: _rate([r.success for r in ok if r.category == c]) for c in categories},
    )


def build_report(
    records: list[EvalRecord], prompt_version: str, config: dict[str, str]
) -> EvalReport:
    return EvalReport(
        created_at=datetime.now().isoformat(timespec="seconds"),
        prompt_version=prompt_version,
        config=config,
        metrics=compute_metrics(records),
        records=records,
    )


def pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.1f} %"


def report_markdown(report: EvalReport) -> str:
    m = report.metrics
    lines = [
        f"# Évaluation — prompts {report.prompt_version} ({report.created_at})",
        "",
        "| Paramètre | Valeur |",
        "|---|---|",
        *[f"| {k} | {v} |" for k, v in report.config.items()],
        "",
        "| Métrique | Résultat |",
        "|---|---|",
        f"| **Taux de pertinence** | **{pct(m.pertinence_rate)}** |",
        f"| Réponses correctes (questions du corpus) | {pct(m.correct_rate)} |",
        f"| Document attendu retrouvé (retrieval hit) | {pct(m.retrieval_hit_rate)} |",
        f"| Document attendu cité | {pct(m.citation_hit_rate)} |",
        f"| Refus correct hors corpus | {pct(m.out_of_corpus_accuracy)} |",
        f"| Latence moyenne | {m.avg_latency_ms} ms |",
        f"| Questions évaluées | {m.evaluated} / {m.total} ({m.errors} erreur(s) d'API) |",
        "",
        "## Questions échouées",
        "",
    ]
    failures = [r for r in report.records if not r.success]
    if not failures:
        lines.append("Aucune.")
    for r in failures:
        reason = r.error or r.judge_reason
        lines.append(f"- **{r.id}** — {r.question}  \n  → {reason}")
    return "\n".join(lines) + "\n"


def write_report(report: EvalReport, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = report.created_at.replace(":", "").replace("-", "")
    base = out_dir / f"{stamp}_{report.prompt_version}"
    json_path, md_path = base.with_suffix(".json"), base.with_suffix(".md")
    json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    md_path.write_text(report_markdown(report), encoding="utf-8")
    return json_path, md_path
