import pytest

from app.services.execution import (
    ExecutionProviderError,
    HostedBuildExecutionProvider,
    LocalDockerBuildExecutionProvider,
    build_execution_provider,
)


def test_local_build_execution_is_default(monkeypatch):
    monkeypatch.delenv("AWE_BUILD_EXECUTION_PROVIDER", raising=False)
    assert isinstance(build_execution_provider(), LocalDockerBuildExecutionProvider)


def test_hosted_build_execution_requires_endpoint(monkeypatch):
    monkeypatch.setenv("AWE_BUILD_EXECUTION_PROVIDER", "hosted")
    monkeypatch.delenv("AWE_BUILD_EXECUTION_URL", raising=False)
    assert isinstance(build_execution_provider(), HostedBuildExecutionProvider)


@pytest.mark.anyio
async def test_hosted_build_execution_reports_missing_endpoint(monkeypatch):
    monkeypatch.delenv("AWE_BUILD_EXECUTION_URL", raising=False)
    with pytest.raises(ExecutionProviderError, match="AWE_BUILD_EXECUTION_URL"):
        await HostedBuildExecutionProvider().execute(None, None, None, None)


def test_unknown_execution_provider_fails_explicitly(monkeypatch):
    monkeypatch.setenv("AWE_BUILD_EXECUTION_PROVIDER", "unknown")
    with pytest.raises(ExecutionProviderError, match="Unsupported"):
        build_execution_provider()
