from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pytest

from cove_douban_mcp.config import Settings
from cove_douban_mcp.opencli.gateway import OpenCLIResult
from cove_douban_mcp.services.container import ServiceContainer
from cove_douban_mcp.storage.paths import AppPaths


class FakeGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str]]] = []
        self.failures: dict[str, tuple[str, str]] = {}
        self.rows: dict[str, list[dict[str, object]]] = defaultdict(list)

    async def run(self, command: str, arguments: list[str]) -> OpenCLIResult:
        self.calls.append((command, arguments))
        if command in self.failures:
            code, message = self.failures[command]
            return OpenCLIResult(
                ok=False,
                error_code=code,
                safe_error=message,
            )
        rows = self.rows[command]
        if command in {"marks", "marks-full"}:
            status = arguments[arguments.index("--status") + 1]
            mark_rows = [
                {
                    "movie_id": f"{status}-100001",
                    "title": f"虚构{status}影片",
                    "status": status,
                    "genres": ["喜剧"],
                    "countries": ["中国香港"],
                    "year": 2024,
                }
            ]
            offset = (
                int(arguments[arguments.index("--offset") + 1])
                if "--offset" in arguments
                else 0
            )
            rows = mark_rows[offset:]
        return OpenCLIResult(ok=True, rows=rows)


@pytest.fixture
def gateway() -> FakeGateway:
    gateway = FakeGateway()
    gateway.rows["search"] = [
        {
            "subject_id": "100001",
            "title": "虚构影片",
            "url": "https://movie.example.invalid/subject/100001/",
            "media_type": "movie",
        }
    ]
    gateway.rows["subject"] = [
        {
            "subject_id": "100001",
            "title": "虚构影片",
            "media_type": "movie",
            "summary": "完全虚构的简介",
        }
    ]
    gateway.rows["reviews"] = [
        {"review_id": "300001", "title": "虚构短评", "author": "示例用户"}
    ]
    gateway.rows["doulists"] = [
        {"doulist_id": "400001", "title": "虚构豆列", "item_count": 2}
    ]
    gateway.rows["doulist"] = [
        {"item_id": "1", "subject_id": "100001", "title": "虚构影片"}
    ]
    return gateway


@pytest.fixture
def container(tmp_path: Path, gateway: FakeGateway) -> ServiceContainer:
    settings = Settings.default(tmp_path)
    paths = AppPaths.from_root(tmp_path / "app")
    paths.ensure()
    return ServiceContainer.create(settings=settings, paths=paths, gateway=gateway)
