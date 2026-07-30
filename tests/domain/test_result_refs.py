import base64

from cove_douban_mcp.domain.result_refs import new_opaque_ref


def test_reference_is_opaque_and_not_sequential() -> None:
    first = new_opaque_ref()
    second = new_opaque_ref()

    assert first != second
    assert len(base64.urlsafe_b64decode(first + "==")) >= 32
    assert first.replace("-", "").replace("_", "").isalnum()

