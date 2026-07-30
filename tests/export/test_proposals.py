import pytest

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.export.proposals import ProposalStore


def test_proposal_ids_are_random_and_single_use(tmp_path) -> None:
    store = ProposalStore(tmp_path)
    first = store.create(
        scope="client",
        result_ref="opaque-result",
        target="list.md",
        mode="create",
        heading="",
    )
    second = store.create(
        scope="client",
        result_ref="opaque-result",
        target="other.md",
        mode="create",
        heading="",
    )

    assert first.proposal_id != second.proposal_id
    approved = store.approve(first.proposal_id)
    assert approved.status == "approved"
    with pytest.raises(DoubanError, match="proposal_unavailable"):
        store.approve(first.proposal_id)


def test_reject_and_invalidate_make_proposals_unusable(tmp_path) -> None:
    store = ProposalStore(tmp_path)
    rejected = store.create(
        scope="client",
        result_ref="ref-a",
        target="a.md",
        mode="create",
        heading="",
    )
    pending = store.create(
        scope="client",
        result_ref="ref-b",
        target="b.md",
        mode="append",
        heading="",
    )

    store.reject(rejected.proposal_id)
    store.invalidate_all()

    assert store.load(rejected.proposal_id).status == "rejected"
    assert store.load(pending.proposal_id).status == "invalidated"
