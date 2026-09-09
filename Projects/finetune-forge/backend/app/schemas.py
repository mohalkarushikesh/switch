"""Request/response models for the chat API."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Role = Literal["system", "user", "assistant"]


class ChatMessage(BaseModel):
    role: Role
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0, le=4096)


class ChatResponse(BaseModel):
    reply: str
    provider: str
    model: str


class HealthResponse(BaseModel):
    status: str
    provider: str
    model: str
