import json

import pytest

from app.services.discovery import MockModelGateway
from app.services.model_gateway import (
    ModelGatewayError,
    OpenAICompatibleConfig,
    build_model_gateway,
)


def test_model_gateway_defaults_to_deterministic_mock(monkeypatch):
    monkeypatch.delenv("AWE_MODEL_PROVIDER", raising=False)
    gateway = build_model_gateway(MockModelGateway())
    assert isinstance(gateway, MockModelGateway)


def test_model_gateway_selects_openai_compatible(monkeypatch):
    monkeypatch.setenv("AWE_MODEL_PROVIDER", "openai-compatible")
    monkeypatch.setenv("AWE_MODEL_API_KEY", "test-key")
    gateway = build_model_gateway(MockModelGateway())
    assert gateway.config.api_key == "test-key"
    assert gateway.config.model == "gpt-4o-mini"


def test_model_gateway_rejects_unknown_provider(monkeypatch):
    monkeypatch.setenv("AWE_MODEL_PROVIDER", "unknown")
    with pytest.raises(ModelGatewayError, match="Unsupported"):
        build_model_gateway(MockModelGateway())


def test_model_gateway_requires_api_key(monkeypatch):
    monkeypatch.setenv("AWE_MODEL_PROVIDER", "openai-compatible")
    monkeypatch.delenv("AWE_MODEL_API_KEY", raising=False)
    with pytest.raises(ModelGatewayError, match="API_KEY"):
        build_model_gateway(MockModelGateway())


def test_model_gateway_serializes_chat_completion(monkeypatch):
    monkeypatch.setenv("AWE_MODEL_API_KEY", "test-key")
    monkeypatch.setenv("AWE_MODEL_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("AWE_MODEL_NAME", "test-model")
    config = OpenAICompatibleConfig.from_environment()
    assert config.base_url == "https://example.test/v1"
    assert config.model == "test-model"

    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"choices": [{"message": {"content": '{"industry":"cafe"}'}}]}).encode()

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("app.services.model_gateway.urlopen", fake_urlopen)
    from app.services.model_gateway import OpenAICompatibleModelGateway
    import asyncio

    result = asyncio.run(OpenAICompatibleModelGateway(config).complete({
        "messages": [{"role": "user", "content": "hello"}],
        "temperature": 0,
    }))
    assert result == '{"industry":"cafe"}'
    assert captured["request"].full_url.endswith("/chat/completions")
    assert captured["request"].get_header("Authorization") == "Bearer test-key"
