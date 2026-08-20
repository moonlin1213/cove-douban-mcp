import pytest

from cove_douban_mcp.opencli.gateway import OpenCLIResult


@pytest.mark.asyncio
async def test_partial_sync_does_not_report_all_success(container, gateway) -> None:
    original_run = gateway.run

    async def fail_collect(command: str, arguments: list[str]):
        if command == "marks" and "collect" in arguments:
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


@pytest.mark.asyncio
async def test_large_sync_uses_lightweight_bounded_chunks(container, gateway) -> None:
    rows = [
        {
            "movie_id": f"collect-{index:04d}",
            "title": f"虚构影片 {index}",
            "status": "collect",
        }
        for index in range(320)
    ]

    async def paged_run(command: str, arguments: list[str]) -> OpenCLIResult:
        gateway.calls.append((command, arguments))
        assert command == "marks"
        limit = int(arguments[arguments.index("--limit") + 1])
        offset = int(arguments[arguments.index("--offset") + 1])
        return OpenCLIResult(ok=True, rows=rows[offset : offset + limit])

    gateway.run = paged_run

    result = await container.sync.sync(
        statuses=["collect"],
        include_doulists=False,
        force=True,
    )

    assert result.ok is True
    assert result.statuses["collect"].count == 320
    assert [call[0] for call in gateway.calls] == ["marks", "marks", "marks"]
    assert [
        call[1][call[1].index("--offset") + 1] for call in gateway.calls
    ] == ["0", "150", "300"]
    assert len(container.marks_store.load().ids("collect")) == 320


@pytest.mark.asyncio
async def test_sync_accepts_an_empty_chunk_after_an_exact_page(container, gateway) -> None:
    rows = [
        {
            "movie_id": f"collect-{index:04d}",
            "title": f"虚构影片 {index}",
            "status": "collect",
        }
        for index in range(150)
    ]

    async def paged_run(command: str, arguments: list[str]) -> OpenCLIResult:
        gateway.calls.append((command, arguments))
        limit = int(arguments[arguments.index("--limit") + 1])
        offset = int(arguments[arguments.index("--offset") + 1])
        return OpenCLIResult(ok=True, rows=rows[offset : offset + limit])

    gateway.run = paged_run

    result = await container.sync.sync(
        statuses=["collect"],
        include_doulists=False,
        force=True,
    )

    assert result.ok is True
    assert result.statuses["collect"].count == 150
    assert len(gateway.calls) == 2


@pytest.mark.asyncio
async def test_unexpected_sync_failure_clears_running_state(container, gateway) -> None:
    async def explode(_command: str, _arguments: list[str]) -> OpenCLIResult:
        raise RuntimeError("synthetic unexpected failure")

    gateway.run = explode

    with pytest.raises(RuntimeError, match="synthetic unexpected failure"):
        await container.sync.sync(
            statuses=["collect"],
            include_doulists=False,
            force=True,
        )

    state = container.sync_state_store.load()
    assert state.running is False
    assert state.last_error == "synchronization interrupted before completion"
