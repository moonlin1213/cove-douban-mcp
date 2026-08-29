def test_setup_dry_run_has_no_filesystem_side_effects(cli_runner, isolated_env) -> None:
    result = cli_runner("setup", "--dry-run")

    assert result.exit_code == 0
    assert "dry run" in result.stdout.lower()
    assert isolated_env.changed_paths() == set()


def test_existing_user_adapter_stops_default_install(cli_runner, isolated_env) -> None:
    isolated_env.create_user_adapter("douban/search.js")

    result = cli_runner("setup", "--yes")

    assert result.exit_code != 0
    assert "existing adapter" in result.stderr.lower()
    assert not (isolated_env.opencli_home / "plugins" / "cove-douban-mcp").exists()


def test_approved_setup_writes_only_isolated_roots(cli_runner, isolated_env) -> None:
    result = cli_runner("setup", "--yes")

    assert result.exit_code == 0
    assert (isolated_env.data_root / "config.toml").exists()
    plugin = isolated_env.opencli_home / "plugins" / "cove-douban-mcp"
    assert (plugin / "opencli-plugin.json").exists()
    assert (plugin / "clis" / "douban" / "search.js").exists()
    assert (plugin / "clis" / "douban" / "chart.js").exists()
    assert (isolated_env.opencli_home / "clis" / "douban" / "search.js").exists()
    assert (isolated_env.opencli_home / "clis" / "douban" / "chart.js").exists()
