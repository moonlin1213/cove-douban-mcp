"""Bearer and Origin checks for loopback-only HTTP."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path

from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from cove_douban_mcp.storage.permissions import make_file_private


@dataclass(frozen=True, slots=True)
class LocalBearerAuth:
    token: str
    allowed_origins: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if len(self.token) < 43:
            raise ValueError("HTTP bearer token must provide at least 256 bits")

    def authorize(self, headers: Headers) -> tuple[bool, int]:
        supplied = headers.get("authorization", "")
        prefix = "Bearer "
        if not supplied.startswith(prefix) or not secrets.compare_digest(
            supplied[len(prefix) :],
            self.token,
        ):
            return False, 401
        origin = headers.get("origin")
        if origin is not None and origin not in self.allowed_origins:
            return False, 403
        return True, 200


class AuthenticatedASGI:
    def __init__(self, app: ASGIApp, auth: LocalBearerAuth) -> None:
        self.app = app
        self.auth = auth

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        authorized, status = self.auth.authorize(Headers(scope=scope))
        if not authorized:
            response = JSONResponse(
                {"error": "unauthorized" if status == 401 else "origin_rejected"},
                status_code=status,
            )
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)


def load_or_create_http_token(path: Path) -> str:
    if path.exists():
        make_file_private(path, require_strong=True)
        return path.read_text(encoding="utf-8").strip()
    path.parent.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(32)
    try:
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
    except FileExistsError:
        return load_or_create_http_token(path)
    try:
        with os.fdopen(
            descriptor,
            "w",
            encoding="utf-8",
            newline="\n",
        ) as token_file:
            token_file.write(f"{token}\n")
        make_file_private(path, require_strong=True)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return token
