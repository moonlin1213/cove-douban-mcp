"""Read-only checks for the local OpenCLI executable."""

from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path

from cove_douban_mcp.domain.models import PublicModel

_VERSION = re.compile(r"(\d+\.\d+\.\d+)")


class DiagnosticResult(PublicModel):
    available: bool
    version: str = ""
    message: str = ""


class OpenCLIDiagnostics:
    def __init__(self, binary: str | Path) -> None:
        self.binary = Path(binary)

    async def check(self) -> DiagnosticResult:
        prefix = (
            [sys.executable, str(self.binary)]
            if self.binary.suffix.casefold() == ".py"
            else [str(self.binary)]
        )
        try:
            process = await asyncio.create_subprocess_exec(
                *prefix,
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _stderr = await asyncio.wait_for(process.communicate(), timeout=5)
        except (OSError, TimeoutError):
            return DiagnosticResult(
                available=False,
                message="OpenCLI is unavailable",
            )
        text = stdout.decode("utf-8", errors="replace")
        match = _VERSION.search(text)
        return DiagnosticResult(
            available=process.returncode == 0 and match is not None,
            version=match.group(1) if match else "",
            message="" if match else "OpenCLI returned no recognizable version",
        )
