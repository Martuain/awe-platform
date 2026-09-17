from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.models import TeamAcceptInvitationRequest, TeamInvitation, TeamInviteRequest, TeamMember, TeamRole
from app.security import _hash_secret, get_user

router = APIRouter(prefix="/team", tags=["team"])


async def _require_admin(request: Request) -> tuple[object, UUID]:
    user = get_user(request)
    if user.auth_type != "session":
        raise HTTPException(status_code=403, detail="Team administration requires a user session")
    role = await request.app.state.repository.get_team_role(user.tenant_id, user.id)
    if role != TeamRole.ADMIN:
        raise HTTPException(status_code=403, detail="Team administration requires an admin role")
    return user, user.tenant_id


@router.get("/members", response_model=list[TeamMember])
async def list_members(request: Request):
    user = get_user(request)
    if user.auth_type != "session":
        raise HTTPException(status_code=403, detail="Team access requires a user session")
    role = await request.app.state.repository.get_team_role(user.tenant_id, user.id)
    if role is None:
        raise HTTPException(status_code=403, detail="Team access denied")
    return await request.app.state.repository.list_team_members(user.tenant_id)


@router.post("/invitations")
async def create_invitation(body: TeamInviteRequest, request: Request):
    user, tenant_id = await _require_admin(request)
    email = body.email.strip().lower()
    raw = "awei_" + secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    invitation = TeamInvitation(
        tenant_id=tenant_id,
        inviter_id=user.id,
        email=email,
        role=body.role,
        created_at=now,
        expires_at=now + timedelta(days=7),
    )
    await request.app.state.repository.create_team_invitation(invitation, _hash_secret(raw))
    return {
        "id": str(invitation.id),
        "email": invitation.email,
        "role": invitation.role,
        "status": invitation.status,
        "expires_at": invitation.expires_at,
        "invitation_token": raw,
    }


@router.post("/invitations/{invitation_id}/accept", response_model=TeamInvitation)
async def accept_invitation(invitation_id: UUID, body: TeamAcceptInvitationRequest, request: Request):
    user = get_user(request)
    if user.auth_type != "session":
        raise HTTPException(status_code=403, detail="Invitation acceptance requires a user session")
    invitation = await request.app.state.repository.get_team_invitation(invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if invitation.status != "pending":
        raise HTTPException(status_code=409, detail="Invitation is no longer pending")
    if invitation.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Invitation has expired")
    if invitation.email != user.email.strip().lower():
        raise HTTPException(status_code=403, detail="Invitation email does not match authenticated account")
    try:
        return await request.app.state.repository.accept_team_invitation(
            invitation_id, user.id, _hash_secret(body.token), datetime.now(timezone.utc)
        )
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid invitation token")


@router.get("/memberships")
async def list_memberships(request: Request):
    user = get_user(request)
    if user.auth_type != "session":
        raise HTTPException(status_code=403, detail="Team access requires a user session")
    memberships = []
    # The repository exposes tenant-scoped membership lookup; discover memberships
    # through the authenticated user's project-accessible tenants in a bounded way.
    # Current MVP keeps the home tenant explicit and returns it as the canonical membership.
    role = await request.app.state.repository.get_team_role(user.tenant_id, user.id)
    if role:
        memberships.append({"tenant_id": str(user.tenant_id), "role": role})
    return memberships
