"""Authentication and API protection dependencies."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from cybershield.api.models import TokenResponse


JWT_ALGORITHM = "HS256"
JWT_DEFAULT_EXP_MINUTES = 60

_SECRET_KEY = os.getenv("CYBERSHIELD_JWT_SECRET", "cybershield-dev-secret-change-me")
_security = HTTPBearer(auto_error=True)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(payload: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    return _b64url_encode(digest)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> TokenResponse:
    """Create an HMAC-signed JWT access token."""
    expires_delta = expires_delta or timedelta(minutes=JWT_DEFAULT_EXP_MINUTES)
    expires_at = datetime.now(timezone.utc) + expires_delta
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {"sub": subject, "exp": int(expires_at.timestamp()), "iat": int(datetime.now(timezone.utc).timestamp())}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}"
    signature = _sign(signing_input, _SECRET_KEY)
    token = f"{signing_input}.{signature}"
    return TokenResponse(access_token=token, expires_at=expires_at)


def decode_access_token(token: str) -> dict[str, int | str]:
    """Decode and validate JWT token signature and expiry."""
    try:
        header_b64, payload_b64, signature = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format") from exc

    signing_input = f"{header_b64}.{payload_b64}"
    expected = _sign(signing_input, _SECRET_KEY)
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature")

    try:
        payload_raw = _b64url_decode(payload_b64)
        payload = json.loads(payload_raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload") from exc

    exp = payload.get("exp")
    if not isinstance(exp, int):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token expiry")
    if datetime.now(timezone.utc).timestamp() >= exp:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    return payload


def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(_security)]) -> str:
    payload = decode_access_token(credentials.credentials)
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    return subject


@dataclass(slots=True)
class _RateWindow:
    started_at: datetime
    count: int


class InMemoryRateLimiter:
    """Simple fixed-window rate limiter per user and route."""

    def __init__(self, requests_per_minute: int = 60) -> None:
        self.requests_per_minute = requests_per_minute
        self._lock = Lock()
        self._windows: dict[str, _RateWindow] = {}

    def check(self, key: str) -> None:
        now = datetime.now(timezone.utc)
        with self._lock:
            window = self._windows.get(key)
            if window is None or (now - window.started_at) >= timedelta(minutes=1):
                self._windows[key] = _RateWindow(started_at=now, count=1)
                return
            if window.count >= self.requests_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please retry in under a minute.",
                )
            window.count += 1


rate_limiter = InMemoryRateLimiter(requests_per_minute=120)


def enforce_rate_limit(request: Request, user: Annotated[str, Depends(get_current_user)]) -> None:
    route_key = request.url.path
    rate_limiter.check(f"{user}:{route_key}")


def enforce_public_rate_limit(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    route_key = request.url.path
    rate_limiter.check(f"anon:{client}:{route_key}")
