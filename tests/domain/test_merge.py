from cove_douban_mcp.domain.merge import mark_identity, merge_mark_items
from cove_douban_mcp.domain.models import MovieMark


def test_latest_present_fields_enrich_without_empty_value_erasure() -> None:
    existing = MovieMark(
        movie_id="100001",
        title="示例",
        countries=["示例甲地"],
        comment="保留的短评",
    )
    latest = MovieMark(
        movie_id="100001",
        title="示例",
        countries=[],
        genres=["喜剧"],
        comment="",
    )

    merged = merge_mark_items([existing], [latest])

    assert merged[0].countries == ["示例甲地"]
    assert merged[0].genres == ["喜剧"]
    assert merged[0].comment == "保留的短评"


def test_merge_preserves_existing_order_and_appends_new_items() -> None:
    existing = [
        MovieMark(movie_id="100001", title="甲"),
        MovieMark(movie_id="100002", title="乙"),
    ]
    latest = [
        MovieMark(movie_id="100002", title="乙 (更新)"),
        MovieMark(movie_id="100003", title="丙"),
    ]

    merged = merge_mark_items(existing, latest)

    assert [item.movie_id for item in merged] == ["100001", "100002", "100003"]
    assert merged[1].title == "乙 (更新)"


def test_identity_prefers_subject_id_then_url_then_normalized_title() -> None:
    assert mark_identity(MovieMark(movie_id="100001", title="任意")) == "id:100001"
    url_mark = MovieMark(url="https://example.invalid/subject/2", title="任意")
    assert mark_identity(url_mark).startswith("url:")
    assert mark_identity(MovieMark(title="  示例  影片 ")) == "title:示例 影片"
