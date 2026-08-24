import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.store import InMemoryRepository
from app.models import WebsiteGeneration, WebsiteGenerationStatus, GeneratedFile
from app.services.build import WebsiteBuildService
from uuid import uuid4


@pytest.mark.anyio
async def test_build_plan_is_safe_and_does_not_execute_generated_code():
    project_id = uuid4()
    repo = InMemoryRepository()
    await repo.create_generation(WebsiteGeneration(
        project_id=project_id,
        status=WebsiteGenerationStatus.VALIDATED,
        files=[
            GeneratedFile(path="package.json", content='{"scripts":{"build":"next build"},"dependencies":{"next":"15.5.21","react":"19.1.9","react-dom":"19.1.9"}}'),
            GeneratedFile(path="app/page.tsx", content="export default function Page(){return null}"),
        ],
    ))
    app.state.repository = repo
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"/api/v1/website-build/plan?project_id={project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "planned"
    assert data["isolation"] == "sandbox-required"
    assert data["network_access"] == "disabled-by-default"
    assert data["allowed_commands"] == ["next build", "next start"]


@pytest.mark.anyio
async def test_build_plan_rejects_unsupported_dependencies():
    project_id = uuid4()
    repo = InMemoryRepository()
    await repo.create_generation(WebsiteGeneration(
        project_id=project_id,
        status=WebsiteGenerationStatus.VALIDATED,
        files=[
            GeneratedFile(path="package.json", content='{"dependencies":{"evil-package":"1.0.0"}}'),
            GeneratedFile(path="app/page.tsx", content="export default function Page(){return null}"),
        ],
    ))
    plan = await WebsiteBuildService(repo).plan(project_id)
    assert plan.status.value == "rejected"
    assert "Unsupported runtime dependencies" in plan.diagnostics[0]
