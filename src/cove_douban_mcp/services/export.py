"""Application boundary for optional Markdown export."""

from __future__ import annotations

from cove_douban_mcp.domain.models import ToolEnvelope
from cove_douban_mcp.export.markdown import ExportService
from cove_douban_mcp.export.proposals import ExportMode


class ExportApplicationService:
    def __init__(self, exporter: ExportService) -> None:
        self.exporter = exporter

    async def request(
        self,
        *,
        scope: str,
        result_ref: str,
        path: str,
        mode: ExportMode = "create",
        heading: str = "",
    ) -> ToolEnvelope:
        outcome = self.exporter.request(
            scope,
            result_ref,
            path,
            mode=mode,
            heading=heading,
        )
        return ToolEnvelope(
            data=outcome.model_dump(mode="json"),
            source="local_export",
            result_ref=result_ref,
        )

