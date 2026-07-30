import pytest


@pytest.mark.asyncio
async def test_partial_sync_does_not_report_all_success(container, gateway) -> None:
    original_run = gateway.run

    async def fail_collect(command: str, arguments: list[str]):
        if command == "marks-full" and "collect" in arguments:
            gateway.calls.append((command, arguments))
            from cove_douban_mcp.opencli.gateway import OpenCLIResult

            return OpenCLIResult(
                ok=False,
                error_code="source_unavailable",
                safe_error="temporary source failure",
            )
        return await original_run(command, arguments)

    gateway.run = fail_collect

    result = await container.sync.sync(
        statuses=["wish", "collect"],
        include_doulists=False,
        force=True,
    )

    assert result.ok is False
    assert result.statuses["wish"].ok is True
    assert result.statuses["collect"].ok is False
    assert container.marks_store.load().ids("wish")
    assert container.marks_store.load().ids("collect") == set()

