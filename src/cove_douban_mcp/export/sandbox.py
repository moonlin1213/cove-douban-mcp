"""Path confinement for the optional Markdown export boundary."""

from __future__ import annotations

import os
from pathlib import Path

from cove_douban_mcp.domain.errors import DoubanError

_MARKDOWN_SUFFIXES = {".md", ".markdown"}
_WINDOWS_REPARSE_POINT = 0x0400


def _is_windows_reparse_point(path: Path) -> bool:
    if os.name != "nt" or not path.exists():
        return False
    attributes = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
    return bool(attributes & _WINDOWS_REPARSE_POINT)


class ExportSandbox:
    def __init__(self, root: Path) -> None:
        self.root = root.expanduser().absolute()

    @staticmethod
    def _outside() -> DoubanError:
        return DoubanError(
            "path_outside_root",
            "the export path resolves outside the authorized root",
            "Choose a Markdown path inside the configured export directory.",
        )

    def resolve_markdown(self, value: str) -> Path:
        requested = Path(value).expanduser()
        candidate = requested if requested.is_absolute() else self.root / requested
        if candidate.suffix.casefold() not in _MARKDOWN_SUFFIXES:
            raise DoubanError(
                "invalid_export_path",
                "only .md and .markdown files can be exported",
            )

        root_real = self.root.resolve(strict=False)
        candidate_real = candidate.resolve(strict=False)
        try:
            relative = candidate_real.relative_to(root_real)
        except ValueError as error:
            raise self._outside() from error

        current = root_real
        for component in relative.parts[:-1]:
            current = current / component
            if current.is_symlink() or _is_windows_reparse_point(current):
                raise self._outside()
        return candidate_real
