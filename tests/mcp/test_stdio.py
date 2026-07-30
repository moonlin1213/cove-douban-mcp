import os

from cove_douban_mcp.mcp.transport import stdio_environment


def test_stdio_environment_is_unbuffered_and_does_not_include_secrets(tmp_path) -> None:
    environment = stdio_environment(
        data_root=tmp_path,
        base={"PATH": os.environ.get("PATH", "")},
    )

    assert environment["PYTHONUNBUFFERED"] == "1"
    assert environment["COVE_DOUBAN_DATA_ROOT"] == str(tmp_path)
    assert all("TOKEN" not in key and "COOKIE" not in key for key in environment)
