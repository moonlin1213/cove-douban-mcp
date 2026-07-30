#!/usr/bin/env python3
"""Synthetic OpenCLI process used only by isolated tests."""

from __future__ import annotations

import json
import sys
import time


def main() -> int:
    arguments = sys.argv[1:]
    if arguments == ["--version"]:
        print("opencli 1.8.6")
        return 0
    if len(arguments) < 2 or arguments[0] != "douban":
        print("invalid invocation", file=sys.stderr)
        return 2

    command = arguments[1]
    payload = arguments[2:]
    if "timeout" in payload:
        time.sleep(5)
    if "sensitive-error" in payload:
        print(
            "Cookie: private-cookie-value Authorization: Bearer private-token-value",
            file=sys.stderr,
        )
        return 1
    if "bridge-error" in payload:
        print("Browser bridge is unavailable", file=sys.stderr)
        return 1
    if "malformed" in payload:
        print("not-json")
        return 0
    if "typed-error" in payload:
        print(json.dumps({"error": {"code": "login_required", "message": "Sign in"}}))
        return 0

    query = payload[0] if payload else ""
    print(
        json.dumps(
            {
                "columns": ["title", "id"],
                "rows": [{"title": query or f"示例 {command}", "id": "100001"}],
            },
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
