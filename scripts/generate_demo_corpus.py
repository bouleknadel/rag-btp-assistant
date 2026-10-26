"""Génère le corpus de démonstration dans ``data/raw/``.

Usage :
    python scripts/generate_demo_corpus.py                       # 20 documents de base
    python scripts/generate_demo_corpus.py --daily-reports 400   # + 400 rapports journaliers

Les documents de base sont versionnés dans le dépôt. Les rapports journaliers
générés (option ``--daily-reports``) sont écrits dans ``data/raw/generated/``,
ignoré par Git : ils servent à simuler un corpus volumineux (400+ documents).
Toutes les données sont synthétiques.
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab import rl_config
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from demo_corpus import DOCUMENTS  # noqa: E402

# PDF reproductibles à l'octet près (pas de date de création ni d'identifiant aléatoire).
rl_config.invariant = 1

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


# ---------------------------------------------------------------------------
# Rendu PDF d'un Markdown simplifié
# ---------------------------------------------------------------------------
# Symboles absents des polices PDF standard (Helvetica) : remplacés à l'écriture.
_PDF_SUBSTITUTIONS = {"≤": "<=", "≥": ">=", "λ": "lambda"}


def render_pdf(markdown: str, path: Path) -> None:
    """Rend un Markdown simplifié (titres #/##, listes -, paragraphes) en PDF."""
    for symbol, replacement in _PDF_SUBSTITUTIONS.items():
        markdown = markdown.replace(symbol, replacement)
    styles = getSampleStyleSheet()
    story: list = []
    bullets: list[ListItem] = []

    def flush_bullets() -> None:
        if bullets:
            story.append(ListFlowable(list(bullets), bulletType="bullet", leftIndent=12))
            bullets.clear()

    for raw_line in markdown.strip().splitlines():
        line = raw_line.strip()
        if line.startswith("- "):
            bullets.append(ListItem(Paragraph(escape(line[2:]), styles["BodyText"])))
            continue
        flush_bullets()
        if not line:
            story.append(Spacer(1, 4))
        elif line.startswith("## "):
            story.append(Paragraph(escape(line[3:]), styles["Heading2"]))
        elif line.startswith("# "):
            story.append(Paragraph(escape(line[2:]), styles["Heading1"]))
        else:
            story.append(Paragraph(escape(line), styles["BodyText"]))
    flush_bullets()

    title = markdown.strip().splitlines()[0].lstrip("# ").strip()
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=title,
        author="Corpus de démonstration (données synthétiques)",
    )
    doc.build(story)


def write_document(filename: str, content: str, out_dir: Path) -> Path:
    path = out_dir / filename
    if path.suffix == ".pdf":
        render_pdf(content, path)
    else:
        path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Rapports journaliers générés (simulation d'un corpus volumineux)
# ---------------------------------------------------------------------------
_TRAVAUX = [
    "Coffrage et ferraillage des voiles du niveau {niveau}",
    "Coulage de la dalle haute du niveau {niveau} ({volume} m³ de béton C25/30)",
    "Décoffrage et ragréage des voiles du niveau {niveau}",
    "Pose des prédalles et des réservations au niveau {niveau}",
    "Montage des escaliers préfabriqués du niveau {niveau}",
    "Réalisation des longrines et du dallage du sous-sol",
    "Pose des réseaux enterrés (eaux pluviales et eaux usées)",
    "Maçonnerie des cloisons du local technique au niveau {niveau}",
]
_METEO = [
    "Temps sec et ensoleillé",
    "Ciel couvert, vent faible",
    "Averses en matinée",
    "Pluie continue, travaux extérieurs réduits",
    "Gel matinal, démarrage différé à 9 h 00",
]
_OBSERVATIONS = [
    "Aucune observation particulière.",
    "Livraison d'aciers HA en retard de 2 heures.",
    "Panne de la pompe à béton pendant 30 minutes.",
    "Visite du bureau de contrôle sur les armatures.",
    "Nettoyage et rangement des zones de stockage.",
    "Quart d'heure sécurité sur le port des EPI.",
]


def daily_report(day: date, rng: random.Random) -> str:
    niveau = rng.choice(["R+1", "R+2", "R+3", "R+4"])
    securite = "Aucun accident." if rng.random() > 0.05 else "Presqu'accident déclaré."
    travaux = rng.sample(_TRAVAUX, k=2)
    lines = [
        f"# Rapport journalier de chantier — {day:%d/%m/%Y}",
        "",
        "Chantier : Résidence Les Tilleuls",
        "Rédigé par : chef de chantier, BTP Rhodanien SAS",
        "",
        "## Conditions",
        "",
        f"- Météo : {rng.choice(_METEO)}.",
        f"- Température à 7 h 30 : {rng.randint(-3, 22)} °C.",
        f"- Effectif : {rng.randint(10, 22)} compagnons.",
        "",
        "## Travaux réalisés",
        "",
    ]
    for t in travaux:
        lines.append(f"- {t.format(niveau=niveau, volume=rng.randint(20, 95))}.")
    lines += [
        "",
        "## Sécurité",
        "",
        f"- {securite}",
        "",
        "## Observations",
        "",
        f"- {rng.choice(_OBSERVATIONS)}",
    ]
    return "\n".join(lines)


def generate_daily_reports(count: int, out_dir: Path, seed: int = 42) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    day = date(2025, 11, 3)
    written = 0
    while written < count:
        if day.weekday() < 5:  # jours ouvrés uniquement
            name = f"tilleuls__rapport_journalier__genere-{day:%Y-%m-%d}.md"
            (out_dir / name).write_text(daily_report(day, rng) + "\n", encoding="utf-8")
            written += 1
        day += timedelta(days=1)
    return written


# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--daily-reports",
        type=int,
        default=0,
        metavar="N",
        help="génère en plus N rapports journaliers synthétiques (data/raw/generated/)",
    )
    parser.add_argument("--out", type=Path, default=RAW_DIR, help="dossier de sortie")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    for doc in DOCUMENTS:
        write_document(doc.filename, doc.content, args.out)
    print(f"{len(DOCUMENTS)} documents de base écrits dans {args.out}")

    if args.daily_reports:
        n = generate_daily_reports(args.daily_reports, args.out / "generated")
        print(f"{n} rapports journaliers générés dans {args.out / 'generated'}")


if __name__ == "__main__":
    main()
