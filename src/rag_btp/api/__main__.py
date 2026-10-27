"""Lance l'API : ``python -m rag_btp.api`` (équivalent à ``uvicorn rag_btp.api.main:app``)."""

import logging

import uvicorn

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    for noisy in ("httpx", "huggingface_hub", "sentence_transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    uvicorn.run("rag_btp.api.main:app", host="127.0.0.1", port=8000)
