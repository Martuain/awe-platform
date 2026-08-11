from fastapi import APIRouter, HTTPException
from app.models import DiscoveryMessageRequest, DiscoveryContext
from app.store import projects, contexts

router = APIRouter(prefix="/business-discovery", tags=["business-discovery"])

@router.post("/start", response_model=DiscoveryContext, status_code=201)
async def start_discovery(project_id: str):
    from uuid import UUID
    pid = UUID(project_id)
    if pid not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    context = DiscoveryContext(project_id=pid)
    contexts[pid] = context
    return context

@router.post("/message", response_model=DiscoveryContext)
async def add_message(request: DiscoveryMessageRequest):
    if request.project_id not in contexts:
        raise HTTPException(status_code=404, detail="Discovery session not found")
    context = contexts[request.project_id]
    context.source_messages.append(request.message)
    return context

@router.get("/context/{project_id}", response_model=DiscoveryContext)
async def get_context(project_id: str):
    from uuid import UUID
    pid = UUID(project_id)
    context = contexts.get(pid)
    if not context:
        raise HTTPException(status_code=404, detail="Discovery context not found")
    return context
