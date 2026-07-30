import pytest


@pytest.mark.asyncio
async def test_doulists_and_items_use_distinct_commands(container, gateway) -> None:
    lists = await container.doulists.list_doulists(kind="movie", limit=30)
    items = await container.doulists.list_items("400001", limit=40)

    assert lists.data["items"][0]["doulist_id"] == "400001"
    assert items.data["items"][0]["subject_id"] == "100001"
    assert [call[0] for call in gateway.calls] == ["doulists", "doulist"]

