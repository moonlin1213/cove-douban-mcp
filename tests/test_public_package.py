from cove_douban_mcp import __version__


def test_public_version_is_chart_feature_release() -> None:
    assert __version__ == "0.2.0"
