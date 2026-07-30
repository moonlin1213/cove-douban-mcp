from cove_douban_mcp.storage.sync_state import SyncState, SyncStateStore


def test_missing_sync_state_uses_safe_defaults(tmp_path) -> None:
    state = SyncStateStore(tmp_path / "sync-state.json").load()

    assert state.running is False
    assert state.statuses == {}


def test_sync_state_round_trips(tmp_path) -> None:
    store = SyncStateStore(tmp_path / "sync-state.json")
    expected = SyncState(
        last_checked_at="2026-07-30T05:10:00+08:00",
        last_success_local_date="2026-07-30",
        reason="scheduled",
        statuses={"wish": {"ok": True}},
    )

    store.save(expected)

    assert store.load() == expected

