import pytest

from cove_douban_mcp.domain.errors import DoubanError


@pytest.mark.asyncio
async def test_chart_normalizes_fixed_board_and_caches_success(container, gateway) -> None:
    first = await container.charts.get("movie_weekly", limit=10, scope="client-a")
    second = await container.charts.get("movie_weekly", limit=10, scope="client-a")

    assert first.ok is True
    assert first.data == {
        "board_key": "movie_weekly",
        "board": "豆瓣电影一周口碑榜",
        "category": "movie",
        "items": [
            {
                "rank": 1,
                "subject_id": "100001",
                "title": "虚构榜单影片",
                "url": "https://movie.example.invalid/subject/100001/",
                "rating": 8.8,
                "rating_count": 12345,
                "year": 2026,
                "summary": "虚构导演 / 虚构演员",
                "trend": "",
                "chart_note": "连续上榜 2 周",
            }
        ],
    }
    assert first.source == "live"
    assert first.result_ref
    assert second.source == "query_cache"
    assert gateway.calls == [("chart", ["movie_weekly", "--limit", "10"])]


@pytest.mark.asyncio
async def test_chart_refresh_failure_returns_safe_cached_fallback(container, gateway) -> None:
    await container.charts.get("book_hot", limit=10)
    gateway.failures["chart"] = ("browser_bridge_unavailable", "bridge unavailable")

    result = await container.charts.get("book_hot", limit=10, refresh=True)

    assert result.ok is True
    assert result.source == "query_cache"
    assert result.freshness is not None and result.freshness.stale is True
    assert result.warning is not None
    assert result.warning.code == "browser_bridge_unavailable"


@pytest.mark.asyncio
async def test_chart_rejects_unknown_board_before_browser_call(container, gateway) -> None:
    with pytest.raises(DoubanError, match="invalid_argument"):
        await container.charts.get("https://example.invalid/chart")

    assert gateway.calls == []
