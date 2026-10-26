# RAG BTP Assistant

Assistant RAG (Retrieval-Augmented Generation) pour l'exploitation de documents techniques
de chantiers BTP : rapports de chantier, fiches techniques, comptes-rendus de sécurité.

> Projet en cours de développement — la documentation complète sera ajoutée à la fin.

## Structure du projet

```
rag-btp-assistant/
├── src/rag_btp/
│   ├── config.py        # Configuration centralisée (.env)
│   ├── ingestion/       # Chargement des documents + chunking
│   ├── indexing/        # Embeddings + ChromaDB
│   ├── retrieval/       # Recherche vectorielle + reranking
│   ├── llm/             # Fournisseurs LLM (Groq, OpenAI, Gemini)
│   ├── prompts/         # Prompts versionnés
│   ├── graph/           # Graphe RAG LangGraph
│   ├── api/             # API FastAPI
│   └── evaluation/      # Évaluation LangSmith
├── scripts/             # Scripts CLI (génération du corpus, ingestion, évaluation)
├── data/raw/            # Documents de démonstration
├── evaluation/          # Dataset et résultats d'évaluation
├── n8n/                 # Workflow d'automatisation n8n
└── tests/               # Tests pytest
```

## Installation rapide

```bash
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
# Sans GPU : PyTorch CPU (~200 Mo au lieu de ~2 Go avec CUDA)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-dev.txt
pip install -e .
cp .env.example .env               # puis renseigner les clés API
```

> Les documents de démonstration sont **synthétiques** : les documents réels de l'entreprise
> sont confidentiels et ne font pas partie de ce dépôt.
