from cove_douban_mcp.storage.paths import AppPaths


def test_injected_root_produces_complete_isolated_layout(tmp_path) -> None:
    paths = AppPaths.from_root(tmp_path / "app-data")

    assert paths.root == tmp_path / "app-data"
    assert paths.config == paths.root / "config.toml"
    assert paths.query_cache == paths.root / "cache" / "queries.json"
    assert paths.marks == paths.root / "cache" / "movie-marks.json"
    assert paths.sync_state == paths.root / "cache" / "sync-state.json"
    assert paths.opencli_lock == paths.root / "cache" / "opencli-browser.lock"
    assert paths.working == paths.root / "cache" / "working"
    assert paths.proposals == paths.root / "proposals"
    assert paths.logs == paths.root / "logs"


def test_ensure_creates_only_directories_under_injected_root(tmp_path) -> None:
    paths = AppPaths.from_root(tmp_path / "isolated")

    paths.ensure()

    assert paths.cache.is_dir()
    assert paths.working.is_dir()
    assert paths.proposals.is_dir()
    assert paths.logs.is_dir()
