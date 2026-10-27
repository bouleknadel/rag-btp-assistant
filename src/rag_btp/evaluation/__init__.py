"""Évaluation et monitoring avec LangSmith."""

from rag_btp.evaluation.judge import JudgeVerdict, judge_answer, parse_verdict
from rag_btp.evaluation.runner import (
    EvalExample,
    EvalRecord,
    EvalReport,
    build_report,
    compute_metrics,
    load_dataset,
    report_markdown,
    run_evaluation,
    score_example,
    write_report,
)
from rag_btp.evaluation.tracing import langsmith_project, tracing_enabled

__all__ = [
    "EvalExample",
    "EvalRecord",
    "EvalReport",
    "JudgeVerdict",
    "build_report",
    "compute_metrics",
    "judge_answer",
    "langsmith_project",
    "load_dataset",
    "parse_verdict",
    "report_markdown",
    "run_evaluation",
    "score_example",
    "tracing_enabled",
    "write_report",
]
