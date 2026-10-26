"""Ingestion : chargement des documents (PDF, Markdown, texte) et découpage en chunks."""

from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document

from rag_btp.config import get_settings
from rag_btp.ingestion.chunking import make_chunk_id, split_documents
from rag_btp.ingestion.loaders import (
    CHANTIERS,
    DOC_TYPES,
    SUPPORTED_EXTENSIONS,
    load_directory,
    load_file,
    parse_filename_metadata,
)


def ingest_directory(directory: Path | None = None) -> list[Document]:
    """Pipeline complet : chargement du dossier puis découpage en chunks."""
    settings = get_settings()
    documents = load_directory(directory or settings.raw_data_dir)
    return split_documents(documents, settings.chunk_size, settings.chunk_overlap)


__all__ = [
    "CHANTIERS",
    "DOC_TYPES",
    "SUPPORTED_EXTENSIONS",
    "ingest_directory",
    "load_directory",
    "load_file",
    "make_chunk_id",
    "parse_filename_metadata",
    "split_documents",
]
