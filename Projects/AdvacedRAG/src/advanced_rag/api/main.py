"""FastAPI service.

Endpoints mirror the pipeline's two-phase contract: POST /ask may come back
`awaiting_approval`, and POST /approve resumes that thread.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from advanced_rag.certs import enable_system_trust_store
from advanced_rag.config import get_settings
from advanced_rag.graph import pipeline
from advanced_rag.models import AnswerResponse
from advanced_rag.observability import setup_logging

logger = logging.getLogger(__name__)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4_000)
    thread_id: str | None = None


class ApproveRequest(BaseModel):
    thread_id: str
    approved: bool


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int | None = None
    mode: str = Field("hybrid", pattern="^(dense|sparse|hybrid)$")
    fusion: str = Field("weighted", pattern="^(weighted|rrf)$")
    use_hyde: bool = False
    rerank: bool = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)
    enable_system_trust_store()
    logger.info("Starting API (model=%s)", settings.llm_model)
    # Compile the graph up front so the first request does not pay for it.
    pipeline.get_graph()
    yield
    logger.info("Shutting down API")


app = FastAPI(
    title="Kubernetes SRE Copilot",
    version="0.1.0",
    description="Enterprise Advanced RAG: hybrid search, reranking, HyDE, CRAG, "
    "Self-RAG, Text2SQL with approval, caching and guardrails.",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, Any]:
    from advanced_rag.retrieval import get_store

    settings = get_settings()
    try:
        indexed = get_store().count()
    except Exception as exc:
        logger.warning("Vector store unreachable: %s", exc)
        indexed = -1
    return {
        "status": "ok" if indexed > 0 else "degraded",
        "indexed_chunks": indexed,
        "model": settings.llm_model,
        "vector_store": settings.qdrant_url or f"embedded:{settings.qdrant_path}",
        "sql_dialect": settings.sql_dialect,
        "cache": "redis" if settings.redis_url else "in-process",
        "features": {
            "hyde": settings.enable_hyde,
            "crag": settings.enable_crag,
            "self_rag": settings.enable_self_rag,
            "text2sql": settings.enable_text2sql,
            "guardrails": settings.enable_guardrails,
            "cache": settings.enable_cache,
        },
    }


@app.post("/ask", response_model=AnswerResponse)
def ask(request: AskRequest) -> AnswerResponse:
    try:
        return pipeline.ask(request.question, thread_id=request.thread_id)
    except Exception as exc:
        logger.exception("Request failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/approve", response_model=AnswerResponse)
def approve(request: ApproveRequest) -> AnswerResponse:
    try:
        return pipeline.resume(request.thread_id, approved=request.approved)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Resume failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/pending/{thread_id}")
def pending(thread_id: str) -> dict[str, Any]:
    payload = pipeline.pending_approval(thread_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="nothing awaiting approval on that thread")
    return payload


@app.post("/retrieve")
def retrieve(request: RetrieveRequest) -> dict[str, Any]:
    """Retrieval without generation - for tuning and for the UI's compare view."""
    from advanced_rag.retrieval import get_retriever

    result = get_retriever().retrieve(
        request.query,
        use_hyde=request.use_hyde,
        rerank=request.rerank,
        mode=request.mode,
        fusion=request.fusion,
        top_k=request.top_k,
    )
    return {
        "query": request.query,
        "hyde_document": result.hyde_document,
        "reranked": result.reranked,
        "results": [
            {
                "source": hit.chunk.source,
                "section": hit.chunk.section,
                "retrieval_score": round(hit.retrieval_score, 4),
                "rerank_score": None if hit.rerank_score is None else round(hit.rerank_score, 4),
                "text": hit.chunk.text,
            }
            for hit in result.chunks
        ],
    }


@app.post("/cache/clear")
def clear_cache() -> dict[str, str]:
    from advanced_rag.cache import get_cache

    get_cache().clear()
    return {"status": "cleared"}


def run() -> None:
    """`rag-api` entry point."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "advanced_rag.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
