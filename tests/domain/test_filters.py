from cove_douban_mcp.domain.filters import (
    MarkFilters,
    filter_movie_marks,
    normalize_country_terms,
    parse_exclude_terms,
)
from cove_douban_mcp.domain.models import MovieMark

SYNTHETIC_MARKS = [
    MovieMark(
        movie_id="100001",
        title="春日喜剧",
        year=2022,
        countries=["中国香港"],
        genres=["剧情", "喜剧"],
        directors=["林示例"],
        casts=["演员甲"],
    ),
    MovieMark(
        movie_id="100002",
        title="不要这部",
        year=2023,
        countries=["中国香港"],
        genres=["喜剧"],
    ),
    MovieMark(
        movie_id="100003",
        title="大陆动画",
        year=2020,
        countries=["中国大陆"],
        genres=["动画"],
    ),
    MovieMark(
        movie_id="100004",
        title="海岛动画",
        year=2021,
        countries=["泰国"],
        genres=["动画"],
    ),
]


def test_filter_combines_country_genre_year_and_exclusion() -> None:
    filters = MarkFilters(
        country="香港",
        genre="喜剧",
        year_from=2020,
        exclude="不要这部",
    )

    result = filter_movie_marks(SYNTHETIC_MARKS, filters)

    assert [item.movie_id for item in result] == ["100001"]


def test_country_alias_uses_longest_match_without_short_substring_collision() -> None:
    assert normalize_country_terms("中国香港或泰国") == ("中国香港", "泰国")


def test_country_filter_is_or_across_requested_terms() -> None:
    result = filter_movie_marks(
        SYNTHETIC_MARKS,
        MarkFilters(country="国产、泰国"),
    )

    assert [item.movie_id for item in result] == ["100003", "100004"]


def test_query_matches_people_and_metadata_case_insensitively() -> None:
    result = filter_movie_marks(SYNTHETIC_MARKS, MarkFilters(query="演员甲"))

    assert [item.movie_id for item in result] == ["100001"]


def test_exclusion_parser_accepts_strings_and_sequences() -> None:
    assert parse_exclude_terms("甲, 乙；丙") == ("甲", "乙", "丙")  # noqa: RUF001
    assert parse_exclude_terms(["甲", " 乙 ", ""]) == ("甲", "乙")
