"""Cross-process locks mapped to stable public errors."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from filelock import FileLock, Timeout

from cove_douban_mcp.domain.errors import DoubanError


@contextmanager
def acquire_process_lock(path: Path, timeout_seconds: float) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(path, timeout=timeout_seconds)
    try:
        with lock:
            yield
    except Timeout as error:
        raise DoubanError(
            "operation_in_progress",
            "another local operation is already in progress",
            "Wait for it to finish, then retry.",
        ) from error
