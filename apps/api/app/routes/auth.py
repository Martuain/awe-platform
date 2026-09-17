from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.security import ApiKeyRow, AuthTokenRow, SSOIdentityRow, SSOStateRow, UserRow, auth_mode, create_session, get_user, _hash_secret, _password_hash, _verify_password
from app.models import TeamMember, TeamRole
from app.services.sso import authorization_url, exchange_code, hash_state, issue_state, sso_mode

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=200)


class LoginRequest(RegisterRequest):
    pass


class VerifyEmailRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class ConfirmTokenRequest(BaseModel):
    token: str = Field(min_length=20, max_length=500)


class PasswordResetConfirmRequest(ConfirmTokenRequest):
    password: str = Field(min_length=12, max_length=200)


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    scopes: list[str] = Field(default_factory=lambda: ["project:read", "project:write", "generation:write", "deployment:write"])


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, request: Request):
    if auth_mode() != "strict":
        raise HTTPException(status_code=409, detail="Registration is available only in strict authentication mode")
    session_factory = getattr(request.app.state.repository, "session_factory", None)
    if session_factory is None:
        raise HTTPException(status_code=503, detail="Persistent authentication storage is unavailable")
    email = body.email.strip().lower()
    async with session_factory() as session:
        existing = await session.execute(select(UserRow).where(UserRow.email == email))
        if existing.scalars().first():
            raise HTTPException(status_code=409, detail="Account already exists")
        user = UserRow(id=str(uuid4()), email=email, password_hash=_password_hash(body.password), tenant_id=str(uuid4()), created_at=datetime.now(timezone.utc), email_verified=False)
        session.add(user)
        await session.commit()
        await request.app.state.repository.add_team_member(TeamMember(user_id=UUID(user.id), tenant_id=UUID(user.tenant_id), role=TeamRole.ADMIN))
        token, expires = await create_session(session_factory, user)
    return {"access_token": token, "token_type": "bearer", "expires_at": expires}


