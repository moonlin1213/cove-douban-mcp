import pytest


@pytest.mark.asyncio
async def test_reviews_return_normalized_items_and_reference(container) -> None:
    result = await container.reviews.list_reviews(limit=20)

    assert result.data["items"][0]["review_id"] == "300001"
    assert result.result_ref

