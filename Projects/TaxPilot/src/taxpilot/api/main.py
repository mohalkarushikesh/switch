"""FastAPI service.

Endpoints mirror the pipeline's two-phase contract: POST /prepare may come back
`awaiting_review`, and POST /resume continues that thread with any corrections.
"""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from taxpilot.certs import enable_system_trust_store
from taxpilot.config import PROJECT_ROOT, get_settings
from taxpilot.graph import pipeline
from taxpilot.intake.loader import classify_doc_type
from taxpilot.models import Correction, DocType, ReturnResponse, SourceDocument
from taxpilot.observability import setup_logging

logger = logging.getLogger(__name__)

#: The single-page web UI, served by this same app at "/".
WEB_DIR = PROJECT_ROOT / "web"


class InlineDocument(BaseModel):
    filename: str
    text: str = Field(min_length=1)
    doc_type: DocType | None = None


class PrepareRequest(BaseModel):
    #: Provide inline documents, or leave empty to read the configured DOCUMENTS_DIR.
    documents: list[InlineDocument] | None = None
    documents_dir: str | None = None
    thread_id: str | None = None
    #: Force a regime, overriding the documents (for "recompute under other regime").
    regime: Literal["auto", "old", "new"] | None = None
    #: Set False to run the pipeline entirely on its deterministic paths (no LLM,
    #: no API key). Defaults to True (use the model where a stage benefits from it).
    use_llm: bool = True


class ResumeRequest(BaseModel):
    thread_id: str
    corrections: list[Correction] = Field(default_factory=list)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)
    enable_system_trust_store()
    logger.info("Starting TaxPilot API (year=%s, model=%s)", settings.tax_year, settings.llm_model)
    pipeline.get_graph()  # compile up front so the first request does not pay for it
    yield
    logger.info("Shutting down API")


app = FastAPI(
    title="TaxPilot",
    version="0.1.0",
    description="Autonomous tax-prep copilot: RAG-grounded deductions, a deterministic "
    "tax engine, audit-risk scoring, a human-review gate and a guardrails layer.",
    lifespan=lifespan,
)

# ---- Web UI (a static single-page app that calls the JSON API below) ----

if WEB_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Serve the web console. The page's JS drives /prepare, /pending and /resume."""
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, Any]:
    from taxpilot.knowledge import get_retriever

    settings = get_settings()
    try:
        rules = get_retriever().count()
    except Exception as exc:
        logger.warning("Knowledge base unavailable: %s", exc)
        rules = -1
    #: Whether an API key is configured for the active provider. The UI uses this
    #: to default the "Use AI" switch and warn when a key is missing.
    key = (
        settings.google_api_key
        if settings.llm_provider == "gemini"
        else settings.anthropic_api_key
    )
    return {
        "status": "ok" if rules > 0 else "degraded",
        "tax_year": settings.tax_year,
        "indexed_rule_passages": rules,
        "model": settings.llm_model,
        "provider": settings.llm_provider,
        "llm_configured": bool(key),
        "features": {
            "rag": settings.enable_rag,
            "audit": settings.enable_audit,
            "review": settings.enable_review,
            "guardrails": settings.enable_guardrails,
        },
    }


@app.post("/prepare", response_model=ReturnResponse)
def prepare(request: PrepareRequest) -> ReturnResponse:
    try:
        documents = _inline_documents(request.documents) if request.documents else None
        return pipeline.prepare(
            documents=documents,
            documents_dir=request.documents_dir,
            thread_id=request.thread_id,
            regime=request.regime,
            use_llm=request.use_llm,
        )
    except Exception as exc:
        logger.exception("Prepare failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/pending/{thread_id}")
def pending(thread_id: str) -> dict[str, Any]:
    payload = pipeline.pending_review(thread_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="nothing awaiting review on that thread")
    return payload


@app.post("/resume", response_model=ReturnResponse)
def resume(request: ResumeRequest) -> ReturnResponse:
    try:
        return pipeline.resume(request.thread_id, corrections=request.corrections)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Resume failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _inline_documents(inline: list[InlineDocument]) -> list[SourceDocument]:
    documents: list[SourceDocument] = []
    for item in inline:
        doc_type = item.doc_type or classify_doc_type(item.text, item.filename)
        documents.append(SourceDocument(
            id=item.filename.rsplit(".", 1)[0] or uuid.uuid4().hex,
            filename=item.filename,
            doc_type=doc_type,
            text=item.text,
        ))
    return documents


def run() -> None:
    """`tax-api` entry point."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "taxpilot.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
