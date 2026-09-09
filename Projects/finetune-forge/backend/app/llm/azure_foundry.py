"""Provider that calls a fine-tuned model deployed on Azure AI Foundry.

Azure AI Foundry exposes fine-tuned deployments through the Azure OpenAI
data-plane chat-completions API. We call it directly with httpx so the backend
carries no heavyweight SDK — just an endpoint, a deployment name and a key.
"""
from __future__ import annotations

import httpx

from app.llm.base import LLMError, LLMProvider
from app.schemas import ChatMessage


class AzureFoundryProvider(LLMProvider):
    name = "azure"

    def __init__(
        self,
        *,
        endpoint: str,
        deployment: str,
        api_key: str,
        api_version: str,
        system_prompt: str,
    ) -> None:
        missing = [
            label
            for label, value in (
                ("AZURE_FOUNDRY_ENDPOINT", endpoint),
                ("AZURE_FOUNDRY_DEPLOYMENT", deployment),
                ("AZURE_FOUNDRY_API_KEY", api_key),
            )
            if not value
        ]
        if missing:
            raise LLMError(
                "Azure provider selected but missing config: " + ", ".join(missing)
            )

        self._endpoint = endpoint.rstrip("/")
        self._deployment = deployment
        self._api_key = api_key
        self._api_version = api_version
        self._system_prompt = system_prompt

    @property
    def model(self) -> str:
        return self._deployment

    @property
    def _url(self) -> str:
        return (
            f"{self._endpoint}/openai/deployments/{self._deployment}"
            f"/chat/completions?api-version={self._api_version}"
        )

    def _payload_messages(self, messages: list[ChatMessage]) -> list[dict]:
        # Prepend the persona system prompt unless the caller already sent one.
        if messages and messages[0].role == "system":
            return [m.model_dump() for m in messages]
        return [{"role": "system", "content": self._system_prompt}] + [
            m.model_dump() for m in messages
        ]

    async def generate(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float,
        max_tokens: int,
    ) -> str:
        payload = {
            "messages": self._payload_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    self._url,
                    headers={"api-key": self._api_key},
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise LLMError(
                f"Azure Foundry returned {exc.response.status_code}: "
                f"{exc.response.text[:500]}"
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMError(f"Azure Foundry request failed: {exc}") from exc

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Unexpected Azure Foundry response shape: {data}") from exc
