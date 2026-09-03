from fastapi import APIRouter

router = APIRouter(tags=["system"])

@router.get("/health")
async def health():
    return {"status": "ok", "service": "awe-api", "version": "1.0.2"}
