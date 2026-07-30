"""Shared service helpers and dependency protocols."""

from __future__ import annotations

from typing import Protocol

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.domain.models import ToolError
from cove_douban_mcp.opencli.gateway import OpenCLIResult


class Gateway(Protocol):
    async def run(self, command: str, arguments: list[str]) -> OpenCLIResult: ...


def gateway_error(result: OpenCLIResult) -> DoubanError:
    return DoubanError(
        result.error_code or "source_unavailable",
        result.safe_error or "the local read source is unavailable",
        "Check Chrome, the Browser Bridge, and the doctor output.",
    )


def warning_from(result: OpenCLIResult) -> ToolError:
    return ToolError(
        code=result.error_code or "source_unavailable",
        message=result.safe_error or "using cached data because refresh failed",
        action="Check the local browser connection before the next refresh.",
    )

