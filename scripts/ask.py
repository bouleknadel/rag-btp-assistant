"""Pose une question à l'assistant RAG depuis le terminal.

Usage :
    python scripts/ask.py "Quel est le délai de levée des réserves du lot plâtrerie ?"
    python scripts/ask.py "Quelles observations lors de la visite CSPS ?" --chantier tilleuls
    python scripts/ask.py --graph      # affiche le graphe LangGraph (Mermaid)

L'index doit avoir été construit au préalable (``python scripts/ingest.py``).
"""

from __future__ import annotations

import argparse
import logging
import time

from rag_btp.graph import answer_question, get_rag_graph


def main() -> None:
    parser = argparse.ArgumentParser(description="Question à l'assistant RAG BTP")
    parser.add_argument("question", nargs="?")
    parser.add_argument("--chantier", help="filtre : tilleuls, jean-moulin")
    parser.add_argument("--doc-type", help="filtre : compte_rendu, essais, securite…")
    parser.add_argument("--graph", action="store_true", help="affiche le graphe (Mermaid)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    for noisy in ("httpx", "huggingface_hub", "sentence_transformers", "google_genai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    if args.graph:
        print(get_rag_graph().get_graph().draw_mermaid())
        return
    if not args.question:
        parser.error("indiquez une question (ou --graph)")

    start = time.perf_counter()
    try:
        result = answer_question(args.question, chantier=args.chantier, doc_type=args.doc_type)
    except Exception as exc:  # erreur d'API (quota, timeout, clé invalide…)
        raise SystemExit(f"\nErreur lors de l'appel au LLM : {type(exc).__name__}: {exc}") from exc
    elapsed = time.perf_counter() - start

    print(f"\nQuestion : {result.question}")
    if result.search_query:
        print(f"Requête reformulée : {result.search_query}")
    print(f"\n{result.answer}\n")
    print(
        f"--- Statut : {result.status} | essais : {result.attempts} | "
        f"prompts : {result.prompt_version} | {elapsed:.1f} s"
    )
    for src in result.sources:
        mark = "✓" if src["cited"] else " "
        print(f" {mark} [{src['index']}] {src['source']} (p. {src['page']})")


if __name__ == "__main__":
    main()
