"""Best-effort private permissions for local application state."""

from __future__ import annotations

import os
from pathlib import Path


def make_file_private(path: Path) -> None:
    """Apply owner-only POSIX permissions.

    Windows ACL hardening is performed by the setup command before it creates
    an HTTP credential; ordinary non-secret cache files rely on the user's
    profile ACL.
    """

    if os.name != "nt":
        path.chmod(0o600)

