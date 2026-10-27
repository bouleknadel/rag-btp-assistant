"""Vérifie que toutes les images référencées par le README existent.

Usage :
    python scripts/check_readme_images.py         # liste les images manquantes
    python scripts/check_readme_images.py --fix   # retire du README les lignes qui les référencent

Utile avant un commit : une image absente s'affiche « cassée » sur GitHub.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
IMAGE_REF = re.compile(r"""(?:src=["']|\]\()(docs/images/[^"')\s]+)""")


def missing_images(text: str) -> list[str]:
    refs = dict.fromkeys(IMAGE_REF.findall(text))
    return [ref for ref in refs if not (ROOT / ref).exists()]


def remove_empty_sections(text: str) -> str:
    """Supprime un titre « ## … » qui n'a plus de contenu avant le titre suivant."""
    lines, result = text.splitlines(), []
    for i, line in enumerate(lines):
        if line.startswith("## "):
            rest = next((li for li in lines[i + 1 :] if li.strip()), "")
            if rest.startswith("## "):
                continue
        result.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(result))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fix", action="store_true", help="retire les lignes des images absentes")
    args = parser.parse_args()

    text = README.read_text(encoding="utf-8")
    missing = missing_images(text)
    if not missing:
        print("Toutes les images du README sont présentes.")
        return
    print("Images manquantes :\n" + "\n".join(f"  - {m}" for m in missing))
    if not args.fix:
        sys.exit("Ajoutez-les dans docs/images/ ou relancez avec --fix.")

    kept = [line for line in text.splitlines() if not any(m in line for m in missing)]
    README.write_text(remove_empty_sections("\n".join(kept)) + "\n", encoding="utf-8")
    print(f"{len(missing)} référence(s) retirée(s) du README.")


if __name__ == "__main__":
    main()
