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

## Itération 2 — Prompts : faux négatifs au tri de pertinence

### Symptôme

Après l'itération 1, le retriever renvoie bien le PV de réception en 1re position
(test d'intégration au vert), mais le graphe répond encore `not_found` à la question
sur le délai de levée des réserves, avec les prompts **v1**.

### Diagnostic

La recherche étant correcte, l'extrait est écarté à l'étape `grade` : le prompt v1
(« évalue la pertinence… réponds en JSON ») est trop vague. Le modèle attend une
correspondance quasi littérale entre la question et l'extrait, et ne sait pas quoi
faire en cas de doute. L'option `--debug` de `scripts/ask.py` affiche, pour chaque
extrait retrouvé, la décision GARDÉ / REJETÉ et la réponse brute du tri :

```bash
python scripts/ask.py "Quel est le délai de levée des réserves du lot plâtrerie ?" --prompt-version v1 --debug
python scripts/ask.py "Quel est le délai de levée des réserves du lot plâtrerie ?" --prompt-version v3 --debug
```

### Corrections (détaillées en tête de chaque fichier `src/rag_btp/prompts/vN.py`)

| Version | Tri de pertinence (grade) | Réponse (answer) | Synthèse de rapport |
|---|---|---|---|
| v1 | Consigne vague, liste de numéros | « Réponds à partir du contexte » | Résumé libre |
| v2 | Définition d'un extrait pertinent, « en cas de doute, garder », exemple JSON | Contexte uniquement, phrase imposée si absent, chiffres exacts, citations obligatoires | Plan imposé en 6 sections, « Non mentionné » |
| v3 | Évaluation extrait par extrait avec justification courte avant la décision | Réponse directe d'abord, ≤ 4 puces, document le plus récent en cas de contradiction, chantier précisé | JSON validé par schéma (exploitable par l'API et n8n) |

La version active se choisit avec `PROMPT_VERSION` dans `.env` (défaut : v3) ou
`--prompt-version` en ligne de commande. Le gain de chaque version est mesuré par le
script d'évaluation (taux de pertinence sur le dataset de questions/réponses).

## Itération 3 — Évaluation : citations non détectées

### Symptôme

Lors de la première évaluation (prompts v1), le taux de pertinence est de 93,5 % mais le
taux de « document attendu cité » n'est que de 64,3 %, alors que le document attendu est
retrouvé dans 100 % des cas.

### Diagnostic

L'inspection des réponses brutes du modèle `openai/gpt-oss-120b` montre qu'il cite souvent
ses sources avec des crochets pleine chasse : `…au plus tard le 23 avril 2026【 1】.`
L'extraction des citations ne reconnaissait que `[1]` : ces sources étaient donc
comptées comme « non citées ». Le problème venait de la **mesure**, pas du modèle.

### Correction

`normalize_citations()` convertit `【1】`, `【 1】`, `【2, 3】` et `【4†L1-L5】` en `[1]`,
`[2,3]`, `[4]` avant l'extraction des citations ; la réponse renvoyée à l'utilisateur est
elle aussi normalisée.

### Vérification

- `tests/test_graph.py::test_fullwidth_citations_are_normalized`
- `tests/test_graph.py::test_graph_detects_fullwidth_citation_as_cited`
- Relancer `python scripts/evaluate.py` pour mesurer le taux de citation corrigé.

## Itération 4 — Observabilité : traces LangSmith perdues

### Symptôme

Avec le tracing activé, aucune trace n'apparaît dans LangSmith après `scripts/ask.py`.

### Diagnostic

Deux causes : le compte LangSmith est hébergé dans la région **UE** alors que l'endpoint
configuré était celui des États-Unis ; et les traces sont envoyées en arrière-plan, un
script court peut se terminer avant la fin de l'envoi.

### Correction

`LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com` pour un compte UE (documenté dans
`.env.example`), et appel à `wait_for_all_tracers()` à la fin de `ask.py` et `evaluate.py`.
