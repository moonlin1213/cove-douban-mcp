"""Markdown rendering and confined, recoverable writes."""

from __future__ import annotations

import os
import shutil
import tempfile
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Literal

from cove_douban_mcp.config import ExportPolicy
from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.domain.models import PublicModel
from cove_douban_mcp.export.proposals import ExportMode, ProposalStore
from cove_douban_mcp.export.sandbox import ExportSandbox
from cove_douban_mcp.storage.permissions import make_file_private
from cove_douban_mcp.storage.working_cache import WorkingCache

_START = "<!-- cove-douban-mcp:start -->"
_END = "<!-- cove-douban-mcp:end -->"


class ExportOutcome(PublicModel):
    code: Literal["write_confirmation_required", "export_completed"]
    proposal_id: str = ""
    path: str = ""
    bytes_written: int = 0


def _cell(value: Any) -> str:
    if isinstance(value, list):
        value = ", ".join(str(item) for item in value)
    elif isinstance(value, dict):
        value = ", ".join(f"{key}: {item}" for key, item in value.items())
    return str(value if value is not None else "").replace("\n", " ").replace("|", "\\|")


def render_markdown(rows: Sequence[Any], heading: str = "") -> str:
    normalized: list[dict[str, Any]] = []
    columns: list[str] = []
    for row in rows:
        model_dump = getattr(row, "model_dump", None)
        value = model_dump(mode="json") if callable(model_dump) else row
        if not isinstance(value, Mapping):
            value = {"value": value}
        mapping = dict(value)
        normalized.append(mapping)
        for key in mapping:
            if key not in columns:
                columns.append(str(key))

    lines = [_START]
    if heading.strip():
        lines.extend([f"# {heading.strip()}", ""])
    if not normalized:
        lines.append("_No items._")
    else:
        lines.append("| " + " | ".join(_cell(column) for column in columns) + " |")
        lines.append("| " + " | ".join("---" for _column in columns) + " |")
        for row in normalized:
            lines.append("| " + " | ".join(_cell(row.get(column, "")) for column in columns) + " |")
    lines.extend([_END, ""])
    return "\n".join(lines)


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        make_file_private(path)
    finally:
        temporary.unlink(missing_ok=True)


class ExportService:
    def __init__(
        self,
        *,
        working_cache: WorkingCache,
        proposal_store: ProposalStore,
        export_root: Path,
        policy: ExportPolicy,
        maximum_write_bytes: int,
    ) -> None:
        self.working_cache = working_cache
        self.proposal_store = proposal_store
        self.sandbox = ExportSandbox(export_root)
        self.policy = policy
        self.maximum_write_bytes = maximum_write_bytes

    def _render(self, scope: str, result_ref: str, heading: str) -> str:
        content = render_markdown(
            self.working_cache.load_complete(scope, result_ref),
            heading=heading,
        )
        if len(content.encode()) > self.maximum_write_bytes:
            raise DoubanError(
                "export_too_large",
                "the generated Markdown exceeds the configured write limit",
            )
        return content

    def _write(self, target: Path, content: str, mode: ExportMode) -> ExportOutcome:
        if mode == "create" and target.exists():
            raise DoubanError("export_conflict", "the target file already exists")

        final = content
        if mode == "append" and target.exists():
            existing = target.read_text(encoding="utf-8")
            final = f"{existing.rstrip()}\n\n{content}"
        elif mode == "replace":
            if not target.exists():
                raise DoubanError("export_conflict", "the target file does not exist")
            existing = target.read_text(encoding="utf-8")
            start = existing.find(_START)
            end = existing.find(_END, start + len(_START))
            if start < 0 or end < 0:
                raise DoubanError(
                    "export_conflict",
                    "the existing document has no recognized generated block",
                )
            end += len(_END)
            final = existing[:start] + content.rstrip() + existing[end:]
            backup = target.with_name(f"{target.name}.bak.{int(time.time())}")
            shutil.copy2(target, backup)
            make_file_private(backup)

        encoded = final.encode()
        if len(encoded) > self.maximum_write_bytes:
            raise DoubanError(
                "export_too_large",
                "the final Markdown file exceeds the configured write limit",
            )
        _atomic_write_text(target, final)
        return ExportOutcome(
            code="export_completed",
            path=str(target),
            bytes_written=len(encoded),
        )

    def request(
        self,
        scope: str,
        result_ref: str,
        path: str,
        *,
        mode: ExportMode = "create",
        heading: str = "",
    ) -> ExportOutcome:
        if mode not in {"create", "append", "replace"}:
            raise DoubanError(
                "invalid_argument",
                "export mode must be create, append, or replace",
            )
        if self.policy == ExportPolicy.OFF:
            raise DoubanError(
                "permission_required",
                "Markdown export is disabled",
                "A local user can enable it with the permissions command.",
            )
        target = self.sandbox.resolve_markdown(path)
        content = self._render(scope, result_ref, heading)
        if self.policy == ExportPolicy.CONFIRM_EACH:
            proposal = self.proposal_store.create(
                scope=scope,
                result_ref=result_ref,
                target=str(target),
                mode=mode,
                heading=heading,
            )
            return ExportOutcome(
                code="write_confirmation_required",
                proposal_id=proposal.proposal_id,
                path=str(target),
            )
        return self._write(target, content, mode)

    def approve_proposal(self, proposal_id: str) -> ExportOutcome:
        proposal = self.proposal_store.approve(proposal_id)
        target = self.sandbox.resolve_markdown(proposal.target)
        content = self._render(proposal.scope, proposal.result_ref, proposal.heading)
        outcome = self._write(target, content, proposal.mode)
        self.proposal_store.complete(proposal_id)
        return outcome
