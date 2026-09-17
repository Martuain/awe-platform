from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID

from app.models import WebsiteGeneration, WebsiteBuildPlan


class ExecutionProviderError(RuntimeError):
    pass


class BuildExecutionProvider(ABC):
    name = "base"

    @abstractmethod
    async def execute(self, project_id: UUID, generation: WebsiteGeneration, plan: WebsiteBuildPlan, service: Any, install_timeout_seconds: int = 300, build_timeout_seconds: int = 180) -> dict[str, Any]:
        raise NotImplementedError


class LocalDockerBuildExecutionProvider(BuildExecutionProvider):
    name = "local-docker"

    async def execute(self, project_id: UUID, generation: WebsiteGeneration, plan: WebsiteBuildPlan, service: Any, install_timeout_seconds: int = 300, build_timeout_seconds: int = 180) -> dict[str, Any]:
        # Delegate to the existing hardened local implementation without introducing
        # another sandbox implementation or changing its security contract.
        return await service._execute_local_docker(project_id, install_timeout_seconds=install_timeout_seconds, build_timeout_seconds=build_timeout_seconds)


class HostedBuildExecutionProvider(BuildExecutionProvider):
    name = "hosted"

    async def execute(self, project_id: UUID, generation: WebsiteGeneration, plan: WebsiteBuildPlan, service: Any, install_timeout_seconds: int = 300, build_timeout_seconds: int = 180) -> dict[str, Any]:
        endpoint = os.getenv("AWE_BUILD_EXECUTION_URL", "").strip()
        token = os.getenv("AWE_BUILD_EXECUTION_TOKEN", "").strip()
        if not endpoint:
            raise ExecutionProviderError("AWE_BUILD_EXECUTION_URL is required for hosted build execution")
        payload = {"project_id": str(project_id), "generation": generation.model_dump(mode="json"), "plan": plan.model_dump(mode="json")}
        request = Request(endpoint.rstrip("/") + "/execute", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})}, method="POST")
        try:
            with urlopen(request, timeout=float(os.getenv("AWE_BUILD_EXECUTION_TIMEOUT_SECONDS", "600"))) as response:
                body = response.read().decode()
                if response.status >= 400:
                    raise ExecutionProviderError(f"Hosted build execution returned HTTP {response.status}")
                result = json.loads(body)
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            raise ExecutionProviderError(f"Hosted build execution failed: {exc}") from exc
        if not isinstance(result, dict) or "status" not in result:
            raise ExecutionProviderError("Hosted build execution returned an invalid response")
        result["execution_provider"] = self.name
        return result


def build_execution_provider() -> BuildExecutionProvider:
    mode = os.getenv("AWE_BUILD_EXECUTION_PROVIDER", "local-docker").strip().lower()
    if mode in {"local", "local-docker", "docker"}:
        return LocalDockerBuildExecutionProvider()
    if mode == "hosted":
        return HostedBuildExecutionProvider()
    raise ExecutionProviderError(f"Unsupported AWE_BUILD_EXECUTION_PROVIDER: {mode}")
