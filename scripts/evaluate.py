"""Évalue l'assistant RAG sur le dataset de référence et calcule le taux de pertinence.

Usage :
    python scripts/evaluate.py                          # prompts de la config (.env)
    python scripts/evaluate.py --prompt-versions v1 v3  # compare plusieurs versions
    python scripts/evaluate.py --limit 5                # test rapide sur 5 questions
    python scripts/evaluate.py --langsmith              # + dataset et expérience LangSmith
    python scripts/evaluate.py --judge-provider gemini  # juge différent du générateur

Les résultats sont écrits dans evaluation/results/ (JSON détaillé + résumé Markdown).
L'index doit avoir été construit au préalable (``python scripts/ingest.py``).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from rag_btp.config import PROJECT_ROOT, get_settings
from rag_btp.evaluation import (
    EvalExample,
    EvalRecord,
    build_report,
    langsmith_project,
    load_dataset,
    score_example,
    tracing_enabled,
    write_report,
)
from rag_btp.evaluation.runner import pct, run_evaluation
from rag_btp.graph import RAGAnswer, answer_question
from rag_btp.llm import build_chat_model, get_llm, model_name, provider_chain

DATASET = PROJECT_ROOT / "evaluation" / "dataset.json"
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"


def print_record(i: int, total: int, record: EvalRecord) -> None:
    mark = "ERREUR" if record.error else ("OK    " if record.success else "ÉCHEC ")
    detail = record.error or record.judge_reason or ""
    print(f"[{i:>2}/{total}] {mark} {record.id} {record.question[:60]:<60} | {detail[:70]}")


# --- Mode LangSmith -------------------------------------------------------------------------
def sync_langsmith_dataset(client, name: str, examples: list[EvalExample]) -> None:
    """Crée le dataset LangSmith s'il n'existe pas encore."""
    if client.has_dataset(dataset_name=name):
        print(f"Dataset LangSmith « {name} » déjà présent.")
        return
    dataset = client.create_dataset(name, description="Q/R de référence — corpus BTP synthétique")
    client.create_examples(
        dataset_id=dataset.id,
        examples=[
            {
                "inputs": {"question": e.question, "chantier": e.chantier},
                "outputs": {"reference": e.reference, "sources": e.sources},
                "metadata": {"id": e.id, "category": e.category},
            }
            for e in examples
        ],
    )
    print(f"Dataset LangSmith « {name} » créé ({len(examples)} exemples).")


def run_langsmith(version: str, examples, judge_llm, dataset_name: str, delay: float):
    """Lance une expérience LangSmith ; retourne aussi les enregistrements pour le rapport local."""
    import time

    from langsmith import Client

    client = Client()
    sync_langsmith_dataset(client, dataset_name, examples)
    by_question = {e.question: e for e in examples}
    records: list[EvalRecord] = []

    def target(inputs: dict) -> dict:
        start = time.perf_counter()
        result = answer_question(
            inputs["question"], chantier=inputs.get("chantier"), prompt_version=version
        )
        time.sleep(delay)
        return {**result.model_dump(), "latency_ms": int((time.perf_counter() - start) * 1000)}

    def evaluator(inputs: dict, outputs: dict | None) -> list[dict]:
        example = by_question[inputs["question"]]
        if not outputs or "answer" not in outputs:  # la cible a échoué (erreur d'API)
            record = EvalRecord(
                id=example.id,
                question=example.question,
                category=example.category,
                reference=example.reference,
                error="Erreur lors de la génération (voir la trace LangSmith)",
            )
        else:
            outputs = dict(outputs)
            latency = outputs.pop("latency_ms", None)
            try:
                record = score_example(example, RAGAnswer.model_validate(outputs), judge_llm)
                record.latency_ms = latency
            except Exception as exc:  # juge indisponible ou verdict illisible
                record = EvalRecord(
                    id=example.id,
                    question=example.question,
                    category=example.category,
                    reference=example.reference,
                    answer=outputs.get("answer"),
                    error=f"Juge : {type(exc).__name__}",
                )
        records.append(record)
        print_record(len(records), len(examples), record)
        results = [
            {"key": "pertinence", "score": int(record.success), "comment": record.judge_reason}
        ]
        for key in ("retrieval_hit", "citation_hit"):
            if getattr(record, key) is not None:
                results.append({"key": key, "score": int(getattr(record, key))})
        return results

    client.evaluate(
        target,
        data=dataset_name,
        evaluators=[evaluator],
        experiment_prefix=f"rag-btp-prompts-{version}",
        metadata={"prompt_version": version},
        max_concurrency=1,
    )
    return records


# --- Programme principal ---------------------------------------------------------------------
def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Évaluation de l'assistant RAG BTP")
    parser.add_argument("--prompt-versions", nargs="+", default=[settings.prompt_version])
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--limit", type=int, help="nombre maximal de questions")
    parser.add_argument("--delay", type=float, default=2.0, help="pause entre questions (s)")
    parser.add_argument("--judge-provider", choices=["groq", "openai", "gemini"])
    parser.add_argument("--langsmith", action="store_true", help="expérience LangSmith")
    parser.add_argument("--langsmith-dataset", default="rag-btp-eval")
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

    examples = load_dataset(args.dataset)[: args.limit]
    providers = provider_chain(settings)
    if not providers:
        sys.exit("Aucune clé API LLM configurée dans .env.")
    judge_provider = args.judge_provider or providers[0]
    judge_llm = build_chat_model(judge_provider, settings) if args.judge_provider else get_llm()
    config = {
        "LLM (génération)": f"{providers[0]}/{model_name(providers[0], settings)}",
        "Fallbacks": ", ".join(providers[1:]) or "aucun",
        "Juge": f"{judge_provider}/{model_name(judge_provider, settings)}",
        "Embeddings": settings.embedding_model,
        "Reranker": settings.reranker_model,
        "Top-k / top-n": f"{settings.retrieval_top_k} / {settings.rerank_top_n}",
        "Dataset": f"{args.dataset.name} ({len(examples)} questions)",
    }
    if args.langsmith and not tracing_enabled():
        sys.exit("Mode --langsmith : définissez LANGSMITH_TRACING=true et LANGSMITH_API_KEY.")

    print(f"Évaluation de {len(examples)} questions — prompts {', '.join(args.prompt_versions)}")
    if tracing_enabled():
        print(f"Traces LangSmith : projet « {langsmith_project()} »")

    summaries = []
    for version in args.prompt_versions:
        print(f"\n=== Prompts {version} ===")
        if args.langsmith:
            records = run_langsmith(
                version, examples, judge_llm, args.langsmith_dataset, args.delay
            )
        else:
            records = run_evaluation(
                examples,
                answer_fn=lambda e, v=version: answer_question(
                    e.question, chantier=e.chantier, prompt_version=v
                ),
                judge_llm=judge_llm,
                delay=args.delay,
                on_record=lambda i, r: print_record(i, len(examples), r),
            )
        report = build_report(records, version, config)
        json_path, md_path = write_report(report, RESULTS_DIR)
        summaries.append(report)
        m = report.metrics
        print(f"\nTaux de pertinence ({version}) : {pct(m.pertinence_rate)}")
        print(
            f"Document retrouvé : {pct(m.retrieval_hit_rate)} | cité : {pct(m.citation_hit_rate)}"
        )
        print(f"Refus hors corpus : {pct(m.out_of_corpus_accuracy)} | erreurs : {m.errors}")
        print(f"Rapport : {md_path.relative_to(PROJECT_ROOT)}")
        if m.errors:
            print("⚠ Des questions ont échoué pour cause d'erreur d'API : score partiel.")

    if len(summaries) > 1:
        print("\n=== Comparaison des versions ===")
        print(f"{'Version':<8} {'Pertinence':>11} {'Retrouvé':>10} {'Cité':>8} {'Erreurs':>8}")
        for r in summaries:
            m = r.metrics
            print(
                f"{r.prompt_version:<8} {pct(m.pertinence_rate):>11} "
                f"{pct(m.retrieval_hit_rate):>10} {pct(m.citation_hit_rate):>8} {m.errors:>8}"
            )


if __name__ == "__main__":
    try:
        main()
    finally:
        # Les traces LangSmith partent en arrière-plan : on attend la fin de leur envoi
        # avant de quitter, sinon les dernières seraient perdues.
        from langchain_core.tracers.langchain import wait_for_all_tracers

        wait_for_all_tracers()
