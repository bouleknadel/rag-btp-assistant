"""Découpage des documents en chunks avec des identifiants déterministes.

Chaque chunk reçoit :
- un en-tête de contexte (titre + chantier) pour qu'un extrait isolé reste
  compréhensible par le moteur de recherche et le LLM ;
- un identifiant stable, calculé à partir de la source, de la page et du
  contenu : réindexer le même corpus ne crée pas de doublons.
"""

from __future__ import annotations

import hashlib

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Du séparateur le plus « fort » au plus faible : on coupe de préférence
# entre deux sections, puis entre paragraphes, lignes, phrases, mots.
SEPARATORS = ["\n## ", "\n# ", "\n\n", "\n", ". ", " ", ""]


def make_chunk_id(source: str, page: int, chunk_index: int, content: str) -> str:
    """Identifiant déterministe d'un chunk (16 caractères hexadécimaux)."""
    digest = hashlib.sha256(f"{source}|{page}|{chunk_index}|{content}".encode()).hexdigest()
    return digest[:16]


def context_header(metadata: dict) -> str:
    """En-tête ajouté en tête de chaque chunk."""
    return f"[{metadata.get('title', '')} — {metadata.get('chantier_label', '')}]"


def split_documents(
    documents: list[Document],
    chunk_size: int = 800,
    chunk_overlap: int = 120,
    add_context_header: bool = True,
) -> list[Document]:
    """Découpe les documents en chunks et enrichit leurs métadonnées."""
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap doit être strictement inférieur à chunk_size")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=SEPARATORS,
        keep_separator=True,
    )

    chunks: list[Document] = []
    for doc in documents:
        page = int(doc.metadata.get("page", 1))
        for index, text in enumerate(splitter.split_text(doc.page_content)):
            text = text.strip()
            if not text:
                continue
            content = f"{context_header(doc.metadata)}\n{text}" if add_context_header else text
            chunk_id = make_chunk_id(doc.metadata.get("source", ""), page, index, text)
            metadata = {**doc.metadata, "chunk_index": index, "chunk_id": chunk_id}
            chunks.append(Document(page_content=content, metadata=metadata, id=chunk_id))
    return chunks
