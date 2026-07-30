from types import SimpleNamespace

import pytest

from cove_douban_mcp.storage import permissions as permissions_module


def test_windows_strong_permission_failure_aborts_secret_creation(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "http-token"
    path.write_text("synthetic-token", encoding="utf-8")
    monkeypatch.setattr(permissions_module.os, "name", "nt")
    monkeypatch.setattr(
        permissions_module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stderr="denied"),
    )

    with pytest.raises(PermissionError, match="current-user-only ACL"):
        permissions_module.make_file_private(path, require_strong=True)


def test_windows_private_acl_uses_shell_free_icacls(tmp_path, monkeypatch) -> None:
    path = tmp_path / "http-token"
    path.write_text("synthetic-token", encoding="utf-8")
    calls: list[tuple[list[str], dict[str, object]]] = []

    def record_run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(permissions_module.os, "name", "nt")
    monkeypatch.setattr(permissions_module.getpass, "getuser", lambda: "test-user")
    monkeypatch.setattr(permissions_module.subprocess, "run", record_run)

    permissions_module.make_file_private(path, require_strong=True)

    assert calls == [
        (
            [
                "icacls",
                str(path),
                "/inheritance:r",
                "/grant:r",
                "test-user:(F)",
            ],
            {
                "capture_output": True,
                "check": False,
                "text": True,
            },
        )
    ]
