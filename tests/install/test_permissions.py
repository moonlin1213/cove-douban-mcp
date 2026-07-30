from cove_douban_mcp.config import ExportPolicy, Settings


def test_permissions_enable_export_only_with_explicit_root(
    cli_runner,
    isolated_env,
    tmp_path,
) -> None:
    cli_runner("setup", "--yes")
    export_root = tmp_path / "exports"

    result = cli_runner(
        "permissions",
        "export",
        "--policy",
        "confirm_each",
        "--root",
        str(export_root),
    )

    assert result.exit_code == 0
    settings = Settings.load(isolated_env.data_root / "config.toml")
    assert settings.export.enabled is True
    assert settings.export.policy == ExportPolicy.CONFIRM_EACH
    assert settings.export.root == export_root


def test_permissions_disable_invalidates_pending_proposals(
    cli_runner,
    isolated_env,
) -> None:
    cli_runner("setup", "--yes")
    proposals = isolated_env.data_root / "proposals"
    proposals.mkdir(parents=True, exist_ok=True)
    pending = proposals / ("a" * 43 + ".json")
    pending.write_text(
        """{
  "version": 1,
  "proposal_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "scope": "client",
  "result_ref": "ref",
  "target": "list.md",
  "mode": "create",
  "heading": "",
  "status": "pending",
  "created_at": 1
}
""",
        encoding="utf-8",
    )

    result = cli_runner("permissions", "export", "--disable")

    assert result.exit_code == 0
    assert '"status": "invalidated"' in pending.read_text(encoding="utf-8")
