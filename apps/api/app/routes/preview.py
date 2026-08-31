from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, HTTPException, Request
from app.models import WebsitePreview
from app.services.preview import WebsitePreviewService

router = APIRouter(prefix="/website-preview", tags=["website-preview"])


@router.post("/start", response_model=WebsitePreview)
async def start_preview(project_id: UUID, request: Request):
    try:
        return await WebsitePreviewService(request.app.state.repository).start(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Missing artifact: {exc.args[0]}") from exc


@router.post("/stop", response_model=WebsitePreview | None)
async def stop_preview(project_id: UUID, request: Request):
    return await WebsitePreviewService(request.app.state.repository).stop(project_id)
