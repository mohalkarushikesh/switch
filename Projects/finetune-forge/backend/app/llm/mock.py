"""A dependency-free, offline provider for local development and tests.

It never touches the network (important on the corp network where model hubs are
blocked) yet behaves enough like a chat model to build and demo the full UI:
it echoes intent, stays deterministic, and honours the system prompt persona.
"""
from __future__ import annotations

import textwrap

from app.llm.base import LLMProvider
from app.schemas import ChatMessage


class MockProvider(LLMProvider):
    name = "mock"

    def __init__(self, system_prompt: str) -> None:
        self._system_prompt = system_prompt

    @property
    def model(self) -> str:
        return "finetune-forge-mock-v1"

    async def generate(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float,
        max_tokens: int,
    ) -> str:
        last_user = next(
            (m.content for m in reversed(messages) if m.role == "user"),
            "",
        )
        turns = sum(1 for m in messages if m.role == "user")
        reply = f"""\
            [mock model] I'm the FineTune Forge stand-in model, so I echo instead
            of reasoning — swap LLM_PROVIDER=azure to use your fine-tuned model.

            You said: "{last_user.strip()}"

            (turn {turns}, temperature={temperature}, max_tokens={max_tokens})"""
        return textwrap.dedent(reply)
