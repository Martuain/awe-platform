import pytest
from uuid import uuid4
from app.models import WebsiteExecutionState, WebsiteValidation, WebsiteValidationStatus, WebsitePreview, WebsitePreviewStatus
from app.store import InMemoryRepository

@pytest.mark.anyio
async def test_execution_state_survives_repository_reload_in_memory_contract():
    project_id = uuid4()
    repo = InMemoryRepository()
    validation = WebsiteValidation(project_id=project_id, generation_version=3, status=WebsiteValidationStatus.PASSED)
    preview = WebsitePreview(project_id=project_id, generation_version=3, status=WebsitePreviewStatus.STARTED, url="http://127.0.0.1:1234")
    await repo.save_execution_state(WebsiteExecutionState(project_id=project_id, generation_version=3, build_status="succeeded", build_result={"status":"succeeded"}, validation_status="passed", validation=validation, preview_status="started", preview=preview))
    restored = await repo.get_execution_state(project_id)
    assert restored is not None
    assert restored.build_status == "succeeded"
    assert restored.validation_status == "passed"
    assert restored.validation is not None and restored.validation.generation_version == 3
    assert restored.preview_status == "started"
    assert restored.preview is not None and restored.preview.url.endswith(":1234")
