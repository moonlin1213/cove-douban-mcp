"""One-time, human-controlled export proposals."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Literal

from pydantic import Field

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.domain.models import PublicModel
from cove_douban_mcp.domain.result_refs import new_opaque_ref
from cove_douban_mcp.storage.atomic_json import atomic_write_json, read_json
from cove_douban_mcp.storage.permissions import make_file_private

ProposalStatus = Literal["pending", "approved", "rejected", "invalidated", "completed"]
ExportMode = Literal["create", "append", "replace"]
_ID_CHARACTERS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)


class ExportProposal(PublicModel):
    version: int = 1
    proposal_id: str
    scope: str = Field(exclude=True)
    result_ref: str
    target: str
    mode: ExportMode
    heading: str = ""
    status: ProposalStatus = "pending"
    created_at: float


class ProposalStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, proposal_id: str) -> Path:
        if not proposal_id or any(
            character not in _ID_CHARACTERS for character in proposal_id
        ):
            raise self._unavailable()
        return self.root / f"{proposal_id}.json"

    @staticmethod
    def _unavailable() -> DoubanError:
        return DoubanError(
            "proposal_unavailable",
            "the export proposal is unavailable or no longer pending",
        )

    def _save(self, proposal: ExportProposal) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self._path(proposal.proposal_id)
        payload = proposal.model_dump(mode="json")
        payload["scope"] = proposal.scope
        atomic_write_json(path, payload)
        make_file_private(path)

    def create(
        self,
        *,
        scope: str,
        result_ref: str,
        target: str,
        mode: ExportMode,
        heading: str,
    ) -> ExportProposal:
        proposal = ExportProposal(
            proposal_id=new_opaque_ref(),
            scope=scope,
            result_ref=result_ref,
            target=target,
            mode=mode,
            heading=heading,
            created_at=time.time(),
        )
        self._save(proposal)
        return proposal

    def load(self, proposal_id: str) -> ExportProposal:
        path = self._path(proposal_id)
        if not path.exists():
            raise self._unavailable()
        return ExportProposal.model_validate(read_json(path, default={}))

    def _transition(
        self,
        proposal_id: str,
        status: ProposalStatus,
        *,
        require_pending: bool = True,
    ) -> ExportProposal:
        proposal = self.load(proposal_id)
        if require_pending and proposal.status != "pending":
            raise self._unavailable()
        proposal.status = status
        self._save(proposal)
        return proposal

    def approve(self, proposal_id: str) -> ExportProposal:
        return self._transition(proposal_id, "approved")

    def reject(self, proposal_id: str) -> ExportProposal:
        return self._transition(proposal_id, "rejected")

    def complete(self, proposal_id: str) -> ExportProposal:
        proposal = self.load(proposal_id)
        if proposal.status != "approved":
            raise self._unavailable()
        proposal.status = "completed"
        self._save(proposal)
        return proposal

    def invalidate_all(self) -> int:
        count = 0
        if not self.root.exists():
            return count
        for path in self.root.glob("*.json"):
            proposal = ExportProposal.model_validate(read_json(path, default={}))
            if proposal.status == "pending":
                proposal.status = "invalidated"
                self._save(proposal)
                count += 1
        return count

    def list_pending(self) -> list[ExportProposal]:
        if not self.root.exists():
            return []
        return [
            proposal
            for path in sorted(self.root.glob("*.json"))
            if (proposal := ExportProposal.model_validate(read_json(path, default={}))).status
            == "pending"
        ]