@router.post("/login")
async def login(body: LoginRequest, request: Request):
    if auth_mode() != "strict":
        raise HTTPException(status_code=409, detail="Login is available only in strict authentication mode")
    session_factory = getattr(request.app.state.repository, "session_factory", None)
    if session_factory is None:
        raise HTTPException(status_code=503, detail="Persistent authentication storage is unavailable")
    async with session_factory() as session:
        result = await session.execute(select(UserRow).where(UserRow.email == body.email.strip().lower()))
        user = result.scalars().first()
        if not user or not _verify_password(body.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
    token, expires = await create_session(session_factory, user)
    return {"access_token": token, "token_type": "bearer", "expires_at": expires}


@router.get("/me")
async def me(request: Request):
    user = get_user(request)
    return {"id": str(user.id), "tenant_id": str(user.tenant_id), "email": user.email, "auth_type": user.auth_type}



def _expose_auth_tokens() -> bool:
    return os.getenv("AWE_AUTH_EXPOSE_TEST_TOKENS", "false").strip().lower() == "true"


async def _issue_auth_token(session_factory, user_id: str, purpose: str, ttl_hours: int) -> str:
    raw = secrets.token_urlsafe(48)
    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        session.add(AuthTokenRow(id=str(uuid4()), user_id=user_id, token_hash=_hash_secret(raw), purpose=purpose, expires_at=now + timedelta(hours=ttl_hours), created_at=now))
        await session.commit()
    return raw


@router.post("/verify-email/request", status_code=202)
async def request_email_verification(body: VerifyEmailRequest, request: Request):
    if auth_mode() != "strict":
        raise HTTPException(status_code=409, detail="Email verification is available only in strict authentication mode")
    factory = getattr(request.app.state.repository, "session_factory", None)
    if factory is None:
        raise HTTPException(status_code=503, detail="Persistent authentication storage is unavailable")
    async with factory() as session:
        result = await session.execute(select(UserRow).where(UserRow.email == body.email.strip().lower()))
        user = result.scalars().first()
    response = {"accepted": True}
    if user and not user.email_verified:
        token = await _issue_auth_token(factory, user.id, "email_verification", 24)
        if _expose_auth_tokens():
            response["verification_token"] = token
    return response


@router.post("/verify-email/confirm")
async def confirm_email_verification(body: ConfirmTokenRequest, request: Request):
    factory = getattr(request.app.state.repository, "session_factory", None)
    if factory is None:
        raise HTTPException(status_code=503, detail="Persistent authentication storage is unavailable")
    async with factory() as session:
        result = await session.execute(select(AuthTokenRow).where(AuthTokenRow.token_hash == _hash_secret(body.token), AuthTokenRow.purpose == "email_verification", AuthTokenRow.used_at.is_(None)))
        token = result.scalars().first()
        if not token or token.expires_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Invalid or expired verification token")
        user = await session.get(UserRow, token.user_id)
        if not user:
            raise HTTPException(status_code=400, detail="Invalid verification token")
        user.email_verified = True
        token.used_at = datetime.now(timezone.utc)
        await session.commit()
    return {"verified": True}


@router.post("/password-reset/request", status_code=202)
async def request_password_reset(body: VerifyEmailRequest, request: Request):
    if auth_mode() != "strict":
        raise HTTPException(status_code=409, detail="Password recovery is available only in strict authentication mode")
    factory = getattr(request.app.state.repository, "session_factory", None)
    if factory is None:
        raise HTTPException(status_code=503, detail="Persistent authentication storage is unavailable")
    async with factory() as session:
        result = await session.execute(select(UserRow).where(UserRow.email == body.email.strip().lower()))
        user = result.scalars().first()
    response = {"accepted": True}
    if user:
        token = await _issue_auth_token(factory, user.id, "password_reset", 1)
        if _expose_auth_tokens():
            response["reset_token"] = token
    return response


@router.post("/password-reset/confirm")
async def confirm_password_reset(body: PasswordResetConfirmRequest, request: Request):
    factory = getattr(request.app.state.repository, "session_factory", None)
    if factory is None:
        raise HTTPException(status_code=503, detail="Persistent authentication storage is unavailable")
    async with factory() as session:
        result = await session.execute(select(AuthTokenRow).where(AuthTokenRow.token_hash == _hash_secret(body.token), AuthTokenRow.purpose == "password_reset", AuthTokenRow.used_at.is_(None)))
        token = result.scalars().first()
        if not token or token.expires_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        user = await session.get(UserRow, token.user_id)
        if not user:
            raise HTTPException(status_code=400, detail="Invalid reset token")
        user.password_hash = _password_hash(body.password)
        token.used_at = datetime.now(timezone.utc)
        await session.commit()
    return {"password_reset": True}

@router.get("/sso/oidc/start")
async def sso_oidc_start(request: Request):
    if sso_mode() not in {"mock", "oidc"}:
        raise HTTPException(status_code=404, detail="External SSO is not enabled")
    factory = getattr(request.app.state.repository, "session_factory", None)
    if factory is None:
        raise HTTPException(status_code=503, detail="Persistent authentication storage is unavailable")
    state, nonce, expires = issue_state()
    now = datetime.now(timezone.utc)
    async with factory() as session:
        session.add(SSOStateRow(id=str(uuid4()), state_hash=hash_state(state), nonce=nonce, provider="oidc", expires_at=expires, created_at=now))
        await session.commit()
    try:
        url = await authorization_url(state, nonce)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="SSO provider configuration unavailable") from exc
    return RedirectResponse(url=url, status_code=302)


