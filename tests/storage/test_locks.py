import pytest

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.storage.locks import acquire_process_lock


def test_second_process_lock_times_out_with_stable_error(tmp_path) -> None:
    path = tmp_path / "sync.lock"

    with (
        acquire_process_lock(path, timeout_seconds=0),
        pytest.raises(DoubanError, match="operation_in_progress"),
        acquire_process_lock(path, timeout_seconds=0),
    ):
        pass
