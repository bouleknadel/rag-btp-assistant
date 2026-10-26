"""Chargement des documents (PDF, Markdown, texte) avec leurs métadonnées.

Convention de nommage : ``<chantier>__<type>__<nom>.<ext>``,
par exemple ``tilleuls__compte_rendu__reunion-chantier-14.pdf``.
Un fichier hors convention est tout de même chargé, avec ``chantier="inconnu"``
et ``doc_type="autre"``.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from pathlib import Path

from langchain_core.documents import Document
from pypdf import PdfReader

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt"}

DOC_TYPES = {
    "compte_rendu": "Compte-rendu de réunion",
    "rapport_journalier": "Rapport journalier",
    "rapport_hebdo": "Rapport hebdomadaire",
    "fiche_technique": "Fiche technique",
    "cctp": "CCTP",
    "securite": "Sécurité",
    "incident": "Incident",
    "essais": "Essais",
    "non_conformite": "Non-conformité",
    "pv_reception": "PV de réception",
    "geotechnique": "Étude géotechnique",
    "planning": "Planning",
    "autre": "Autre",
}

CHANTIERS = {
    "tilleuls": "Résidence Les Tilleuls",
    "jean-moulin": "Groupe scolaire Jean Moulin",
}


def parse_filename_metadata(path: Path) -> dict[str, str]:
    """Extrait le chantier et le type de document du nom de fichier."""
    parts = path.stem.split("__")
    if len(parts) >= 3 and parts[1] in DOC_TYPES:
        chantier, doc_type = parts[0], parts[1]
    else:
        chantier, doc_type = "inconnu", "autre"
    return {
        "chantier": chantier,
        "chantier_label": CHANTIERS.get(chantier, chantier.replace("-", " ").title()),
        "doc_type": doc_type,
        "doc_type_label": DOC_TYPES[doc_type],
    }


def _clean_text(text: str) -> str:
    """Normalise les espaces sans casser la structure en paragraphes."""
    text = text.replace(" ", " ").replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_title(text: str, fallback: str) -> str:
    """Première ligne non vide du document, sans marqueurs Markdown."""
    for line in text.splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line[:200]
    return fallback


def load_file(path: Path, base_dir: Path | None = None) -> list[Document]:
    """Charge un fichier : un ``Document`` par page pour un PDF, un seul sinon."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Extension non supportée : {path.name}")

    source = path.relative_to(base_dir).as_posix() if base_dir else path.name
    base_meta = {"source": source, "file_name": path.name, **parse_filename_metadata(path)}

    if suffix == ".pdf":
        reader = PdfReader(path)
        pages = [_clean_text(page.extract_text() or "") for page in reader.pages]
        title = _extract_title(pages[0] if pages else "", path.stem)
        return [
            Document(page_content=text, metadata={**base_meta, "title": title, "page": i})
            for i, text in enumerate(pages, start=1)
            if text
        ]

    text = _clean_text(path.read_text(encoding="utf-8"))
    if not text:
        return []
    title = _extract_title(text, path.stem)
    return [Document(page_content=text, metadata={**base_meta, "title": title, "page": 1})]


def iter_supported_files(directory: Path) -> Iterable[Path]:
    """Parcourt récursivement un dossier, dans un ordre déterministe."""
    for path in sorted(Path(directory).rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def load_directory(directory: Path) -> list[Document]:
    """Charge tous les documents supportés d'un dossier (récursif).

    Un fichier illisible est ignoré avec un avertissement, sans bloquer le reste.
    """
    directory = Path(directory)
    documents: list[Document] = []
    for path in iter_supported_files(directory):
        try:
            documents.extend(load_file(path, base_dir=directory))
        except Exception as exc:  # fichier corrompu, encodage invalide…
            logger.warning("Fichier ignoré %s : %s", path.name, exc)
    return documents
