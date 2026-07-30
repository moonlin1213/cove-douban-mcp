import pytest

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.domain.filters import MarkFilters, filter_movie_marks
from cove_douban_mcp.domain.models import MovieMark
from cove_douban_mcp.domain.pagination import paginate


def test_filter_runs_before_pagination() -> None:
    marks = [
        MovieMark(movie_id="100003", title="大陆动画", genres=["动画"]),
        MovieMark(movie_id="100004", title="海岛动画", genres=["动画"]),
        MovieMark(movie_id="100005", title="示例剧情", genres=["剧情"]),
    ]
    filtered = filter_movie_marks(marks, MarkFilters(genre="动画"))

    page, metadata = paginate(filtered, offset=1, limit=1)

    assert metadata.total == 2
    assert [item.movie_id for item in page] == ["100004"]


@pytest.mark.parametrize(
    ("offset", "limit"),
    [(-1, 30), (0, 0), (0, 201)],
)
def test_invalid_pagination_is_rejected(offset: int, limit: int) -> None:
    with pytest.raises(DoubanError, match="invalid_argument"):
        paginate([1, 2, 3], offset=offset, limit=limit)
