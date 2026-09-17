from uuid import UUID
from fastapi import APIRouter, HTTPException, Request

from app.models import WebsiteMockFeedbackRequest
from app.services.generation import WebsiteGenerationService

router = APIRouter(prefix="/website-generation", tags=["website-generation"])

def service(request: Request) -> WebsiteGenerationService:
    return WebsiteGenerationService(request.app.state.repository)

@router.post("/generate", status_code=201)
async def generate_website(project_id: UUID, request: Request):
    try:
        return await service(request).generate(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Website Specification not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None

@router.post("/{project_id}/revise", status_code=201)
async def revise_generation(project_id: UUID, body: WebsiteMockFeedbackRequest, request: Request):
    try:
        return await service(request).revise(project_id, body.feedback)
    except KeyError:
        raise HTTPException(status_code=404, detail="Website Generation not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/{project_id}")
async def get_generation(project_id: UUID, request: Request):
    try:
        return await service(request).get(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Website Generation not found") from None
