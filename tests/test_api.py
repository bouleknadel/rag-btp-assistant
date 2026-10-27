"""Tests d'intégration de l'API avec des modèles factices (aucun appel externe)."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models import FakeListChatModel

from rag_btp.api.main import create_app
from rag_btp.api.services import Services
from rag_btp.config import PROJECT_ROOT, Settings
from rag_btp.indexing import get_vector_store, index_chunks
from rag_btp.ingestion import ingest_directory
from rag_btp.retrieval import BTPRetriever
from rag_btp.summary import parse_summary
from test_retrieval import KeywordReranker

RAW_DIR = PROJECT_ROOT / "data" / "raw"

SUMMARY_JSON = {
    "resume": "Dalle R+2 coulée ; retard de 6 jours.",
    "avancement": "48 %",
    "points_cles": ["Coulage de 86 m³"],
    "problemes": ["Retard de 6 jours ouvrés"],
    "securite": ["Presqu'accident le 5 mars 2026"],
    "actions": [{"action": "Renfort coffrage", "responsable": "BTP Rhodanien", "echeance": "null"}],
    "chiffres_cles": ["86 m³", "16 personnes"],
}

REPORT = (
    "Rapport hebdomadaire semaine 10. Avancement 48 %. Retard de 6 jours ouvrés. "
    "Presqu'accident le 5 mars 2026 : chute d'un serre-joint depuis le R+3."
)


def make_client(tmp_path: Path, responses: list[str], with_llm: bool = True) -> TestClient:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(exist_ok=True)
    settings = Settings(_env_file=None, raw_data_dir=raw_dir, prompt_version="v3")
    store = get_vector_store(
        embeddings=DeterministicFakeEmbedding(size=64),
        persist_dir=tmp_path / "chroma",
        collection_name="test-api",
    )
    chunks = [c for c in ingest_directory(RAW_DIR) if not c.metadata["source"].startswith("gen")]
    index_chunks(chunks, store)
    services = Services(
        store=store,
        retriever=BTPRetriever(vector_store=store, reranker=KeywordReranker(), top_k=60, top_n=3),
        llm=FakeListChatModel(responses=responses) if with_llm else None,
        settings=settings,
        llm_providers=["fake"] if with_llm else [],
    )
    return TestClient(create_app(services))


# --- /health -----------------------------------------------------------------------------
def test_health(tmp_path):
    with make_client(tmp_path, []) as client:
        data = client.get("/health").json()
    assert data["status"] == "ok"
    assert data["documents_indexed"] > 0
    assert data["prompt_version"] == "v3"


def test_health_degraded_without_llm(tmp_path):
    with make_client(tmp_path, [], with_llm=False) as client:
        assert client.get("/health").json()["status"] == "degraded"
        response = client.post("/ask", json={"question": "Vent maximal ?"})
    assert response.status_code == 503


# --- /ask ----------------------------------------------------------------------------------
def test_ask_returns_sourced_answer(tmp_path):
    grade = '{"evaluations": [{"extrait": 1, "raison": "72 km/h", "pertinent": true}]}'
    with make_client(tmp_path, [grade, "Arrêt au-delà de 72 km/h [1]."]) as client:
        response = client.post("/ask", json={"question": "vent 72 km/h grue"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "answered"
    assert data["answer"] == "Arrêt au-delà de 72 km/h [1]."
    assert data["sources"][0]["cited"] is True
    assert data["retrieved"] is None  # détail uniquement en mode debug
    assert data["duration_ms"] >= 0


def test_ask_debug_mode(tmp_path):
    grade = '{"evaluations": [{"extrait": 1, "raison": "ok", "pertinent": true}]}'
    with make_client(tmp_path, [grade, "Réponse [1]."]) as client:
        data = client.post("/ask", json={"question": "vent grue", "debug": True}).json()
    assert len(data["retrieved"]) == 3
    assert data["retrieved"][0]["kept"] is True
    assert data["grade_raw"] == grade


def test_ask_validation_error(tmp_path):
    with make_client(tmp_path, []) as client:
        assert client.post("/ask", json={"question": ""}).status_code == 422
        assert (
            client.post("/ask", json={"question": "ok ?", "prompt_version": "v9"}).status_code
            == 422
        )


def test_ask_llm_failure_returns_502(tmp_path):
    class FailingModel(FakeListChatModel):
        def _call(self, *args, **kwargs):
            raise RuntimeError("503 UNAVAILABLE")

    client = make_client(tmp_path, [])
    client.app.state.services.llm = FailingModel(responses=["x"])
    with client:
        response = client.post("/ask", json={"question": "Vent maximal ?"})
    assert response.status_code == 502
    assert "503 UNAVAILABLE" in response.json()["detail"]


# --- /ingest ---------------------------------------------------------------------------------
def test_ingest_upload_indexes_file(tmp_path):
    content = "# Rapport journalier\n\nCoulage du dallage du sous-sol : 42 m³ de béton.".encode()
    with make_client(tmp_path, []) as client:
        before = client.get("/health").json()["documents_indexed"]
        files = {"files": ("tilleuls__rapport_journalier__test.md", content, "text/markdown")}
        response = client.post("/ingest", files=files)
        after = client.get("/health").json()["documents_indexed"]
    assert response.status_code == 200
    assert response.json()["files"] == ["tilleuls__rapport_journalier__test.md"]
    assert after == before + response.json()["chunks_upserted"]
    assert (tmp_path / "raw" / "uploads" / "tilleuls__rapport_journalier__test.md").exists()


def test_ingest_same_file_twice_does_not_duplicate(tmp_path):
    files = {"files": ("doc.md", b"# Doc\n\nContenu de test pour le chantier.", "text/markdown")}
    with make_client(tmp_path, []) as client:
        first = client.post("/ingest", files=files).json()
        second = client.post("/ingest", files=files).json()
    assert second["total_in_collection"] == first["total_in_collection"]


def test_ingest_rejects_unsupported_extension_and_path_traversal(tmp_path):
    with make_client(tmp_path, []) as client:
        bad_ext = client.post("/ingest", files={"files": ("plan.dwg", b"x", "application/acad")})
        traversal = client.post(
            "/ingest", files={"files": ("../../evil.md", b"# x\n\ntexte", "text/markdown")}
        )
    assert bad_ext.status_code == 415
    assert traversal.status_code == 200
    assert traversal.json()["files"] == ["evil.md"]
    assert not (tmp_path / "evil.md").exists()


def test_reindex(tmp_path):
    client = make_client(tmp_path, [])
    (tmp_path / "raw" / "tilleuls__planning__test.md").write_text("# Planning\n\nFin : mai.")
    with client:
        data = client.post("/ingest/reindex", params={"reset": True}).json()
    assert data["documents"] == 1
    assert data["total_in_collection"] == data["chunks_upserted"]


# --- /summarize --------------------------------------------------------------------------------
def test_summarize_returns_structured_summary(tmp_path):
    llm_output = f"```json\n{json.dumps(SUMMARY_JSON, ensure_ascii=False)}\n```"
    with make_client(tmp_path, [llm_output]) as client:
        response = client.post("/summarize", json={"text": REPORT})
    assert response.status_code == 200
    summary = response.json()["summary"]
    assert summary["avancement"] == "48 %"
    assert summary["actions"][0]["echeance"] is None  # "null" texte → null JSON
    assert response.json()["markdown"] is None


def test_summarize_v2_returns_markdown(tmp_path):
    with make_client(tmp_path, ["## Résumé\nDalle coulée."]) as client:
        data = client.post("/summarize", json={"text": REPORT, "prompt_version": "v2"}).json()
    assert data["summary"] is None
    assert data["markdown"].startswith("## Résumé")


def test_summarize_file(tmp_path):
    llm_output = json.dumps(SUMMARY_JSON)
    with make_client(tmp_path, [llm_output]) as client:
        files = {"file": ("rapport.txt", REPORT.encode(), "text/plain")}
        response = client.post("/summarize/file", files=files)
    assert response.status_code == 200
    assert response.json()["report_characters"] == len(REPORT)


def test_summarize_too_short_is_rejected(tmp_path):
    with make_client(tmp_path, []) as client:
        assert client.post("/summarize", json={"text": "trop court"}).status_code == 422


# --- Parsing de la synthèse ----------------------------------------------------------------------
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('{"resume": "ok", "problemes": "un seul problème"}', ["un seul problème"]),
        ('{"resume": "ok", "problemes": null}', []),
    ],
)
def test_parse_summary_normalizes_lists(text, expected):
    assert parse_summary(text).problemes == expected


def test_parse_summary_invalid_returns_none():
    assert parse_summary("pas de JSON") is None
    assert parse_summary('{"actions": [{"responsable": "x"}]}') is None  # action manquante
