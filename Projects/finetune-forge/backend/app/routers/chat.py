"""Chat + health endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.llm.base import LLMError, LLMProvider
from app.llm.factory import get_provider
from app.schemas import ChatRequest, ChatResponse, HealthResponse

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/health", response_model=HealthResponse)
async def health(provider: LLMProvider = Depends(get_provider)) -> HealthResponse:
    return HealthResponse(status="ok", provider=provider.name, model=provider.model)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    provider: LLMProvider = Depends(get_provider),
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    temperature = (
        request.temperature
        if request.temperature is not None
        else settings.llm_temperature
    )
    max_tokens = (
        request.max_tokens if request.max_tokens is not None else settings.llm_max_tokens
    )
    try:
        reply = await provider.generate(
            request.messages, temperature=temperature, max_tokens=max_tokens
        )
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ChatResponse(reply=reply, provider=provider.name, model=provider.model)
