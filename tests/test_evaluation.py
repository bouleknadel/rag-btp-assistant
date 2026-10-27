from pathlib import Path

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models import FakeListChatModel

from rag_btp.config import PROJECT_ROOT
from rag_btp.evaluation import (
    EvalExample,
    build_report,
    load_dataset,
    parse_verdict,
    report_markdown,
    run_evaluation,
    score_example,
    tracing_enabled,
    write_report,
)
from rag_btp.graph import RAGAnswer
from rag_btp.indexing import IndexModelMismatchError, get_vector_store

DATASET = PROJECT_ROOT / "evaluation" / "dataset.json"
RAW_DIR = PROJECT_ROOT / "data" / "raw"

FACT = EvalExample(
    id="t1",
    question="Vent maximal pour la grue ?",
    reference="72 km/h",
    sources=["ppsps.pdf"],
    category="factuel",
)
OUT = EvalExample(
    id="t2", question="Couleur des volets ?", reference="absent", category="hors_corpus"
)


def rag_answer(status="answered", answer="Arrêt à 72 km/h [1].", cited=True) -> RAGAnswer:
    return RAGAnswer(
        question="q",
        answer=answer,
        status=status,
        sources=[{"source": "ppsps.pdf", "cited": cited}] if status == "answered" else [],
        prompt_version="v3",
        retrieved=[{"index": 1, "source": "ppsps.pdf", "kept": True}],
    )


def judge(*verdicts: str) -> FakeListChatModel:
    return FakeListChatModel(responses=list(verdicts))


OK_VERDICT = '{"pertinent": true, "correct": true, "raison": "72 km/h présent"}'
KO_VERDICT = '{"pertinent": true, "correct": false, "raison": "valeur fausse"}'


# --- Dataset ------------------------------------------------------------------------------------
def test_dataset_is_valid_and_sources_exist():
    examples = load_dataset(DATASET)
    assert len(examples) >= 25
    assert len({e.id for e in examples}) == len(examples)
    corpus = {p.name for p in RAW_DIR.iterdir()}
    for e in examples:
        if e.category == "hors_corpus":
            assert e.sources == []
        else:
            assert e.sources, e.id
            assert set(e.sources) <= corpus, f"{e.id} : source absente du corpus"
    assert {e.category for e in examples} == {"factuel", "evolution", "hors_corpus"}


# --- Notation d'une question --------------------------------------------------------------------
def test_score_correct_answer():
    record = score_example(FACT, rag_answer(), judge(OK_VERDICT))
    assert record.success and record.retrieval_hit and record.citation_hit


def test_score_wrong_answer():
    record = score_example(FACT, rag_answer(answer="50 km/h [1]."), judge(KO_VERDICT))
    assert not record.success
    assert record.judge_reason == "valeur fausse"


def test_not_found_on_in_corpus_question_fails_without_judge_call():
    record = score_example(FACT, rag_answer(status="not_found"), judge())  # aucun verdict dispo
    assert not record.success
    assert record.retrieval_hit is True  # le document était là : utile au diagnostic


def test_out_of_corpus_refusal_is_success():
    assert score_example(OUT, rag_answer(status="not_found"), judge()).success
    assert not score_example(OUT, rag_answer(), judge()).success
    assert score_example(OUT, rag_answer(status="not_found"), judge()).retrieval_hit is None


def test_parse_verdict():
    assert parse_verdict(f"Voici : {OK_VERDICT}").success
    assert parse_verdict("illisible") is None


# --- Série complète et métriques ----------------------------------------------------------------
def test_run_evaluation_metrics_and_error_handling():
    answers = iter([rag_answer(), rag_answer(status="not_found"), RuntimeError("429 quota")])

    def answer_fn(_example):
        value = next(answers)
        if isinstance(value, Exception):
            raise value
        return value

    examples = [FACT, OUT, FACT.model_copy(update={"id": "t3"})]
    records = run_evaluation(examples, answer_fn, judge(OK_VERDICT))
    report = build_report(records, "v3", {"LLM": "fake"})
    m = report.metrics

    assert m.total == 3 and m.evaluated == 2 and m.errors == 1
    assert m.pertinence_rate == 1.0  # erreurs d'API exclues du taux
    assert m.out_of_corpus_accuracy == 1.0
    assert records[2].error.startswith("RuntimeError: 429 quota")


def test_report_files(tmp_path: Path):
    records = run_evaluation([FACT], lambda e: rag_answer(), judge(KO_VERDICT))
    report = build_report(records, "v1", {"LLM": "fake"})
    json_path, md_path = write_report(report, tmp_path)
    assert json_path.exists() and md_path.exists()
    markdown = report_markdown(report)
    assert "**Taux de pertinence** | **0.0 %**" in markdown
    assert "valeur fausse" in markdown


# --- Tracing --------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("flag", "key", "expected"),
    [("true", "lsv2_x", True), ("false", "lsv2_x", False), ("true", "", False)],
)
def test_tracing_enabled(monkeypatch, flag, key, expected):
    monkeypatch.setenv("LANGSMITH_TRACING", flag)
    monkeypatch.setenv("LANGSMITH_API_KEY", key)
    assert tracing_enabled() is expected


# --- Garde-fou : modèle d'embeddings de l'index ---------------------------------------
def test_index_built_with_another_model_is_rejected(tmp_path: Path):
    class OtherModel(DeterministicFakeEmbedding):
        pass

    get_vector_store(DeterministicFakeEmbedding(size=8), tmp_path, "guard-test")
    get_vector_store(DeterministicFakeEmbedding(size=8), tmp_path, "guard-test")  # même modèle
    with pytest.raises(IndexModelMismatchError, match="ingest.py --reset"):
        get_vector_store(OtherModel(size=8), tmp_path, "guard-test")
