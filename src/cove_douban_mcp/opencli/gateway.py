"""Async, shell-free OpenCLI process execution."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from pydantic import Field

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.domain.models import PublicModel
from cove_douban_mcp.opencli.parser import parse_opencli_json, redact_diagnostic
from cove_douban_mcp.opencli.registry import validate_arguments


class OpenCLIResult(PublicModel):
    ok: bool
    rows: list[dict[str, object]] = Field(default_factory=list)
    error_code: str = ""
    safe_error: str = ""


class OpenCLIGateway:
    def __init__(self, binary: str | Path, *, timeout_seconds: float = 45.0) -> None:
        self.binary = Path(binary)
        self.timeout_seconds = timeout_seconds

    def _prefix(self) -> list[str]:
        if self.binary.suffix.casefold() == ".py":
            return [sys.executable, str(self.binary)]
        return [str(self.binary)]

    async def run(self, command: str, arguments: list[str]) -> OpenCLIResult:
        validated = validate_arguments(command, arguments)
        invocation = [
            *self._prefix(),
            "douban",
            command,
            *validated,
            "--site-session",
            "persistent",
            "--window",
            "background",
            "-f",
            "json",
        ]
        try:
            process = await asyncio.create_subprocess_exec(
                *invocation,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as error:
            raise DoubanError(
                "opencli_unavailable",
                "OpenCLI is not installed or could not be started",
                "Install OpenCLI and run the setup and doctor commands.",
            ) from error

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds,
            )
        except TimeoutError as error:
            process.kill()
            await process.communicate()
            raise DoubanError(
                "source_timeout",
                "the local browser-backed request timed out",
                "Check Chrome and the Browser Bridge, then retry.",
            ) from error

        stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
        stderr = redact_diagnostic(stderr_bytes.decode("utf-8", errors="replace"))
        if process.returncode != 0:
            lowered = stderr.casefold()
            if "bridge" in lowered:
                code = "browser_bridge_unavailable"
            elif "login" in lowered or "sign in" in lowered:
                code = "login_required"
            else:
                code = "source_unavailable"
            return OpenCLIResult(
                ok=False,
                error_code=code,
                safe_error=stderr or "the local read adapter failed",
            )

        rows = parse_opencli_json(stdout)
        return OpenCLIResult(ok=True, rows=rows)

