"""Configuration commune des tests.

Les tests ne doivent jamais envoyer de traces vers LangSmith, même si le fichier
``.env`` du développeur active le tracing. Les variables sont fixées ici, avant
l'import de ``rag_btp.config`` (``load_dotenv`` ne remplace pas une variable existante).
"""

import os

os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
