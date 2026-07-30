"""Standard stdio and authenticated loopback Streamable HTTP transports."""

from __future__ import annotations

import ipaddress
import os
from collections.abc import Mapping
from pathlib import Path

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.types import ASGIApp

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.mcp.auth import AuthenticatedASGI, LocalBearerAuth


def validate_loopback_host(host: str) -> str:
    if host.casefold() == "localhost":
        return host
    try:
        address = ipaddress.ip_address(host)
    except ValueError as error:
        raise DoubanError(
            "unsafe_http_host",
            "local HTTP can bind only to a loopback address",
        ) from error
    if not address.is_loopback:
        raise DoubanError(
            "unsafe_http_host",
            "local HTTP can bind only to a loopback address",
        )
    return host


def build_http_app(server: FastMCP, *, auth: LocalBearerAuth) -> ASGIApp:
    return AuthenticatedASGI(server.streamable_http_app(), auth)


def run_stdio(server: FastMCP) -> None:
    server.run("stdio")


def run_streamable_http(
    server: FastMCP,
    *,
    host: str,
    port: int,
    auth: LocalBearerAuth,
) -> None:
    validated_host = validate_loopback_host(host)
    uvicorn.run(
        build_http_app(server, auth=auth),
        host=validated_host,
        port=port,
        log_level="info",
    )


def stdio_environment(
    *,
    data_root: Path,
    base: Mapping[str, str] | None = None,
) -> dict[str, str]:
    source = dict(base or os.environ)
    allowed_names = {
        "PATH",
        "PATHEXT",
        "SYSTEMROOT",
        "WINDIR",
        "COMSPEC",
        "TMP",
        "TEMP",
        "LANG",
        "LC_ALL",
    }
    environment = {key: value for key, value in source.items() if key in allowed_names}
    environment["PYTHONUNBUFFERED"] = "1"
    environment["COVE_DOUBAN_DATA_ROOT"] = str(data_root)
    return environment
