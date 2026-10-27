# Journal des itérations

Ce document trace les problèmes observés pendant le développement, leur diagnostic
et la correction apportée. Chaque itération est vérifiée par un test de non-régression.

## Itération 1 — Recherche : réponse introuvable en fin de chunk

### Symptôme

Question : *« Quel est le délai de levée des réserves du lot plâtrerie ? »*

Le graphe RAG répond `not_found` alors que la réponse (30 jours, au plus tard le
23 avril 2026) figure dans le PV de réception du lot 08.

### Diagnostic

`python scripts/search.py "<question>"` montre que le PV n'est **même pas dans les
20 candidats** de la recherche vectorielle (tous les scores du reranker < 0,06).
Le problème vient donc du *retrieval*, pas du prompt de génération. Deux causes :

1. **Titre tronqué** : dans le PDF, le titre « … Lot n° 08 Plâtrerie » est rendu sur
   deux lignes ; le loader ne gardait que la première. L'en-tête de contexte des
   chunks ne contenait donc pas le mot « Plâtrerie ».
2. **Fenêtre du modèle d'embeddings** : `paraphrase-multilingual-MiniLM-L12-v2`
   tronque les textes à **128 tokens** (~80 mots). La phrase contenant la réponse
   commence au 82e mot du chunk : elle n'était jamais encodée. Ce modèle est de plus
   entraîné pour la similarité de phrases, pas pour la recherche question → passage.

### Correction

- Le titre des PDF est lu dans les **métadonnées** du fichier (complet), avec la
  première ligne du texte en repli.
- Passage à **`intfloat/multilingual-e5-small`** : même taille (384 dimensions, CPU),
  **512 tokens** de contexte (un chunk de 800 caractères est encodé en entier) et
  entraînement spécifique à la recherche documentaire, avec les préfixes
  `query:` / `passage:`.

### Vérification

- `tests/test_ingestion.py::test_pdf_title_comes_from_metadata_even_if_wrapped`
- `tests/test_retrieval.py::test_real_reranker_improves_ranking` (intégration) :
  le PV de réception doit sortir en 1re position avec « 30 jours ».
