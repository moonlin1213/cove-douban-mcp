from cove_douban_mcp import __version__


def test_public_version_is_initial_release() -> None:
    assert __version__ == "0.1.0"
