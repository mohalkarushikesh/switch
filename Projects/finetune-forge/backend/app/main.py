"""FastAPI application entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import chat

settings = get_settings()

app = FastAPI(
    title="FineTune Forge API",
    version="1.0.0",
    description="Serves a fine-tuned LLM to the FineTune Forge web app.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "finetune-forge-api", "docs": "/docs"}
