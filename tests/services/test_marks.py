import pytest

from cove_douban_mcp.domain.models import MovieMark


@pytest.mark.asyncio
async def test_marks_uses_baseline_without_opencli_when_not_refreshing(
    container,
    gateway,
) -> None:
    container.marks_store.merge_status(
        "wish",
        [MovieMark(movie_id="100001", title="缓存喜剧", status="wish", genres=["喜剧"])],
    )

    result = await container.marks.list_marks(status="wish", genre="喜剧")

    assert result.source == "full_cache"
    assert gateway.calls == []


@pytest.mark.asyncio
async def test_refresh_failure_returns_stale_baseline(container, gateway) -> None:
    container.marks_store.merge_status(
        "wish",
        [MovieMark(movie_id="100001", title="缓存影片", status="wish")],
    )
    gateway.failures["marks-full"] = (
        "browser_bridge_unavailable",
        "Browser Bridge unavailable",
    )

    result = await container.marks.list_marks(status="wish", refresh=True)

    assert result.ok is True
    assert result.freshness.stale is True
    assert result.warning.code == "browser_bridge_unavailable"


@pytest.mark.asyncio
async def test_nonempty_uid_never_uses_current_user_baseline(container, gateway) -> None:
    container.marks_store.merge_status(
        "wish",
        [MovieMark(movie_id="private-baseline", title="本地缓存", status="wish")],
    )

    result = await container.marks.list_marks(status="wish", uid="public-example")

    assert gateway.calls[0][0] == "marks-full"
    assert "--uid" in gateway.calls[0][1]
    assert all(item["movie_id"] != "private-baseline" for item in result.data["items"])


@pytest.mark.asyncio
async def test_marks_filters_before_pagination(container) -> None:
    container.marks_store.merge_status(
        "wish",
        [
            MovieMark(movie_id="1", title="甲", status="wish", genres=["动画"]),
            MovieMark(movie_id="2", title="乙", status="wish", genres=["剧情"]),
            MovieMark(movie_id="3", title="丙", status="wish", genres=["动画"]),
        ],
    )

    result = await container.marks.list_marks(
        status="wish",
        genre="动画",
        offset=1,
        limit=1,
    )

    assert result.pagination.total == 2
    assert result.data["items"][0]["movie_id"] == "3"

