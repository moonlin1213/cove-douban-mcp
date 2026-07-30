"""Private permissions for local application state."""

from __future__ import annotations

import getpass
import os
import subprocess
from pathlib import Path


def make_file_private(path: Path, *, require_strong: bool = False) -> None:
    """Limit a file to the current user.

    POSIX platforms use mode ``0600``. Windows uses ``icacls`` without a
    shell to remove inherited entries and grant full control only to the
    current user. Callers creating credentials set ``require_strong`` so an
    unavailable or rejected Windows ACL operation becomes a hard failure.
    """

    if os.name != "nt":
        path.chmod(0o600)
        return

    current_user = getpass.getuser().strip()
    if not current_user:
        if require_strong:
            raise PermissionError("could not establish a current-user-only ACL")
        return

    try:
        result = subprocess.run(
            [
                "icacls",
                str(path),
                "/inheritance:r",
                "/grant:r",
                f"{current_user}:(F)",
            ],
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError as exc:
        if require_strong:
            raise PermissionError(
                "could not establish a current-user-only ACL"
            ) from exc
        return

    if result.returncode != 0 and require_strong:
        raise PermissionError("could not establish a current-user-only ACL")
