"""No-LLM, lock-protected cache synchronization."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import Field

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.domain.models import PublicModel
from cove_douban_mcp.services.doulists import DoulistsService
from cove_douban_mcp.services.marks import MarksService, MarkStatus
from cove_douban_mcp.storage.locks import acquire_process_lock
from cove_douban_mcp.storage.sync_state import SyncState, SyncStateStore


class SyncStatusOutcome(PublicModel):
    ok: bool
    count: int = 0
    error_code: str = ""
    message: str = ""


class SyncResult(PublicModel):
    ok: bool
    skipped: bool = False
    reason: str
    statuses: dict[str, SyncStatusOutcome] = Field(default_factory=dict)
    doulists: SyncStatusOutcome | None = None


class SyncService:
    def __init__(
        self,
        marks: MarksService,
        doulists: DoulistsService,
        state_store: SyncStateStore,
        lock_path: Path,
    ) -> None:
        self.marks = marks
        self.doulists = doulists
        self.state_store = state_store
        self.lock_path = lock_path

    async def sync(
        self,
        *,
        statuses: list[MarkStatus] | None = None,
        include_doulists: bool = True,
        force: bool = False,
        reason: Literal["manual", "scheduled", "startup"] = "manual",
    ) -> SyncResult:
        requested = statuses or ["wish", "collect"]
        today = datetime.now().astimezone().date().isoformat()
        previous = self.state_store.load()
        if not force and previous.last_success_local_date == today:
            return SyncResult(ok=True, skipped=True, reason="already_current")

        outcomes: dict[str, SyncStatusOutcome] = {}
        list_outcome: SyncStatusOutcome | None = None
        with acquire_process_lock(self.lock_path, timeout_seconds=0):
            checked = datetime.now().astimezone().isoformat()
            self.state_store.save(
                previous.model_copy(
                    update={"running": True, "last_checked_at": checked, "reason": reason}
                )
            )
            finalized = False
            try:
                for status in requested:
                    try:
                        items = await self.marks.refresh_baseline(status)
                        outcomes[status] = SyncStatusOutcome(
                            ok=True,
                            count=len(items),
                        )
                    except DoubanError as error:
                        outcomes[status] = SyncStatusOutcome(
                            ok=False,
                            error_code=error.code,
                            message=error.message,
                        )
                if include_doulists:
                    try:
                        result = await self.doulists.list_doulists(
                            limit=80,
                            refresh=True,
                            scope="sync",
                        )
                        list_outcome = SyncStatusOutcome(
                            ok=True,
                            count=len(result.data["items"]),
                        )
                    except DoubanError as error:
                        list_outcome = SyncStatusOutcome(
                            ok=False,
                            error_code=error.code,
                            message=error.message,
                        )

                success = all(outcome.ok for outcome in outcomes.values()) and (
                    list_outcome is None or list_outcome.ok
                )
                finished = datetime.now().astimezone().isoformat()
                self.state_store.save(
                    SyncState(
                        last_checked_at=checked,
                        last_success_at=(
                            finished if success else previous.last_success_at
                        ),
                        last_success_local_date=(
                            today if success else previous.last_success_local_date
                        ),
                        reason=reason,
                        running=False,
                        statuses={
                            name: outcome.model_dump(mode="json")
                            for name, outcome in outcomes.items()
                        },
                        last_error=(
                            "" if success else "one or more read operations failed"
                        ),
                    )
                )
                finalized = True
            finally:
                if not finalized:
                    interrupted = self.state_store.load()
                    self.state_store.save(
                        interrupted.model_copy(
                            update={
                                "running": False,
                                "last_error": (
                                    "synchronization interrupted before completion"
                                ),
                            }
                        )
                    )
        return SyncResult(
            ok=success,
            reason=reason,
            statuses=outcomes,
            doulists=list_outcome,
        )
