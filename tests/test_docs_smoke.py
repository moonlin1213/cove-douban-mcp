import json
from pathlib import Path

from cove_douban_mcp.cli import main


def test_generic_examples_are_valid_json_and_use_no_personal_paths() -> None:
    root = Path(__file__).parents[1]
    stdio = json.loads((root / "examples" / "generic-stdio.json").read_text())
    http = json.loads((root / "examples" / "generic-streamable-http.json").read_text())

    assert stdio["mcpServers"]["douban"]["command"] == "cove-douban-mcp"
    assert stdio["mcpServers"]["douban"]["args"] == ["serve", "--transport", "stdio"]
    assert http["url"] == "http://127.0.0.1:8765/mcp"
    assert "${COVE_DOUBAN_MCP_TOKEN}" in http["headers"]["Authorization"]


def test_documented_shell_free_commands_execute_in_isolation(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("COVE_DOUBAN_DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setenv("COVE_DOUBAN_OPENCLI_HOME", str(tmp_path / "opencli"))

    assert main(["setup", "--dry-run"]) == 0
    assert main(["print-config", "--transport", "stdio"]) == 0
    assert main(["print-config", "--transport", "streamable-http"]) == 0


def test_readme_links_required_public_documents() -> None:
    root = Path(__file__).parents[1]
    readme = (root / "README.md").read_text(encoding="utf-8")

    for relative in (
        "docs/security.md",
        "docs/privacy.md",
        "docs/troubleshooting.md",
        "SECURITY.md",
        "CONTRIBUTING.md",
    ):
        assert relative in readme
        assert (root / relative).exists()


def test_readme_uninstalls_v010_adapters_before_installing_v011() -> None:
    root = Path(__file__).parents[1]
    readme = (root / "README.md").read_text(encoding="utf-8")
    upgrade = readme.split("从 `v0.1.0` 升级", maxsplit=1)[1].split(
        "### 方法二", maxsplit=1
    )[0]

    uninstall = upgrade.index("cove-douban-mcp uninstall")
    install = upgrade.index("uv tool install --force")
    setup = upgrade.index("cove-douban-mcp setup --yes")

    assert uninstall < install < setup
    assert "用户修改过的 adapter" in " ".join(upgrade.split())
