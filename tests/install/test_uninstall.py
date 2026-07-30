def test_default_uninstall_removes_plugin_but_preserves_data(
    cli_runner,
    isolated_env,
) -> None:
    cli_runner("setup", "--yes")
    marker = isolated_env.data_root / "cache" / "preserve.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("{}", encoding="utf-8")

    result = cli_runner("uninstall", "--yes")

    assert result.exit_code == 0
    assert marker.exists()
    assert not (isolated_env.opencli_home / "plugins" / "cove-douban-mcp").exists()
    assert not (isolated_env.opencli_home / "clis" / "douban").exists()


def test_uninstall_preserves_an_adapter_modified_after_setup(
    cli_runner,
    isolated_env,
) -> None:
    cli_runner("setup", "--yes")
    adapter = isolated_env.opencli_home / "clis" / "douban" / "search.js"
    adapter.write_text("// user changed this after setup\n", encoding="utf-8")

    result = cli_runner("uninstall", "--yes")

    assert result.exit_code == 0
    assert adapter.exists()


def test_purge_requires_explicit_double_confirmation(cli_runner, isolated_env) -> None:
    cli_runner("setup", "--yes")

    refused = cli_runner("uninstall", "--purge-data", "--yes")
    accepted = cli_runner(
        "uninstall",
        "--purge-data",
        "--yes",
        "--confirm-purge",
    )

    assert refused.exit_code != 0
    assert accepted.exit_code == 0
    assert not isolated_env.data_root.exists()
