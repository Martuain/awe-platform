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


@router.api_route("/live-proxy/{project_id}/{path:path}", methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_stable_live(project_id: UUID, path: str, request: Request):
    """Proxy the canonical live deployment behind a stable project URL.

    The runtime host/port is deliberately not exposed here. The service resolves
    the durable CURRENT deployment and rewrites generated links into the stable
    deployment-aware Studio namespace.
    """
    try:
        return await WebsitePreviewService(request.app.state.repository).proxy_deployment_request(
            project_id,
            request,
            request_prefix=f"/api/v1/website-preview/live-proxy/{project_id}",
            public_prefix=f"/api/live/{project_id}",
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Live deployment runtime is unreachable: {exc}") from exc


@router.api_route("/deployment-proxy/{project_id}/{path:path}", methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_deployment(project_id: UUID, path: str, request: Request):
    try:
        return await WebsitePreviewService(request.app.state.repository).proxy_deployment_request(project_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Latest deployment runtime is unreachable: {exc}") from exc


@router.post("/refresh", response_model=WebsitePreview)
async def refresh_preview(project_id: UUID, request: Request):
    try:
        return await WebsitePreviewService(request.app.state.repository).refresh_published_content(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Live preview refresh failed: {exc}") from exc


@router.api_route("/preview-proxy/{project_id}/{path:path}", methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_project_preview(project_id: UUID, path: str, request: Request):
    try:
        return await WebsitePreviewService(request.app.state.repository).proxy_preview_project_request(project_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Live preview runtime is unreachable: {exc}") from exc

@router.api_route("/proxy/{port}/{path:path}", methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_preview(port: int, path: str, request: Request):
    try:
        return await WebsitePreviewService(request.app.state.repository).proxy_request(port, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Live preview runtime is unreachable: {exc}") from exc
