from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.services.validation import WebsiteValidationService

router = APIRouter(prefix="/website-validation", tags=["website-validation"])


def service(request: Request) -> WebsiteValidationService:
    return WebsiteValidationService(request.app.state.repository)


@router.post("/validate", status_code=201)
async def validate_website(project_id: UUID, request: Request):
    try:
        return await service(request).validate(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Website Generation not found") from None
