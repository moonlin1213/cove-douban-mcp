"""Strict JSON parsing and secret-minimizing diagnostics."""

from __future__ import annotations

import json
import re
from typing import Any, cast

from cove_douban_mcp.domain.errors import DoubanError

_SECRET_PATTERNS = (
    re.compile(r"(?i)(cookie\s*[:=]\s*)\S+"),
    re.compile(r"(?i)(authorization\s*[:=]\s*)\S+(?:\s+\S+)?"),
    re.compile(r"(?i)(bearer\s+)\S+"),
)
_PATH_PATTERNS = (
    re.compile(r"/Users/[^/\s]+"),
    re.compile(r"(?i)[A-Z]:\\Users\\[^\\\s]+"),
)
_SAFE_CODES = {
    "login_required",
    "browser_bridge_unavailable",
    "source_changed",
    "empty_result",
    "invalid_argument",
}


def redact_diagnostic(value: str, *, maximum_length: int = 500) -> str:
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}[redacted]", redacted)
    for pattern in _PATH_PATTERNS:
        redacted = pattern.sub("[user-path]", redacted)
    return redacted.strip()[:maximum_length]


def _malformed() -> DoubanError:
    return DoubanError(
        "source_malformed",
        "the local browser adapter returned an unexpected result",
        "Run the doctor command and update the adapter if the source page changed.",
    )


def parse_opencli_json(stdout: str) -> list[dict[str, Any]]:
    try:
        document: Any = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise _malformed() from error

    if isinstance(document, dict) and isinstance(document.get("error"), dict):
        adapter_error = document["error"]
        raw_code = str(adapter_error.get("code", "source_changed"))
        code = raw_code if raw_code in _SAFE_CODES else "source_changed"
        raise DoubanError(
            code,
            redact_diagnostic(str(adapter_error.get("message", "adapter error"))),
        )

    rows: Any
    if isinstance(document, list):
        rows = document
    elif isinstance(document, dict):
        rows = document.get("rows", document.get("data"))
    else:
        raise _malformed()
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise _malformed()
    return cast(list[dict[str, Any]], rows)
