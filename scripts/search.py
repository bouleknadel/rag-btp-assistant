"""Compare la recherche vectorielle seule et la recherche avec reranking.

Usage :
    python scripts/search.py "résistance à 28 jours de la dalle du R+2"
    python scripts/search.py "réserves plâtrerie" --chantier jean-moulin
    python scripts/search.py "consignes grue" --doc-type securite --top-n 3

L'index doit avoir été construit au préalable (``python scripts/ingest.py``).
"""

from __future__ import annotations

import argparse
import logging
import time

from langchain_core.documents import Document

from rag_btp.retrieval import get_retriever


def show(title: str, documents: list[Document], elapsed: float) -> None:
    print(f"\n=== {title} ({elapsed:.2f} s) ===")
    for rank, doc in enumerate(documents, start=1):
        scores = f"vecteur={doc.metadata['vector_score']:.3f}"
        if "rerank_score" in doc.metadata:
            scores += f"  rerank={doc.metadata['rerank_score']:.3f}"
        print(f"#{rank}  {scores}  {doc.metadata['source']} (p. {doc.metadata['page']})")
        print("    " + doc.page_content.split("\n", 1)[-1][:160].replace("\n", " ") + "…")


def main() -> None:
    parser = argparse.ArgumentParser(description="Recherche dans l'index ChromaDB")
    parser.add_argument("query")
    parser.add_argument("--chantier", help="filtre : tilleuls, jean-moulin…")
    parser.add_argument("--doc-type", help="filtre : compte_rendu, essais, securite…")
    parser.add_argument("--top-n", type=int, help="nombre de résultats affichés")
    args = parser.parse_args()
    for noisy in ("httpx", "huggingface_hub", "sentence_transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    filters = {"chantier": args.chantier, "doc_type": args.doc_type}
    print(f"Question : {args.query!r}  filtres={ {k: v for k, v in filters.items() if v} }")

    for title, use_reranker in (("Recherche vectorielle seule", False), ("Avec reranking", True)):
        retriever = get_retriever(use_reranker=use_reranker)
        if args.top_n:
            retriever.top_n = args.top_n
        retriever.invoke("préchauffage")  # charge les modèles hors chronométrage
        start = time.perf_counter()
        documents = retriever.invoke(args.query, **filters)
        show(title, documents, time.perf_counter() - start)


if __name__ == "__main__":
    main()
