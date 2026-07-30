from datetime import datetime, timedelta, timezone

from cove_douban_mcp.config import SyncSettings
from cove_douban_mcp.services.scheduler import SyncScheduler
from cove_douban_mcp.storage.sync_state import SyncState, SyncStateStore

UTC_PLUS_8 = timezone(timedelta(hours=8))


def test_scheduler_is_due_after_local_target_time(tmp_path) -> None:
    state_store = SyncStateStore(tmp_path / "sync-state.json")
    scheduler = SyncScheduler(
        sync_service=None,
        settings=SyncSettings(enabled=True, local_time="05:10"),
        state_store=state_store,
    )
    now = datetime(2026, 7, 30, 5, 11, tzinfo=UTC_PLUS_8)

    assert scheduler.is_due(now) is True


def test_scheduler_is_not_due_before_target_or_after_success(tmp_path) -> None:
    state_store = SyncStateStore(tmp_path / "sync-state.json")
    scheduler = SyncScheduler(
        sync_service=None,
        settings=SyncSettings(enabled=True, local_time="05:10"),
        state_store=state_store,
    )
    early = datetime(2026, 7, 30, 5, 9, tzinfo=UTC_PLUS_8)
    assert scheduler.is_due(early) is False

    state_store.save(SyncState(last_success_local_date="2026-07-30"))
    later = datetime(2026, 7, 30, 8, 0, tzinfo=UTC_PLUS_8)
    assert scheduler.is_due(later) is False


def test_disabled_scheduler_is_never_due(tmp_path) -> None:
    scheduler = SyncScheduler(
        sync_service=None,
        settings=SyncSettings(enabled=False),
        state_store=SyncStateStore(tmp_path / "sync-state.json"),
    )

    assert scheduler.is_due(datetime.now().astimezone()) is False
