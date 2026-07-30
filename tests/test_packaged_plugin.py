from importlib import resources
from pathlib import Path

from cove_douban_mcp.opencli.plugin_installer import ADAPTER_NAMES, bundled_plugin_path


def test_bundled_plugin_is_available_to_setup() -> None:
    root = bundled_plugin_path()

    assert (root / "opencli-plugin.json").exists()
    assert all((root / "clis" / "douban" / f"{name}.js").exists() for name in ADAPTER_NAMES)


def test_packaged_resource_contract_has_a_plugin_directory() -> None:
    package_root = resources.files("cove_douban_mcp")
    candidate = package_root.joinpath("opencli_plugin")

    if Path(str(candidate)).exists():
        assert candidate.joinpath("opencli-plugin.json").is_file()
