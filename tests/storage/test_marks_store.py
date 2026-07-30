from cove_douban_mcp.domain.models import MovieMark
from cove_douban_mcp.storage.marks_store import MarksSnapshot, MarksStore


def snapshot_with_ids(*ids: str, status: str = "wish") -> MarksSnapshot:
    return MarksSnapshot(
        statuses={
            status: [
                MovieMark(movie_id=movie_id, title=f"虚构影片 {movie_id}", status=status)
                for movie_id in ids
            ]
        }
    )


def test_short_partial_save_cannot_shrink_long_disk_snapshot(tmp_path) -> None:
    store = MarksStore(tmp_path / "marks.json")
    store.save_protected(snapshot_with_ids("100001", "100002", "100003"))

    store.save_protected(snapshot_with_ids("100004"))

    assert store.load().ids("wish") == {"100001", "100002", "100003", "100004"}


def test_save_merges_each_status_independently(tmp_path) -> None:
    store = MarksStore(tmp_path / "marks.json")
    store.save_protected(snapshot_with_ids("100001", status="wish"))

    store.save_protected(snapshot_with_ids("200001", status="collect"))

    assert store.load().ids("wish") == {"100001"}
    assert store.load().ids("collect") == {"200001"}


def test_missing_store_loads_empty_snapshot(tmp_path) -> None:
    snapshot = MarksStore(tmp_path / "marks.json").load()

    assert snapshot.statuses == {}
