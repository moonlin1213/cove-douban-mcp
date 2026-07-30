from cove_douban_mcp.config import ExportPolicy, Settings


def test_export_is_disabled_by_default(tmp_path) -> None:
    settings = Settings.default(tmp_path)

    assert settings.export.enabled is False
    assert settings.export.policy == ExportPolicy.OFF
    assert settings.export.root is None


def test_settings_round_trip_without_credentials(tmp_path) -> None:
    path = tmp_path / "config.toml"
    settings = Settings.default(tmp_path)
    settings.export.enabled = True
    settings.export.policy = ExportPolicy.CONFIRM_EACH
    settings.export.root = tmp_path / "exports"

    settings.save(path)
    loaded = Settings.load(path)

    assert loaded == settings
    text = path.read_text(encoding="utf-8")
    assert "password" not in text.casefold()
    assert "cookie" not in text.casefold()

