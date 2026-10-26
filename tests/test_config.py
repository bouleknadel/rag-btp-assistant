from pathlib import Path

from rag_btp.config import PROJECT_ROOT, Settings


def test_fallbacks_parsed_from_csv(monkeypatch):
    monkeypatch.setenv("LLM_FALLBACKS", "openai, gemini")
    settings = Settings(_env_file=None)
    assert settings.llm_fallbacks == ["openai", "gemini"]


def test_relative_paths_resolved_from_project_root(monkeypatch):
    monkeypatch.setenv("CHROMA_PERSIST_DIR", "data/chroma_test")
    settings = Settings(_env_file=None)
    assert settings.chroma_persist_dir == PROJECT_ROOT / "data" / "chroma_test"


def test_api_keys_are_masked(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_secret")
    settings = Settings(_env_file=None)
    assert "gsk_secret" not in repr(settings)
    assert settings.groq_api_key.get_secret_value() == "gsk_secret"


def test_absolute_path_kept(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("RAW_DATA_DIR", str(tmp_path))
    assert Settings(_env_file=None).raw_data_dir == tmp_path
