from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.models import WebsiteMockFeedbackRequest
from app.services.mock import WebsiteMockService

router = APIRouter(prefix="/website-mock", tags=["website-mock"])


def service(request: Request) -> WebsiteMockService:
    return WebsiteMockService(request.app.state.repository)


@router.post("/create", status_code=201)
async def create_mock(project_id: UUID, request: Request):
    try:
        return await service(request).create(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Website Generation not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{project_id}")
async def get_mock(project_id: UUID, request: Request):
    try:
        return await service(request).get(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Website Mock not found") from None


@router.post("/{project_id}/feedback")
async def feedback(project_id: UUID, body: WebsiteMockFeedbackRequest, request: Request):
    try:
        return await service(request).feedback(project_id, body.feedback)
    except KeyError:
        raise HTTPException(status_code=404, detail="Website Mock not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{project_id}/revise", status_code=201)
async def revise(project_id: UUID, body: WebsiteMockFeedbackRequest, request: Request):
    try:
        return await service(request).revise(project_id, body.feedback)
    except KeyError:
        raise HTTPException(status_code=404, detail="Website Mock not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{project_id}/approve")
async def approve(project_id: UUID, request: Request):
    try:
        return await service(request).approve(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Website Mock not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
