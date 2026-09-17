from uuid import UUID
from fastapi import APIRouter, Request
from app.models import WebsiteContentItem, WebsiteContentStatus, WebsiteContentUpsertRequest
from app.services.preview import WebsitePreviewService

router = APIRouter(prefix="/website-content", tags=["website-content"])

@router.get("/{project_id}")
async def list_content(project_id: UUID, request: Request, status: WebsiteContentStatus | None = None):
    return await request.app.state.repository.list_content(project_id, status)

@router.put("/{project_id}")
async def upsert_content(project_id: UUID, body: WebsiteContentUpsertRequest, request: Request):
    item = WebsiteContentItem(project_id=project_id, **body.model_dump())
    return await request.app.state.repository.upsert_content(item)

@router.post("/{project_id}/publish")
async def publish_content(project_id: UUID, request: Request):
    published = await request.app.state.repository.publish_content(project_id)
    # Publishing is the authoritative content boundary. Refresh the optional
    # Preview runtime when a generated site exists, but never make content
    # publication depend on disposable runtime availability.
    try:
        await WebsitePreviewService(request.app.state.repository).refresh_published_content(project_id)
    except KeyError as exc:
        # A project may legitimately have editable/publishable content before
        # its first website generation exists. In that state there is no Preview
        # runtime to refresh, but the content publication itself remains valid.
        if exc.args != ("generation",):
            raise

    # Content publication is authoritative and must not be rolled back merely
    # because the optional disposable Preview runtime is unavailable or needs
    # rebuilding. The preview service persists its own status/diagnostics so the
    # UI can surface that condition independently.
    return published

@router.get("/{project_id}/{content_id}/versions")
async def content_versions(project_id: UUID, content_id: UUID, request: Request):
    return await request.app.state.repository.list_content_versions(project_id, content_id)
