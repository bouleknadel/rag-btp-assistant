"""API FastAPI de l'assistant RAG BTP.

Lancement :
    uvicorn rag_btp.api.main:app --reload
Documentation interactive : http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import logging
import tempfile
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.responses import RedirectResponse

from rag_btp import __version__
from rag_btp.api.schemas import (
    AskRequest,
    AskResponse,
    HealthResponse,
    IngestResponse,
    SummarizeRequest,
    SummarizeResponse,
)
from rag_btp.api.services import Services
from rag_btp.evaluation.tracing import tracing_enabled
from rag_btp.graph import answer_question
from rag_btp.indexing import collection_count, index_directory, index_files
from rag_btp.ingestion import SUPPORTED_EXTENSIONS, load_file
from rag_btp.prompts import get_prompts
from rag_btp.summary import summarize_report

logger = logging.getLogger(__name__)


def create_app(services: Services | None = None) -> FastAPI:
    """Crée l'application. ``services`` est injecté dans les tests (modèles factices)."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if getattr(app.state, "services", None) is None:
            logger.info("Chargement des modèles et de l'index…")
            app.state.services = Services.from_settings()
        yield

    app = FastAPI(
        title="RAG BTP Assistant",
        version=__version__,
        description=(
            "Assistant RAG pour les documents techniques de chantiers BTP : "
            "questions-réponses sourcées, ingestion de documents et synthèse de rapports."
        ),
        lifespan=lifespan,
    )
    app.state.services = services
    _register_routes(app)
    return app


def get_services(request: Request) -> Services:
    return request.app.state.services


ServicesDep = Annotated[Services, Depends(get_services)]


def _require_llm(services: Services) -> None:
    if services.llm is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Aucun LLM configuré : renseignez une clé API dans le fichier .env.",
        )


def _llm_error(exc: Exception) -> HTTPException:
    logger.exception("Erreur du fournisseur LLM")
    message = str(exc).splitlines()[0][:300] if str(exc) else ""
    return HTTPException(
        status.HTTP_502_BAD_GATEWAY, f"Erreur du fournisseur LLM : {type(exc).__name__} {message}"
    )


async def _save_upload(upload: UploadFile, directory: Path, max_bytes: int) -> Path:
    """Enregistre un fichier envoyé après validation (extension, taille, nom)."""
    name = Path(upload.filename or "").name  # supprime tout chemin (sécurité)
    if Path(name).suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"{name or 'fichier'} : extensions acceptées {sorted(SUPPORTED_EXTENSIONS)}",
        )
    content = await upload.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE, f"{name} dépasse {max_bytes // 1_000_000} Mo"
        )
    if not content:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{name} est vide")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_bytes(content)
    return path


def _register_routes(app: FastAPI) -> None:
    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    @app.get("/health", response_model=HealthResponse, tags=["système"])
    def health(services: ServicesDep) -> HealthResponse:
        """État du service : index, fournisseurs LLM, modèles et version des prompts."""
        settings = services.settings
        return HealthResponse(
            status="ok" if services.llm is not None else "degraded",
            documents_indexed=collection_count(services.store),
            llm_providers=services.llm_providers,
            prompt_version=settings.prompt_version,
            langsmith_tracing=tracing_enabled(),
            embedding_model=settings.embedding_model,
            reranker_model=settings.reranker_model,
        )

    @app.post("/ingest", response_model=IngestResponse, tags=["ingestion"])
    async def ingest(
        files: Annotated[list[UploadFile], File(description="Documents PDF, .md ou .txt")],
        services: ServicesDep,
    ) -> IngestResponse:
        """Ajoute des documents à la base : enregistrement dans data/raw/uploads puis indexation.

        Convention de nommage conseillée : ``<chantier>__<type>__<nom>.pdf``.
        Renvoyer un fichier du même nom remplace ses anciens chunks.
        """
        settings = services.settings
        upload_dir = settings.raw_data_dir / settings.upload_subdir
        max_bytes = settings.max_upload_mb * 1_000_000
        paths = [await _save_upload(f, upload_dir, max_bytes) for f in files]
        report = index_files(paths, base_dir=settings.raw_data_dir, store=services.store)
        return IngestResponse(files=[p.name for p in paths], **vars(report))

    @app.post("/ingest/reindex", response_model=IngestResponse, tags=["ingestion"])
    def reindex(services: ServicesDep, reset: bool = False) -> IngestResponse:
        """Réindexe tout le dossier data/raw (``reset=true`` : vide d'abord la collection)."""
        report = index_directory(services.settings.raw_data_dir, store=services.store, reset=reset)
        return IngestResponse(files=[], **vars(report))

    @app.post("/ask", response_model=AskResponse, tags=["questions"])
    def ask(request: AskRequest, services: ServicesDep) -> AskResponse:
        """Pose une question sur les documents de chantier ; réponse sourcée."""
        _require_llm(services)
        start = time.perf_counter()
        try:
            result = answer_question(
                request.question,
                chantier=request.chantier,
                doc_type=request.doc_type,
                prompt_version=request.prompt_version,
                graph=services.graph(request.prompt_version),
            )
        except Exception as exc:
            raise _llm_error(exc) from exc
        data = result.model_dump()
        if not request.debug:
            data.update(retrieved=None, grade_raw=None)
        return AskResponse(**data, duration_ms=int((time.perf_counter() - start) * 1000))

    def _summarize(text: str, version: str | None, services: Services) -> SummarizeResponse:
        _require_llm(services)
        start = time.perf_counter()
        try:
            result = summarize_report(text, services.llm, get_prompts(version))
        except ValueError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
        except Exception as exc:
            raise _llm_error(exc) from exc
        return SummarizeResponse(
            **result.model_dump(), duration_ms=int((time.perf_counter() - start) * 1000)
        )

    @app.post("/summarize", response_model=SummarizeResponse, tags=["synthèse"])
    def summarize(request: SummarizeRequest, services: ServicesDep) -> SummarizeResponse:
        """Synthèse d'un rapport de chantier : résumé, avancement, problèmes, sécurité, actions."""
        return _summarize(request.text, request.prompt_version, services)

    @app.post("/summarize/file", response_model=SummarizeResponse, tags=["synthèse"])
    async def summarize_file(
        file: Annotated[UploadFile, File(description="Rapport PDF, .md ou .txt")],
        services: ServicesDep,
    ) -> SummarizeResponse:
        """Synthèse d'un rapport envoyé en fichier (non ajouté à la base)."""
        max_bytes = services.settings.max_upload_mb * 1_000_000
        with tempfile.TemporaryDirectory() as tmp:
            path = await _save_upload(file, Path(tmp), max_bytes)
            text = "\n\n".join(doc.page_content for doc in load_file(path))
        return _summarize(text, None, services)


app = create_app()
