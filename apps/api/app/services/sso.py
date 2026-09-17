from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
import jwt
from jwt import PyJWKClient


@dataclass(frozen=True)
class OIDCIdentity:
    subject: str
    email: str
    email_verified: bool
    claims: dict


def sso_mode() -> str:
    return os.getenv("AWE_SSO_MODE", "disabled").strip().lower()


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing SSO configuration: {name}")
    return value


async def discover_oidc() -> dict:
    issuer = _required("AWE_OIDC_ISSUER").rstrip("/")
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{issuer}/.well-known/openid-configuration")
        response.raise_for_status()
        return response.json()


async def authorization_url(state: str, nonce: str) -> str:
    # Mock mode must be completely offline/deterministic so local regression
    # does not depend on an external IdP or network availability.
    if sso_mode() == "mock":
        endpoint = os.getenv("AWE_MOCK_OIDC_AUTHORIZATION_ENDPOINT", "https://mock-idp.example/authorize")
        params = {
            "response_type": "code",
            "client_id": _required("AWE_OIDC_CLIENT_ID"),
            "redirect_uri": _required("AWE_OIDC_REDIRECT_URI"),
            "scope": os.getenv("AWE_OIDC_SCOPE", "openid email profile"),
            "state": state,
            "nonce": nonce,
        }
        return f"{endpoint}?{urlencode(params)}"

    config = await discover_oidc()
    params = {
        "response_type": "code",
        "client_id": _required("AWE_OIDC_CLIENT_ID"),
        "redirect_uri": _required("AWE_OIDC_REDIRECT_URI"),
        "scope": os.getenv("AWE_OIDC_SCOPE", "openid email profile"),
        "state": state,
        "nonce": nonce,
    }
    return f"{config['authorization_endpoint']}?{urlencode(params)}"


async def exchange_code(code: str, nonce: str) -> OIDCIdentity:
    if sso_mode() == "mock":
        try:
            payload = json.loads(base64.urlsafe_b64decode(code + "=" * (-len(code) % 4)))
            if payload.get("nonce") != nonce or not payload.get("sub") or not payload.get("email"):
                raise ValueError
            return OIDCIdentity(str(payload["sub"]), str(payload["email"]).strip().lower(), bool(payload.get("email_verified", True)), payload)
        except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
            raise ValueError("Invalid mock OIDC code")

    config = await discover_oidc()
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(config["token_endpoint"], data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": _required("AWE_OIDC_REDIRECT_URI"),
            "client_id": _required("AWE_OIDC_CLIENT_ID"),
            "client_secret": _required("AWE_OIDC_CLIENT_SECRET"),
        })
        response.raise_for_status()
        tokens = response.json()

    id_token = tokens.get("id_token")
    if not id_token:
        raise ValueError("OIDC provider did not return an ID token")
    issuer = _required("AWE_OIDC_ISSUER").rstrip("/")
    jwks = PyJWKClient(config["jwks_uri"])
    signing_key = jwks.get_signing_key_from_jwt(id_token)
    claims = jwt.decode(
        id_token,
        signing_key.key,
        algorithms=["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"],
        audience=_required("AWE_OIDC_CLIENT_ID"),
        issuer=issuer,
        options={"require": ["exp", "iat", "iss", "aud", "sub", "nonce"]},
    )
    if claims.get("nonce") != nonce:
        raise ValueError("OIDC nonce mismatch")
    email = str(claims.get("email", "")).strip().lower()
    if not email:
        raise ValueError("OIDC identity has no email")
    return OIDCIdentity(str(claims["sub"]), email, bool(claims.get("email_verified", False)), claims)


def issue_state() -> tuple[str, str, datetime]:
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    return state, nonce, expires


def hash_state(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
