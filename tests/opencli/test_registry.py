import pytest

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.opencli.registry import ALLOWED_COMMANDS, validate_arguments


def test_registry_contains_only_the_eight_read_commands() -> None:
    assert set(ALLOWED_COMMANDS) == {
        "search",
        "chart",
        "subject",
        "marks",
        "marks-full",
        "reviews",
        "doulists",
        "doulist",
    }


def test_registry_rejects_unknown_command_and_flag() -> None:
    with pytest.raises(DoubanError, match="invalid_argument"):
        validate_arguments("download", ["--output", "outside"])
    with pytest.raises(DoubanError, match="invalid_argument"):
        validate_arguments("search", ["示例", "--eval", "script"])


def test_registry_accepts_documented_search_arguments() -> None:
    assert validate_arguments(
        "search",
        ["示例", "--type", "movie", "--limit", "10"],
    ) == ["示例", "--type", "movie", "--limit", "10"]


def test_registry_accepts_only_fixed_chart_arguments() -> None:
    assert validate_arguments(
        "chart",
        ["movie_weekly", "--limit", "10"],
    ) == ["movie_weekly", "--limit", "10"]

    with pytest.raises(DoubanError, match="invalid_argument"):
        validate_arguments("chart", ["https://example.invalid/chart"])
    with pytest.raises(DoubanError, match="invalid_argument"):
        validate_arguments("chart", ["movie_top250", "--start", "25"])
    with pytest.raises(DoubanError, match="invalid_argument"):
        validate_arguments("chart", ["movie_top250", "--limit", "251"])
