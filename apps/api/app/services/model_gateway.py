from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ModelGatewayError(RuntimeError):
    """Raised when a configured production model provider cannot complete."""


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float = 60.0

    @classmethod
    def from_environment(cls) -> "OpenAICompatibleConfig":
        base_url = os.getenv("AWE_MODEL_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        api_key = os.getenv("AWE_MODEL_API_KEY", "").strip()
        model = os.getenv("AWE_MODEL_NAME", "gpt-4o-mini").strip()
        try:
            timeout = float(os.getenv("AWE_MODEL_TIMEOUT_SECONDS", "60"))
        except ValueError as exc:
            raise ModelGatewayError("AWE_MODEL_TIMEOUT_SECONDS must be numeric") from exc
        if timeout <= 0:
            raise ModelGatewayError("AWE_MODEL_TIMEOUT_SECONDS must be greater than zero")
        if not api_key:
            raise ModelGatewayError("AWE_MODEL_API_KEY is required for the production model gateway")
        if not model:
            raise ModelGatewayError("AWE_MODEL_NAME must not be empty")
        return cls(base_url=base_url, api_key=api_key, model=model, timeout_seconds=timeout)


class OpenAICompatibleModelGateway:
    """Provider-neutral gateway for OpenAI-compatible chat-completions APIs.

    The adapter deliberately speaks HTTP directly so the AWE API does not become
    coupled to a provider SDK. Providers can be selected through a base URL and
    model name while the capability continues to depend only on ``complete``.
    """

    def __init__(self, config: OpenAICompatibleConfig | None = None) -> None:
        self.config = config or OpenAICompatibleConfig.from_environment()

    async def complete(self, request: dict) -> str:
        return await asyncio.to_thread(self._complete_sync, request)

    def _complete_sync(self, request: dict) -> str:
        payload = {
            "model": self.config.model,
            "messages": request["messages"],
        }
        if request.get("temperature") is not None:
            payload["temperature"] = request["temperature"]

        body = json.dumps(payload).encode("utf-8")
        http_request = Request(
            f"{self.config.base_url}/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(http_request, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise ModelGatewayError(f"Model provider returned HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError) as exc:
            raise ModelGatewayError(f"Model provider request failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise ModelGatewayError("Model provider returned invalid JSON") from exc

        try:
            content = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelGatewayError("Model provider response did not contain message content") from exc
        if not isinstance(content, str) or not content.strip():
            raise ModelGatewayError("Model provider returned empty message content")
        return content


def build_model_gateway(mock_gateway, *, environment: str | None = None):
    """Select the deterministic mock by default and production HTTP only when enabled."""
    mode = (environment or os.getenv("AWE_MODEL_PROVIDER", "mock")).strip().lower()
    if mode in {"", "mock", "deterministic"}:
        return mock_gateway
    if mode in {"openai-compatible", "openai_compatible", "openai"}:
        return OpenAICompatibleModelGateway()
    raise ModelGatewayError(f"Unsupported AWE_MODEL_PROVIDER: {mode}")
