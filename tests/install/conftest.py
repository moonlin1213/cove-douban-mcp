from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import pytest

from cove_douban_mcp.cli import main


@dataclass
class CliResult:
    exit_code: int
    stdout: str
    stderr: str


@pytest.fixture
def isolated_env(tmp_path, monkeypatch):
    data_root = tmp_path / "data"
    opencli_home = tmp_path / "opencli-home"
    monkeypatch.setenv("COVE_DOUBAN_DATA_ROOT", str(data_root))
    monkeypatch.setenv("COVE_DOUBAN_OPENCLI_HOME", str(opencli_home))

    class IsolatedEnvironment:
        def __init__(self) -> None:
            self.before = self.snapshot()

        def snapshot(self) -> set[Path]:
            return {
                path.relative_to(tmp_path)
                for path in tmp_path.rglob("*")
                if path.is_file()
            }

        def changed_paths(self) -> set[Path]:
            return self.snapshot() - self.before

        def create_user_adapter(self, relative: str) -> None:
            path = opencli_home / "clis" / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("// user-authored adapter\n", encoding="utf-8")

        @property
        def data_root(self) -> Path:
            return data_root

        @property
        def opencli_home(self) -> Path:
            return opencli_home

    return IsolatedEnvironment()


@pytest.fixture
def cli_runner(monkeypatch):
    def run(*arguments: str) -> CliResult:
        stdout = io.StringIO()
        stderr = io.StringIO()
        exit_code = main(
            list(arguments),
            stdout=stdout,
            stderr=stderr,
            environ=dict(__import__("os").environ),
        )
        return CliResult(exit_code, stdout.getvalue(), stderr.getvalue())

    return run

