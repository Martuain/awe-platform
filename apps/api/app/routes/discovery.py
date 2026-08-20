from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.models import DiscoveryApprovalResponse, DiscoveryMessageRequest, DiscoveryContext
from app.services.discovery import DiscoveryService

router = APIRouter(prefix="/business-discovery", tags=["business-discovery"])


def service(request: Request) -> DiscoveryService:
    return DiscoveryService(request.app.state.repository)


@router.post("/start", response_model=DiscoveryContext, status_code=201)
async def start_discovery(project_id: UUID, request: Request):
    if not await request.app.state.repository.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return await service(request).start(project_id)


@router.post("/message", response_model=DiscoveryContext)
async def add_message(payload: DiscoveryMessageRequest, request: Request):
    if not await request.app.state.repository.get_context(payload.project_id):
        raise HTTPException(status_code=404, detail="Discovery session not found")
    try:
        return await service(request).message(payload.project_id, payload.message)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/context/{project_id}", response_model=DiscoveryContext)
async def get_context(project_id: UUID, request: Request):
    context = await request.app.state.repository.get_context(project_id)
    if not context:
        raise HTTPException(status_code=404, detail="Discovery context not found")
    return context


@router.post("/approve/{project_id}", response_model=DiscoveryApprovalResponse)
async def approve(project_id: UUID, request: Request):
    try:
        context = await service(request).approve(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Discovery context not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"context": context}
