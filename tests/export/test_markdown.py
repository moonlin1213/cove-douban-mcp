from pathlib import Path

import pytest

from cove_douban_mcp.config import ExportPolicy
from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.export.markdown import ExportService, render_markdown
from cove_douban_mcp.export.proposals import ProposalStore
from cove_douban_mcp.storage.working_cache import WorkingCache

ROWS = [
    {"title": "虚构 | 影片", "year": 2024, "genres": ["剧情", "喜剧"]},
    {"title": "第二部", "year": 2025, "genres": ["动画"]},
]


def export_service(tmp_path: Path, policy: ExportPolicy) -> tuple[ExportService, str]:
    cache = WorkingCache(tmp_path / "working")
    result_ref = cache.put("test-client", ROWS)
    service = ExportService(
        working_cache=cache,
        proposal_store=ProposalStore(tmp_path / "proposals"),
        export_root=tmp_path / "allowed",
        policy=policy,
        maximum_write_bytes=10_485_760,
    )
    return service, result_ref


def test_markdown_renderer_escapes_tables_and_formats_lists() -> None:
    rendered = render_markdown(ROWS, heading="示例清单")

    assert "# 示例清单" in rendered
    assert "虚构 \\| 影片" in rendered
    assert "剧情, 喜剧" in rendered


def test_off_policy_never_creates_proposal_or_file(tmp_path) -> None:
    service, result_ref = export_service(tmp_path, ExportPolicy.OFF)

    with pytest.raises(DoubanError, match="permission_required"):
        service.request("test-client", result_ref, "list.md")

    assert list(tmp_path.rglob("*.md")) == []
    assert list((tmp_path / "proposals").glob("*.json")) == []


def test_confirm_each_creates_proposal_without_writing(tmp_path) -> None:
    service, result_ref = export_service(tmp_path, ExportPolicy.CONFIRM_EACH)

    result = service.request("test-client", result_ref, "list.md", mode="create")

    assert result.code == "write_confirmation_required"
    assert result.proposal_id
    assert not (tmp_path / "allowed" / "list.md").exists()


def test_allow_in_root_writes_verified_server_side_result(tmp_path) -> None:
    service, result_ref = export_service(tmp_path, ExportPolicy.ALLOW_IN_ROOT)

    outcome = service.request("test-client", result_ref, "list.md", heading="私选")

    exported = tmp_path / "allowed" / "list.md"
    assert outcome.code == "export_completed"
    assert exported.exists()
    assert "第二部" in exported.read_text(encoding="utf-8")


def test_replace_requires_a_recognized_generated_block(tmp_path) -> None:
    service, result_ref = export_service(tmp_path, ExportPolicy.ALLOW_IN_ROOT)
    target = tmp_path / "allowed" / "list.md"
    target.parent.mkdir(parents=True)
    target.write_text("# User document\n", encoding="utf-8")

    with pytest.raises(DoubanError, match="export_conflict"):
        service.request("test-client", result_ref, "list.md", mode="replace")


def test_unknown_write_mode_is_rejected_before_writing(tmp_path) -> None:
    service, result_ref = export_service(tmp_path, ExportPolicy.ALLOW_IN_ROOT)

    with pytest.raises(DoubanError, match="invalid_argument"):
        service.request(
            "test-client",
            result_ref,
            "list.md",
            mode="truncate",  # type: ignore[arg-type]
        )

    assert not (tmp_path / "allowed" / "list.md").exists()
