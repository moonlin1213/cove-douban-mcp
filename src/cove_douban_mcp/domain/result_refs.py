"""Opaque identifiers for server-side working results."""

from __future__ import annotations

import secrets


def new_opaque_ref() -> str:
    """Return a URL-safe reference containing 256 bits of randomness."""

    return secrets.token_urlsafe(32)

