from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.services.strategy import WebsiteStrategyService

router = APIRouter(prefix="/website-strategy", tags=["website-strategy"])


def service(request: Request) -> WebsiteStrategyService:
    return WebsiteStrategyService(request.app.state.repository)


@router.post("/generate", response_model=None, status_code=201)
async def generate_strategy(project_id: UUID, request: Request):
    if not await request.app.state.repository.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        return await service(request).generate(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Business Discovery context not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{project_id}")
async def get_strategy(project_id: UUID, request: Request):
    try:
        return await service(request).get(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Website Strategy not found") from None


@router.post("/{project_id}/approve")
async def approve_strategy(project_id: UUID, request: Request):
    try:
        return await service(request).approve(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Website Strategy not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
