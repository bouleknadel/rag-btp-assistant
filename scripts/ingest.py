"""Indexe les documents dans ChromaDB.

Usage :
    python scripts/ingest.py                    # indexe data/raw (incrémental)
    python scripts/ingest.py --reset            # vide la collection puis réindexe tout
    python scripts/ingest.py --dir mon/dossier  # indexe un autre dossier
    python scripts/ingest.py --query "résistance béton dalle R+2"  # test de recherche
"""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

from rag_btp.config import get_settings
from rag_btp.indexing import get_vector_store, index_directory


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Indexation des documents dans ChromaDB")
    parser.add_argument("--dir", type=Path, default=settings.raw_data_dir)
    parser.add_argument("--reset", action="store_true", help="vide la collection avant")
    parser.add_argument("--query", help="question de test après indexation")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    # Masque les logs HTTP du téléchargement du modèle (Hugging Face).
    for noisy in ("httpx", "huggingface_hub", "sentence_transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    print(f"Modèle d'embeddings : {settings.embedding_model}")
    print(f"Collection Chroma   : {settings.chroma_collection} ({settings.chroma_persist_dir})")
    start = time.perf_counter()
    store = get_vector_store()
    report = index_directory(args.dir, store=store, reset=args.reset)
    elapsed = time.perf_counter() - start

    print(f"\nDocuments traités   : {report.documents}")
    print(f"Chunks indexés      : {report.chunks_upserted}")
    print(f"Chunks obsolètes    : {report.chunks_deleted} supprimé(s)")
    print(f"Total en base       : {report.total_in_collection}")
    print(f"Durée               : {elapsed:.1f} s")

    if args.query:
        print(f"\nRecherche : {args.query!r}")
        results = store.similarity_search_with_score(args.query, k=3)
        for rank, (doc, distance) in enumerate(results, start=1):
            print(f"\n#{rank}  score={1 - distance:.3f}  {doc.metadata['source']}")
            print("   " + doc.page_content[:250].replace("\n", " ") + "…")


if __name__ == "__main__":
    main()
