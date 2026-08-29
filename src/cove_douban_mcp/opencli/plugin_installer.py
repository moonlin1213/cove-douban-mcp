"""Explicit, conflict-aware installation of the bundled OpenCLI plugin."""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

from cove_douban_mcp.domain.errors import DoubanError

ADAPTER_NAMES = (
    "search",
    "chart",
    "subject",
    "marks",
    "marks-full",
    "reviews",
    "doulists",
    "doulist",
)
SUPPORT_FILES = ("extractors", "utils")


def bundled_plugin_path() -> Path:
    source_checkout = Path(__file__).resolve().parents[3] / "opencli-plugin"
    if source_checkout.is_dir():
        return source_checkout
    packaged = resources.files("cove_douban_mcp").joinpath("opencli_plugin")
    return Path(str(packaged))


@dataclass(frozen=True, slots=True)
class SetupPlan:
    data_root: Path
    plugin_source: Path
    plugin_target: Path
    actions: tuple[str, ...]
    conflicts: tuple[Path, ...] = field(default_factory=tuple)

    @property
    def safe_to_apply(self) -> bool:
        return not self.conflicts


class PluginInstaller:
    def __init__(
        self,
        opencli_home: Path,
        *,
        source: Path | None = None,
    ) -> None:
        self.opencli_home = opencli_home
        self.source = source or bundled_plugin_path()
        self.target = opencli_home / "plugins" / "cove-douban-mcp"
        self.adapter_target = opencli_home / "clis" / "douban"

    def conflicts(self) -> tuple[Path, ...]:
        conflicts = [
            self.adapter_target / f"{name}.js"
            for name in (*ADAPTER_NAMES, *SUPPORT_FILES)
            if (self.adapter_target / f"{name}.js").exists()
        ]
        if self.target.exists():
            conflicts.append(self.target)
        return tuple(conflicts)

    def plan(self, data_root: Path) -> SetupPlan:
        return SetupPlan(
            data_root=data_root,
            plugin_source=self.source,
            plugin_target=self.target,
            actions=(
                "create private application-data directories",
                "write default read-only configuration",
                "install the bundled plugin and eight conflict-checked local adapters",
                "print generic MCP client configuration",
            ),
            conflicts=self.conflicts(),
        )

    def install(self) -> Path:
        conflicts = self.conflicts()
        if conflicts:
            raise DoubanError(
                "install_conflict",
                "an existing adapter or plugin would be replaced",
                "Back it up and remove it explicitly, or cancel setup.",
            )
        if not self.source.is_dir():
            raise DoubanError(
                "plugin_missing",
                "the bundled OpenCLI plugin is missing from this installation",
            )
        self.target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            self.source,
            self.target,
            ignore=shutil.ignore_patterns("node_modules", ".DS_Store", "*.log"),
        )
        source_adapters = self.source / "clis" / "douban"
        self.adapter_target.mkdir(parents=True, exist_ok=True)
        for name in (*ADAPTER_NAMES, *SUPPORT_FILES):
            shutil.copy2(source_adapters / f"{name}.js", self.adapter_target)
        return self.target

    def uninstall(self) -> bool:
        removed = False
        source_adapters = self.source / "clis" / "douban"
        for name in (*ADAPTER_NAMES, *SUPPORT_FILES):
            installed = self.adapter_target / f"{name}.js"
            source = source_adapters / f"{name}.js"
            if (
                installed.exists()
                and source.exists()
                and self._digest(installed) == self._digest(source)
            ):
                installed.unlink()
                removed = True
        if self.adapter_target.exists() and not any(self.adapter_target.iterdir()):
            self.adapter_target.rmdir()
        if self.target.exists():
            shutil.rmtree(self.target)
            removed = True
        return removed

    @staticmethod
    def _digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()
