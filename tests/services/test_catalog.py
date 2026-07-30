import pytest


@pytest.mark.asyncio
async def test_search_normalizes_and_caches_success(container, gateway) -> None:
    first = await container.catalog.search("虚构影片", media_type="movie", limit=5)
    second = await container.catalog.search("虚构影片", media_type="movie", limit=5)

    assert first.ok is True
    assert first.data["items"][0]["subject_id"] == "100001"
    assert first.result_ref
    assert second.source == "query_cache"
    assert len(gateway.calls) == 1


@pytest.mark.asyncio
async def test_subject_accepts_url_but_sends_only_numeric_id(container, gateway) -> None:
    result = await container.catalog.subject(
        "https://movie.example.invalid/subject/100001/",
        media_type="movie",
    )

    assert result.data["subject"]["title"] == "虚构影片"
    assert gateway.calls[0] == ("subject", ["100001", "--type", "movie"])

