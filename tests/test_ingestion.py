import sys
from pathlib import Path

import pytest

from rag_btp.config import PROJECT_ROOT
from rag_btp.ingestion import (
    load_directory,
    load_file,
    make_chunk_id,
    parse_filename_metadata,
    split_documents,
)

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from generate_demo_corpus import generate_daily_reports, render_pdf  # noqa: E402

RAW_DIR = PROJECT_ROOT / "data" / "raw"

SAMPLE_MD = """# Compte-rendu de réunion n° 1

## Avancement

La dalle du R+1 a été coulée le 3 mars.

## Sécurité

- Garde-corps à reposer au R+2.
"""


# --- Métadonnées issues du nom de fichier ------------------------------------
def test_parse_filename_metadata_known_convention():
    meta = parse_filename_metadata(Path("tilleuls__compte_rendu__reunion-14.pdf"))
    assert meta["chantier"] == "tilleuls"
    assert meta["chantier_label"] == "Résidence Les Tilleuls"
    assert meta["doc_type"] == "compte_rendu"


def test_parse_filename_metadata_fallback():
    meta = parse_filename_metadata(Path("document-quelconque.pdf"))
    assert meta["chantier"] == "inconnu"
    assert meta["doc_type"] == "autre"


# --- Chargement ----------------------------------------------------------------
def test_load_markdown_file(tmp_path: Path):
    path = tmp_path / "tilleuls__compte_rendu__reunion-1.md"
    path.write_text(SAMPLE_MD, encoding="utf-8")
    docs = load_file(path, base_dir=tmp_path)
    assert len(docs) == 1
    assert docs[0].metadata["title"] == "Compte-rendu de réunion n° 1"
    assert docs[0].metadata["source"] == path.name
    assert "dalle du R+1" in docs[0].page_content


def test_load_pdf_file(tmp_path: Path):
    path = tmp_path / "tilleuls__essais__test.pdf"
    render_pdf("# Essais béton\n\n- Résistance à 28 jours : 34,5 MPa.", path)
    docs = load_file(path)
    assert docs[0].metadata["page"] == 1
    assert "34,5 MPa" in docs[0].page_content


def test_unsupported_extension_raises(tmp_path: Path):
    path = tmp_path / "plan.dwg"
    path.write_bytes(b"\x00")
    with pytest.raises(ValueError):
        load_file(path)


def test_load_directory_skips_unreadable_files(tmp_path: Path):
    (tmp_path / "ok.md").write_text(SAMPLE_MD, encoding="utf-8")
    (tmp_path / "corrompu.pdf").write_bytes(b"pas un pdf")
    docs = load_directory(tmp_path)
    assert [d.metadata["file_name"] for d in docs] == ["ok.md"]


# --- Chunking ------------------------------------------------------------------
def _sample_docs(tmp_path: Path):
    path = tmp_path / "tilleuls__compte_rendu__reunion-1.md"
    path.write_text(SAMPLE_MD * 10, encoding="utf-8")
    return load_file(path)


def test_chunks_respect_size_and_keep_metadata(tmp_path: Path):
    chunks = split_documents(_sample_docs(tmp_path), chunk_size=300, chunk_overlap=50)
    assert len(chunks) > 1
    header = "[Compte-rendu de réunion n° 1 — Résidence Les Tilleuls]"
    for chunk in chunks:
        assert chunk.metadata["chantier"] == "tilleuls"
        assert chunk.page_content.startswith(header)
        body = chunk.page_content.split("\n", 1)[1]
        assert len(body) <= 300


def test_chunk_ids_are_deterministic_and_unique(tmp_path: Path):
    docs = _sample_docs(tmp_path)
    first = [c.id for c in split_documents(docs, chunk_size=300, chunk_overlap=50)]
    second = [c.id for c in split_documents(docs, chunk_size=300, chunk_overlap=50)]
    assert first == second
    assert len(set(first)) == len(first)


def test_chunk_id_changes_with_content():
    assert make_chunk_id("a.md", 1, 0, "texte") != make_chunk_id("a.md", 1, 0, "texte modifié")


def test_invalid_overlap_raises(tmp_path: Path):
    with pytest.raises(ValueError):
        split_documents(_sample_docs(tmp_path), chunk_size=100, chunk_overlap=100)


# --- Corpus de démonstration -------------------------------------------------------
def test_demo_corpus_is_complete():
    files = sorted(p.name for p in RAW_DIR.iterdir() if p.is_file())
    assert len(files) >= 15
    assert any(f.endswith(".pdf") for f in files)
    assert any(f.endswith(".md") for f in files)
    docs = load_directory(RAW_DIR)
    assert {d.metadata["chantier"] for d in docs} == {"tilleuls", "jean-moulin"}


def test_generate_daily_reports(tmp_path: Path):
    assert generate_daily_reports(25, tmp_path) == 25
    docs = load_directory(tmp_path)
    assert len(docs) == 25
    assert all(d.metadata["doc_type"] == "rapport_journalier" for d in docs)


def test_pdf_title_comes_from_metadata_even_if_wrapped(tmp_path: Path):
    long_title = "Procès-verbal de réception avec réserves — Lot n° 08 Plâtrerie et cloisons"
    path = tmp_path / "jean-moulin__pv_reception__test.pdf"
    render_pdf(f"# {long_title}\n\nDélai de levée des réserves : 30 jours.", path)
    docs = load_file(path)
    assert docs[0].metadata["title"] == long_title
