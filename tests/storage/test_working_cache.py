import pytest

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.storage.working_cache import WorkingCache

SYNTHETIC_ROWS = [
    {"movie_id": f"{index:06}", "title": f"虚构影片 {index}"}
    for index in range(1, 66)
]


def test_expired_reference_is_removed(tmp_path) -> None:
    current = [0.0]
    cache = WorkingCache(tmp_path, clock=lambda: current[0])
    result_ref = cache.put("client-a", SYNTHETIC_ROWS, created_at=0)
    current[0] = 90_000

    with pytest.raises(DoubanError, match="result_expired"):
        cache.read("client-a", result_ref, page=1, page_size=30)

    assert list(tmp_path.rglob(f"{result_ref}.json")) == []


def test_reference_is_scoped_to_client(tmp_path) -> None:
    cache = WorkingCache(tmp_path)
    result_ref = cache.put("client-a", SYNTHETIC_ROWS)

    with pytest.raises(DoubanError, match="result_expired"):
        cache.read("client-b", result_ref, page=1, page_size=30)


def test_page_read_returns_metadata_and_complete_total(tmp_path) -> None:
    cache = WorkingCache(tmp_path)
    result_ref = cache.put("client-a", SYNTHETIC_ROWS, metadata={"kind": "marks"})

    page = cache.read("client-a", result_ref, page=2, page_size=30)

    assert len(page.items) == 30
    assert page.items[0]["movie_id"] == "000031"
    assert page.pagination.total == 65
    assert page.pagination.next_offset == 60
    assert page.metadata == {"kind": "marks"}


def test_complete_read_is_for_server_side_export(tmp_path) -> None:
    cache = WorkingCache(tmp_path)
    result_ref = cache.put("client-a", SYNTHETIC_ROWS)

    assert len(cache.load_complete("client-a", result_ref)) == 65


def test_cache_evicts_oldest_reference_over_scope_limit(tmp_path) -> None:
    cache = WorkingCache(tmp_path, max_refs_per_scope=2, clock=lambda: 10.0)
    first = cache.put("client-a", [{"id": "1"}], created_at=1)
    cache.put("client-a", [{"id": "2"}], created_at=2)
    cache.put("client-a", [{"id": "3"}], created_at=3)

    with pytest.raises(DoubanError, match="result_expired"):
        cache.read("client-a", first, page=1, page_size=30)


def test_cache_rejects_oversized_reference(tmp_path) -> None:
    cache = WorkingCache(tmp_path, max_bytes_per_ref=64)

    with pytest.raises(DoubanError, match="result_too_large"):
        cache.put("client-a", [{"title": "x" * 200}])
