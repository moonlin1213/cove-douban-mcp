"""Stable public errors that do not leak provider or runtime details."""

from __future__ import annotations


class DoubanError(Exception):
    """An expected, safe-to-report application error."""

    def __init__(self, code: str, message: str, action: str = "") -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.action = action

