from cove_douban_mcp.storage.query_cache import QueryCache


def test_expired_query_entry_is_not_returned(tmp_path) -> None:
    cache = QueryCache(tmp_path / "queries.json", clock=lambda: 200.0, ttl_seconds=100)
    cache.put("key", {"value": 1}, created_at=0.0)

    assert cache.get("key") is None
    assert cache.keys() == []


def test_cache_evicts_oldest_entry_over_limit(tmp_path) -> None:
    cache = QueryCache(tmp_path / "queries.json", max_entries=2, clock=lambda: 3.0)
    cache.put("a", 1, created_at=1)
    cache.put("b", 2, created_at=2)
    cache.put("c", 3, created_at=3)

    assert cache.keys() == ["b", "c"]


def test_cache_key_is_stable_for_parameter_order() -> None:
    first = QueryCache.make_key("search", {"type": "movie", "query": "示例"})
    second = QueryCache.make_key("search", {"query": "示例", "type": "movie"})

    assert first == second
    assert "示例" not in first

