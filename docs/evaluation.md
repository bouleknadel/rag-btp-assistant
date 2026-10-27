# Méthode d'évaluation

## Dataset

`evaluation/dataset.json` : 33 questions rédigées à partir du corpus de démonstration,
chacune avec une réponse de référence et le ou les documents sources attendus.

| Catégorie | Nombre | Ce qui est testé |
|---|---|---|
| `factuel` | 29 | Retrouver et restituer une information précise (valeurs, dates, noms) |
| `evolution` | 1 | Donner la valeur la plus récente quand deux documents se contredisent |
| `hors_corpus` | 3 | Refuser de répondre quand l'information n'existe pas (anti-hallucination) |

Un test (`tests/test_evaluation.py`) vérifie que chaque source attendue existe bien
dans le corpus.

## Mesures

| Mesure | Calcul | Évalue |
|---|---|---|
| **Taux de pertinence** (principale) | Questions réussies / questions évaluées | Le système de bout en bout |
| Réponses correctes | Verdict `correct` du juge (questions du corpus) | Exactitude des faits |
| Retrieval hit | Document attendu parmi les extraits retrouvés | Recherche + reranking |
| Citation | Document attendu cité dans la réponse | Traçabilité des sources |
| Refus hors corpus | Statut `not_found` sur les questions hors corpus | Résistance aux hallucinations |

Une question est **réussie** si :
- question du corpus : le juge LLM la note à la fois `pertinent` (elle traite la question)
  et `correct` (faits essentiels de la référence présents, aucune contradiction,
  exigence sur les chiffres) ; une réponse « non trouvé » est un échec, sans appel au juge ;
- question hors corpus : l'assistant répond qu'il n'a pas trouvé l'information
  (vérification déterministe, sans juge).

Les erreurs d'API (quota, indisponibilité) sont comptées à part et exclues du taux ;
le rapport signale alors un score partiel.

## Lancer l'évaluation

```bash
python scripts/evaluate.py                          # version de prompts du .env
python scripts/evaluate.py --prompt-versions v1 v3  # comparaison de versions
python scripts/evaluate.py --judge-provider gemini  # juge distinct du générateur
python scripts/evaluate.py --langsmith              # dataset + expérience dans LangSmith
```

Résultats : `evaluation/results/<date>_<version>.md` (résumé) et `.json` (détail par question).

## Limites

- Le juge est un LLM : son verdict peut se tromper. Utiliser un juge d'un autre
  fournisseur que le générateur (`--judge-provider`) limite le biais d'auto-évaluation.
- 33 questions sur un corpus synthétique : un ordre de grandeur, pas une garantie de
  performance sur des documents réels.
- Les résultats varient légèrement d'une exécution à l'autre (LLM non déterministe).
