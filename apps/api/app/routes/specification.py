from uuid import UUID
from fastapi import APIRouter, HTTPException, Request
from app.services.specification import WebsiteSpecificationService

router = APIRouter(prefix="/website-specification", tags=["website-specification"])

def service(request: Request) -> WebsiteSpecificationService:
    return WebsiteSpecificationService(request.app.state.repository)

@router.post("/generate", status_code=201)
async def generate_specification(project_id: UUID, request: Request):
    try:
        return await service(request).generate(project_id)
    except KeyError as exc:
        detail = "Website Strategy not found" if str(exc).strip("'") == "strategy" else "Brand & Design Direction not found"
        raise HTTPException(status_code=404, detail=detail) from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None

@router.get("/{project_id}")
async def get_specification(project_id: UUID, request: Request):
    try:
        return await service(request).get(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Website Specification not found") from None

@router.post("/{project_id}/approve")
async def approve_specification(project_id: UUID, request: Request):
    try:
        return await service(request).approve(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Website Specification not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
