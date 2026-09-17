from __future__ import annotations

import hashlib
import json
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, Request, status
from sqlalchemy import DateTime, String, Text, select, Index
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from app.store import Base

DEV_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
DEV_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


class UserRow(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    email_verified: Mapped[bool] = mapped_column(default=True)


class AuthTokenRow(Base):
    __tablename__ = "auth_tokens"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    purpose: Mapped[str] = mapped_column(String(32), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SSOIdentityRow(Base):
    __tablename__ = "sso_identities"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    subject: Mapped[str] = mapped_column(String(255), index=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (Index("uq_sso_identity_provider_subject", "provider", "subject", unique=True),)


class SSOStateRow(Base):
    __tablename__ = "sso_states"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    state_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    nonce: Mapped[str] = mapped_column(String(128))
    provider: Mapped[str] = mapped_column(String(32))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SessionRow(Base):
    __tablename__ = "auth_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ApiKeyRow(Base):
    __tablename__ = "api_keys"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    name: Mapped[str] = mapped_column(String(120))
    key_prefix: Mapped[str] = mapped_column(String(20), index=True)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    scopes: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


@dataclass(frozen=True)
class AuthenticatedUser:
    id: UUID
    tenant_id: UUID
    email: str
    auth_type: str
    api_key_id: UUID | None = None
    scopes: tuple[str, ...] = ()


def auth_mode() -> str:
    return os.getenv("AWE_AUTH_MODE", "development").strip().lower()


def _hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    derived = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${salt.hex()}${derived.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        _, salt_hex, digest_hex = encoded.split("$", 2)
        actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1)
        return hmac.compare_digest(actual.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def _dev_user() -> AuthenticatedUser:
    return AuthenticatedUser(DEV_USER_ID, DEV_TENANT_ID, "developer@local", "development", scopes=("*",))


async def authenticate(request: Request) -> AuthenticatedUser:
    if auth_mode() == "development":
        return _dev_user()
    repository = request.app.state.repository
    session_factory = getattr(repository, "session_factory", None)
    if session_factory is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    credential = header[7:].strip()
    if not credential:
        raise HTTPException(status_code=401, detail="Authentication required")

    async with session_factory() as session:
        if credential.startswith("awe_" ):
            row = await session.execute(select(ApiKeyRow).where(ApiKeyRow.key_hash == _hash_secret(credential), ApiKeyRow.revoked_at.is_(None)))
            key = row.scalars().first()
            if key:
                user = await session.get(UserRow, key.user_id)
                if user:
                    key.last_used_at = datetime.now(timezone.utc)
                    await session.commit()
                    return AuthenticatedUser(UUID(user.id), UUID(user.tenant_id), user.email, "api_key", UUID(key.id), tuple(json.loads(key.scopes)))
        else:
            row = await session.execute(select(SessionRow).where(SessionRow.token_hash == _hash_secret(credential)))
            auth_session = row.scalars().first()
            if auth_session and auth_session.expires_at > datetime.now(timezone.utc):
                user = await session.get(UserRow, auth_session.user_id)
                if user:
                    return AuthenticatedUser(UUID(user.id), UUID(user.tenant_id), user.email, "session", scopes=("*",))
    raise HTTPException(status_code=401, detail="Invalid or expired credentials")


def get_user(request: Request) -> AuthenticatedUser:
    user = getattr(request.state, "user", None)
    if user is None and auth_mode() == "development":
        return _dev_user()
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def authorize_project(request: Request, project_id: UUID) -> None:
    user = get_user(request)
    repository = request.app.state.repository
    project = await repository.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Project access denied")


async def create_session(session_factory: async_sessionmaker[AsyncSession], user: UserRow) -> tuple[str, datetime]:
    raw = secrets.token_urlsafe(48)
    expires = datetime.now(timezone.utc) + timedelta(hours=int(os.getenv("AWE_SESSION_TTL_HOURS", "12")))
    async with session_factory() as session:
        session.add(SessionRow(id=str(uuid4()), user_id=user.id, token_hash=_hash_secret(raw), expires_at=expires, created_at=datetime.now(timezone.utc)))
        await session.commit()
    return raw, expires


def require_scope(request: Request, scope: str) -> None:
    user = get_user(request)
    if user.auth_type != "api_key":
        return
    if scope not in user.scopes and "*" not in user.scopes:
        raise HTTPException(status_code=403, detail=f"API key lacks required scope: {scope}")

async def _authorize_resource(request: Request, user: UserRow) -> None:
    path = request.url.path

    # Project-scoped resources.
    project_id: UUID | None = None

    if path.startswith("/api/v1/projects/"):
        parts = path.split("/")
        if len(parts) >= 5:
            try:
                project_id = UUID(parts[4])
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid project_id",
                )

    elif path.startswith("/api/v1/website-content/"):
        # Content endpoints are project-scoped by path:
        # /api/v1/website-content/{project_id}
        # /api/v1/website-content/{project_id}/{content_id}/versions
        parts = path.split("/")
        if len(parts) >= 5:
            try:
                project_id = UUID(parts[4])
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid project_id",
                )

    elif path.startswith("/api/v1/deployments/"):
        # Deployment resources are identified by deployment ID.
        parts = path.split("/")
        if len(parts) >= 5:
            try:
                deployment_id = UUID(parts[4])
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid deployment_id",
                )

            deployment = await repository.get_deployment(deployment_id)

            if deployment is None:
                raise HTTPException(
                    status_code=404,
                    detail="Deployment not found",
                )

            project_id = deployment.project_id

    else:
        # Some project-scoped operations expose project_id as a query
        # parameter rather than as part of the path.
        project_id_raw = request.query_params.get("project_id")

        if project_id_raw:
            try:
                project_id = UUID(project_id_raw)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid project_id",
                )

    if project_id is None:
        return

    # A user may access the project only if they have membership/access
    # through the tenant/team authorization model.
    membership = await repository.get_project_membership(
        project_id=project_id,
        user_id=user.id,
    )

    if membership is None:
        raise HTTPException(
            status_code=403,
            detail="Project access denied",
        )
