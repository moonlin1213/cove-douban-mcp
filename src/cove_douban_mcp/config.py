"""Versioned, secret-minimizing local configuration."""

from __future__ import annotations

import tomllib
from enum import StrEnum
from pathlib import Path

import tomli_w
from pydantic import Field

from cove_douban_mcp.domain.models import PublicModel
from cove_douban_mcp.storage.permissions import make_file_private


class ExportPolicy(StrEnum):
    OFF = "off"
    CONFIRM_EACH = "confirm_each"
    ALLOW_IN_ROOT = "allow_in_root"


class CacheSettings(PublicModel):
    query_ttl_seconds: int = 21_600
    query_max_entries: int = 80
    working_ttl_seconds: int = 86_400
    working_max_refs_per_scope: int = 16
    working_max_bytes_per_ref: int = 8_388_608
    working_max_total_bytes_per_scope: int = 67_108_864


class MarksSettings(PublicModel):
    default_page_size: int = 30
    maximum_page_size: int = 200


class SyncSettings(PublicModel):
    enabled: bool = True
    local_time: str = "05:10"
    statuses: list[str] = Field(default_factory=lambda: ["wish", "collect"])
    include_doulists: bool = True
    startup_delay_seconds: int = 90


class ExportSettings(PublicModel):
    enabled: bool = False
    policy: ExportPolicy = ExportPolicy.OFF
    root: Path | None = None
    maximum_write_bytes: int = 10_485_760


class HttpSettings(PublicModel):
    host: str = "127.0.0.1"
    port: int = 8765
    authentication_required: bool = True
    allowed_origins: list[str] = Field(default_factory=list)


class Settings(PublicModel):
    version: int = 1
    cache: CacheSettings = Field(default_factory=CacheSettings)
    marks: MarksSettings = Field(default_factory=MarksSettings)
    sync: SyncSettings = Field(default_factory=SyncSettings)
    export: ExportSettings = Field(default_factory=ExportSettings)
    http: HttpSettings = Field(default_factory=HttpSettings)

    @classmethod
    def default(cls, _data_root: Path | None = None) -> Settings:
        return cls()

    @classmethod
    def load(cls, path: Path) -> Settings:
        if not path.exists():
            return cls.default(path.parent)
        with path.open("rb") as handle:
            return cls.model_validate(tomllib.load(handle))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        serialized = tomli_w.dumps(self.model_dump(mode="json", exclude_none=True))
        path.write_text(serialized, encoding="utf-8", newline="\n")
        make_file_private(path)

