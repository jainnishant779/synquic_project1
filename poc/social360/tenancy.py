"""Tenant identity. The tenant always comes from a signed token, never from request data."""
import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass


class AuthError(Exception):
    pass


class AccessDenied(Exception):
    pass


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    role: str = "service"


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def issue_token(tenant_id: str, secret: bytes, role: str = "service", ttl_seconds: int = 3600) -> str:
    body = _b64(json.dumps({"tenant": tenant_id, "role": role, "exp": time.time() + ttl_seconds}).encode())
    signature = _b64(hmac.new(secret, body.encode(), hashlib.sha256).digest())
    return f"{body}.{signature}"


def verify_token(token: str, secret: bytes) -> TenantContext:
    try:
        body, signature = token.split(".")
    except ValueError as exc:
        raise AuthError("malformed token") from exc
    expected = _b64(hmac.new(secret, body.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(signature, expected):
        raise AuthError("bad signature")
    claims = json.loads(_unb64(body))
    if claims["exp"] < time.time():
        raise AuthError("token expired")
    return TenantContext(claims["tenant"], claims["role"])
