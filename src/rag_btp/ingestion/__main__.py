"""Aperçu de l'ingestion : ``python -m rag_btp.ingestion [dossier]``.

Charge et découpe les documents, puis affiche des statistiques et un exemple de chunk.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from rag_btp.config import get_settings
from rag_btp.ingestion import ingest_directory


def main() -> None:
    directory = Path(sys.argv[1]) if len(sys.argv) > 1 else get_settings().raw_data_dir
    chunks = ingest_directory(directory)
    if not chunks:
        print(f"Aucun document trouvé dans {directory}")
        return

    sources = {c.metadata["source"] for c in chunks}
    sizes = [len(c.page_content) for c in chunks]
    print(f"Dossier          : {directory}")
    print(f"Documents        : {len(sources)}")
    print(f"Chunks           : {len(chunks)}")
    print(f"Taille moyenne   : {sum(sizes) // len(sizes)} caractères (max {max(sizes)})")

    print("\nChunks par chantier :")
    for chantier, n in Counter(c.metadata["chantier"] for c in chunks).most_common():
        print(f"  {chantier:<15} {n}")
    print("\nChunks par type de document :")
    for doc_type, n in Counter(c.metadata["doc_type"] for c in chunks).most_common():
        print(f"  {doc_type:<20} {n}")

    sample = chunks[len(chunks) // 2]
    print(f"\nExemple de chunk ({sample.metadata['chunk_id']}) :")
    print(sample.page_content)


if __name__ == "__main__":
    main()
