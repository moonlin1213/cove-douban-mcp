import os
from types import SimpleNamespace

import pytest

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.export import sandbox as sandbox_module
from cove_douban_mcp.export.sandbox import ExportSandbox


def test_parent_escape_is_rejected(tmp_path) -> None:
    sandbox = ExportSandbox(tmp_path / "allowed")

    with pytest.raises(DoubanError, match="path_outside_root"):
        sandbox.resolve_markdown("../outside.md")


def test_absolute_escape_is_rejected(tmp_path) -> None:
    sandbox = ExportSandbox(tmp_path / "allowed")

    with pytest.raises(DoubanError, match="path_outside_root"):
        sandbox.resolve_markdown(str(tmp_path / "outside.md"))


def test_non_markdown_extension_is_rejected(tmp_path) -> None:
    sandbox = ExportSandbox(tmp_path / "allowed")

    with pytest.raises(DoubanError, match="invalid_export_path"):
        sandbox.resolve_markdown("data.json")


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink semantics")
def test_symlink_escape_is_rejected(tmp_path) -> None:
    root = tmp_path / "allowed"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "linked").symlink_to(outside, target_is_directory=True)
    sandbox = ExportSandbox(root)

    with pytest.raises(DoubanError, match="path_outside_root"):
        sandbox.resolve_markdown("linked/escaped.md")


def test_valid_nested_markdown_path_is_resolved(tmp_path) -> None:
    root = tmp_path / "allowed"
    sandbox = ExportSandbox(root)

    assert sandbox.resolve_markdown("lists/example.markdown") == root / "lists" / "example.markdown"


def test_windows_reparse_guard_detects_junction_attribute(monkeypatch) -> None:
    class FakePath:
        def exists(self) -> bool:
            return True

        def stat(self, *, follow_symlinks: bool):
            assert follow_symlinks is False
            return SimpleNamespace(st_file_attributes=0x0400)

    monkeypatch.setattr(sandbox_module.os, "name", "nt")

    assert sandbox_module._is_windows_reparse_point(FakePath()) is True  # type: ignore[arg-type]
