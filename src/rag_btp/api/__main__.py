"""Lance l'API : ``python -m rag_btp.api`` (équivalent à ``uvicorn rag_btp.api.main:app``).

Variables d'environnement optionnelles :
- ``API_HOST`` (défaut 127.0.0.1) : mettre 0.0.0.0 pour que n8n, lancé dans Docker,
  puisse joindre l'API via host.docker.internal ;
- ``API_PORT`` (défaut 8000).
"""

import logging
import os

import uvicorn

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    for noisy in ("httpx", "huggingface_hub", "sentence_transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    uvicorn.run(
        "rag_btp.api.main:app",
        host=os.getenv("API_HOST", "127.0.0.1"),
        port=int(os.getenv("API_PORT", "8000")),
    )
