from __future__ import annotations

import hmac
import os
from uuid import UUID

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.security import authenticate, require_scope


class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        internal_preview_secret = os.getenv("AWE_INTERNAL_PREVIEW_SECRET", "dev-preview-proxy")
        if (path.startswith("/api/v1/website-preview/proxy/") or path.startswith("/api/v1/website-preview/deployment-proxy/") or path.startswith("/api/v1/website-preview/live-proxy/")) and hmac.compare_digest(request.headers.get("X-AWE-Preview-Proxy", ""), internal_preview_secret):
            return await call_next(request)
        if (
            path == "/api/v1/health"
            or path.startswith("/api/v1/auth/register")
            or path.startswith("/api/v1/auth/login")
            or path.startswith("/api/v1/auth/verify-email/request")
            or path.startswith("/api/v1/auth/verify-email/confirm")
            or path.startswith("/api/v1/auth/password-reset/request")
            or path.startswith("/api/v1/auth/password-reset/confirm")
            or path.startswith("/api/v1/auth/sso/oidc/start")
            or path.startswith("/api/v1/auth/sso/oidc/callback")
        ):
            return await call_next(request)
        try:
            request.state.user = await authenticate(request)
            self._require_scope(request)
            await self._authorize_resource(request)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)
        return await call_next(request)


    def _require_scope(self, request: Request) -> None:
        path = request.url.path
        if path.startswith("/api/v1/projects"):
            require_scope(request, "project:write" if request.method in {"POST", "PATCH", "DELETE"} else "project:read")
        elif path.startswith("/api/v1/deployments"):
            require_scope(request, "deployment:write" if request.method == "POST" else "project:read")
        elif path.startswith("/api/v1/generation") or path.startswith("/api/v1/website-generation"):
            require_scope(request, "generation:write" if request.method == "POST" else "project:read")
        elif path.startswith("/api/v1/monitoring") or path.startswith("/api/v1/website-performance"):
            require_scope(request, "project:read")
        elif path.startswith("/api/v1/website-content"):
            require_scope(request, "project:write" if request.method in {"POST", "PUT", "PATCH", "DELETE"} else "project:read")
        elif path.startswith("/api/v1/business-discovery") or path.startswith("/api/v1/strategy") or path.startswith("/api/v1/design") or path.startswith("/api/v1/specification") or path.startswith("/api/v1/website-build") or path.startswith("/api/v1/website-validation") or path.startswith("/api/v1/website-preview"):
            require_scope(request, "project:write" if request.method == "POST" else "project:read")

    async def _authorize_resource(self, request: Request) -> None:
        path = request.url.path
        project_id = None

        if path.startswith("/api/v1/projects/"):
            parts = path.split("/")
            if len(parts) >= 5:
                try:
                    project_id = UUID(parts[4])
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid project_id")

        elif path.startswith("/api/v1/website-content/"):
            parts = path.split("/")
            if len(parts) >= 5:
                try:
                    project_id = UUID(parts[4])
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid project_id")

        elif path.startswith("/api/v1/"):
            value = request.query_params.get("project_id")
            if value:
                try:
                    project_id = UUID(value)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid project_id")

            if path.startswith("/api/v1/deployments/") and not path.endswith("/stop"):
                parts = path.split("/")
                if len(parts) >= 5:
                    try:
                        deployment_id = UUID(parts[4])
                    except ValueError:
                        deployment_id = None

                    if deployment_id:
                        deployment = await request.app.state.repository.get_deployment(
                            deployment_id
                        )
                        if not deployment:
                            raise HTTPException(
                                status_code=404,
                                detail="Deployment not found",
                            )
                        project_id = deployment.project_id

            elif path.startswith("/api/v1/deployments/") and path.endswith("/stop"):
                parts = path.split("/")
                try:
                    deployment_id = UUID(parts[4])
                except (ValueError, IndexError):
                    deployment_id = None

                if deployment_id:
                    deployment = await request.app.state.repository.get_deployment(
                        deployment_id
                    )
                    if not deployment:
                        raise HTTPException(
                            status_code=404,
                            detail="Deployment not found",
                        )
                    project_id = deployment.project_id

        if project_id is None:
            return

        project = await request.app.state.repository.get_project(project_id)
        if not project:
            return

        user = request.state.user
        if not await request.app.state.repository.can_access_project(
            project_id,
            user.id,
            user.tenant_id,
        ):
            raise HTTPException(status_code=403, detail="Project access denied")
