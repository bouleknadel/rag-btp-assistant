"""Tests complémentaires : services de l'API, reranker, synthèse, CLI d'ingestion."""

import sys
import types
from pathlib import Path

import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models import FakeListChatModel

from rag_btp.config import Settings
from rag_btp.prompts import get_prompts
from rag_btp.summary import MAX_REPORT_CHARS, summarize_report


# --- Services de l'API ---------------------------------------------------------------------------
@pytest.mark.parametrize("with_key", [True, False])
def test_services_from_settings(monkeypatch, tmp_path: Path, with_key: bool):
    import rag_btp.indexing as indexing
    import rag_btp.llm as llm
    import rag_btp.retrieval as retrieval
    from rag_btp.api.services import Services

    store = indexing.get_vector_store(DeterministicFakeEmbedding(size=8), tmp_path, "svc-test")
    monkeypatch.setattr(indexing, "get_vector_store", lambda: store)
    monkeypatch.setattr(retrieval, "get_reranker", lambda: None)
    if not with_key:
        monkeypatch.setattr(
            llm, "get_llm", lambda s: (_ for _ in ()).throw(llm.NoLLMConfiguredError())
        )
    else:
        monkeypatch.setattr(llm, "get_llm", lambda s: FakeListChatModel(responses=["x"]))

    keys = {"groq_api_key": "gsk_test"} if with_key else {"groq_api_key": None}
    settings = Settings(_env_file=None, google_api_key=None, openai_api_key=None, **keys)
    services = Services.from_settings(settings)

    assert services.store is store
    assert (services.llm is not None) is with_key
    assert services.llm_providers == (["groq"] if with_key else [])
    assert services.graph("v3") is services.graph("v3")  # graphe compilé une seule fois


# --- Reranker cross-encoder (modèle simulé) -------------------------------------------------------
def test_cross_encoder_scores_are_probabilities(monkeypatch):
    class FakeCrossEncoder:
        def __init__(self, name, device, max_length):
            self.name = name

        def predict(self, pairs, show_progress_bar=False):
            return [3.0, -2.0, 0.0][: len(pairs)]

    monkeypatch.setitem(
        sys.modules, "sentence_transformers", types.SimpleNamespace(CrossEncoder=FakeCrossEncoder)
    )
    from rag_btp.retrieval.reranker import CrossEncoderReranker

    reranker = CrossEncoderReranker("fake-model")
    docs = [Document(page_content=t) for t in ("a", "b", "c")]
    scores = reranker.score("question", docs)

    assert all(0.0 < s < 1.0 for s in scores)
    assert scores[0] > scores[2] > scores[1]  # ordre des logits conservé
    assert scores[2] == pytest.approx(0.5)
    assert reranker.score("question", []) == []


# --- Synthèse : validation de l'entrée ------------------------------------------------------------
@pytest.mark.parametrize("report", ["   ", "x" * (MAX_REPORT_CHARS + 1)])
def test_summarize_rejects_empty_or_too_long_report(report):
    with pytest.raises(ValueError):
        summarize_report(report, FakeListChatModel(responses=["{}"]), get_prompts("v3"))


# --- CLI d'aperçu de l'ingestion ------------------------------------------------------------------
def test_ingestion_cli(monkeypatch, tmp_path: Path, capsys):
    from rag_btp.ingestion.__main__ import main

    (tmp_path / "tilleuls__planning__test.md").write_text("# Planning\n\nFin du GO : avril.")
    monkeypatch.setattr(sys, "argv", ["rag_btp.ingestion", str(tmp_path)])
    main()
    output = capsys.readouterr().out
    assert "Documents        : 1" in output
    assert "planning" in output


def test_ingestion_cli_empty_folder(monkeypatch, tmp_path: Path, capsys):
    from rag_btp.ingestion.__main__ import main

    monkeypatch.setattr(sys, "argv", ["rag_btp.ingestion", str(tmp_path)])
    main()
    assert "Aucun document" in capsys.readouterr().out
