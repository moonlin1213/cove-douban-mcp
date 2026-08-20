"""Platform-native runtime paths with injectable test roots."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_data_path


@dataclass(frozen=True, slots=True)
class AppPaths:
    root: Path
    config: Path
    cache: Path
    query_cache: Path
    marks: Path
    sync_state: Path
    opencli_lock: Path
    working: Path
    proposals: Path
    logs: Path

    @classmethod
    def from_root(cls, root: Path) -> AppPaths:
        root = root.expanduser().absolute()
        cache = root / "cache"
        return cls(
            root=root,
            config=root / "config.toml",
            cache=cache,
            query_cache=cache / "queries.json",
            marks=cache / "movie-marks.json",
            sync_state=cache / "sync-state.json",
            opencli_lock=cache / "opencli-browser.lock",
            working=cache / "working",
            proposals=root / "proposals",
            logs=root / "logs",
        )

    @classmethod
    def platform_default(cls) -> AppPaths:
        return cls.from_root(Path(user_data_path("cove-douban-mcp", appauthor=False)))

    def ensure(self) -> None:
        for directory in (self.root, self.cache, self.working, self.proposals, self.logs):
            directory.mkdir(parents=True, exist_ok=True)
            if os.name != "nt":
                directory.chmod(0o700)
