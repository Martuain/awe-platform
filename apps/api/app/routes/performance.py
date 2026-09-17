from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.services.browser_validation import BrowserValidationService

router = APIRouter(prefix="/website-performance", tags=["website-performance"])


@router.post("/check")
async def performance_check(project_id: UUID, request: Request):
    generation = await request.app.state.repository.get_generation(project_id)
    if not generation:
        raise HTTPException(status_code=404, detail="Website Generation not found")

    files = generation.files
    total_bytes = sum(len(item.content.encode("utf-8")) for item in files)
    js_bytes = sum(len(item.content.encode("utf-8")) for item in files if item.path.endswith((".js", ".tsx", ".ts")))
    css_bytes = sum(len(item.content.encode("utf-8")) for item in files if item.path.endswith((".css", ".scss")))
    html_files = [item for item in files if item.path.endswith((".html", ".tsx"))]
    checks = [
        {"name": "Generated artifact exists", "status": "passed", "detail": f"{len(files)} files"},
        {"name": "Artifact size", "status": "passed" if total_bytes <= 500_000 else "warning", "detail": f"{total_bytes} bytes"},
        {"name": "JavaScript source budget", "status": "passed" if js_bytes <= 250_000 else "warning", "detail": f"{js_bytes} bytes"},
        {"name": "CSS source budget", "status": "passed" if css_bytes <= 100_000 else "warning", "detail": f"{css_bytes} bytes"},
        {"name": "Page entry points", "status": "passed" if html_files else "warning", "detail": f"{len(html_files)} candidate page files"},
    ]
    return {
        "project_id": str(project_id),
        "generation_version": generation.version,
        "status": "passed" if all(item["status"] == "passed" for item in checks) else "warning",
        "total_bytes": total_bytes,
        "javascript_bytes": js_bytes,
        "css_bytes": css_bytes,
        "checks": checks,
    }


@router.post("/browser-check")
async def browser_performance_check(project_id: UUID, request: Request):
    try:
        return await BrowserValidationService(request.app.state.repository).check(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Website Generation not found") from None