@router.get("/sso/oidc/callback")
async def sso_oidc_callback(state: str, code: str, request: Request):
    if sso_mode() not in {"mock", "oidc"}:
        raise HTTPException(status_code=404, detail="External SSO is not enabled")
    factory = getattr(request.app.state.repository, "session_factory", None)
    if factory is None:
        raise HTTPException(status_code=503, detail="Persistent authentication storage is unavailable")
    now = datetime.now(timezone.utc)
    async with factory() as session:
        result = await session.execute(select(SSOStateRow).where(SSOStateRow.state_hash == hash_state(state), SSOStateRow.provider == "oidc", SSOStateRow.used_at.is_(None)))
        state_row = result.scalars().first()
        if not state_row or state_row.expires_at <= now:
            raise HTTPException(status_code=400, detail="Invalid or expired SSO state")
        try:
            identity = await exchange_code(code, state_row.nonce)
        except Exception as exc:
            raise HTTPException(status_code=401, detail="External identity verification failed") from exc
        state_row.used_at = now
        identity_result = await session.execute(select(SSOIdentityRow).where(SSOIdentityRow.provider == "oidc", SSOIdentityRow.subject == identity.subject))
        identity_row = identity_result.scalars().first()
        user = None
        if identity_row:
            user = await session.get(UserRow, identity_row.user_id)
        if user is None:
            email_result = await session.execute(select(UserRow).where(UserRow.email == identity.email))
            user = email_result.scalars().first()
        if user is None:
            if not identity.email_verified or os.getenv("AWE_SSO_AUTO_PROVISION", "false").strip().lower() != "true":
                raise HTTPException(status_code=403, detail="External account is not linked to an AWE account")
            user = UserRow(id=str(uuid4()), email=identity.email, password_hash=_password_hash(secrets.token_urlsafe(32)), tenant_id=str(uuid4()), created_at=now, email_verified=True)
            session.add(user)
            await session.flush()
            await request.app.state.repository.add_team_member(TeamMember(user_id=UUID(user.id), tenant_id=UUID(user.tenant_id), role=TeamRole.ADMIN))
        elif not identity.email_verified and not user.email_verified:
            raise HTTPException(status_code=403, detail="External identity email is not verified")
        if identity_row is None:
            session.add(SSOIdentityRow(id=str(uuid4()), user_id=user.id, provider="oidc", subject=identity.subject, email=identity.email, created_at=now))
        await session.commit()
    token, expires = await create_session(factory, user)
    return {"access_token": token, "token_type": "bearer", "expires_at": expires, "auth_type": "session", "provider": "oidc"}


@router.post("/api-keys")
async def create_api_key(body: ApiKeyCreateRequest, request: Request):
    user = get_user(request)
    if user.auth_type != "session":
        raise HTTPException(status_code=403, detail="API key administration requires a user session")
    session_factory = getattr(request.app.state.repository, "session_factory", None)
    raw = "awe_" + uuid4().hex + secrets.token_urlsafe(24)
    async with session_factory() as session:
        row = ApiKeyRow(id=str(uuid4()), user_id=str(user.id), tenant_id=str(user.tenant_id), name=body.name, key_prefix=raw[:12], key_hash=_hash_secret(raw), scopes=json.dumps(sorted(set(body.scopes))), created_at=datetime.now(timezone.utc))
        session.add(row)
        await session.commit()
    return {"id": row.id, "name": row.name, "key_prefix": row.key_prefix, "scopes": json.loads(row.scopes), "created_at": row.created_at, "api_key": raw}


@router.get("/api-keys")
async def list_api_keys(request: Request):
    user = get_user(request)
    if user.auth_type == "development":
        return []
    if user.auth_type != "session":
        raise HTTPException(status_code=403, detail="API key administration requires a user session")
    session_factory = request.app.state.repository.session_factory
    async with session_factory() as session:
        result = await session.execute(select(ApiKeyRow).where(ApiKeyRow.user_id == str(user.id)).order_by(ApiKeyRow.created_at.desc()))
        rows = result.scalars().all()
    return [{"id": row.id, "name": row.name, "key_prefix": row.key_prefix, "scopes": json.loads(row.scopes), "created_at": row.created_at, "last_used_at": row.last_used_at, "revoked_at": row.revoked_at} for row in rows]


@router.post("/api-keys/{key_id}/revoke")
async def revoke_api_key(key_id: UUID, request: Request):
    user = get_user(request)
    if user.auth_type != "session":
        raise HTTPException(status_code=403, detail="API key administration requires a user session")
    async with request.app.state.repository.session_factory() as session:
        row = await session.get(ApiKeyRow, str(key_id))
        if not row or row.user_id != str(user.id):
            raise HTTPException(status_code=404, detail="API key not found")
        row.revoked_at = datetime.now(timezone.utc)
        await session.commit()
    return {"id": str(key_id), "revoked": True}
