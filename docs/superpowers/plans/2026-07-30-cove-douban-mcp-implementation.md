# Cove Douban MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the standalone, privacy-safe `cove-douban-mcp` v0.1.0 package with the complete approved read-only Douban capability set, standard MCP transports, isolated OpenCLI integration, durable local caching, and optional sandboxed Markdown export.

**Architecture:** A pure Python domain layer owns normalization, filtering, pagination, merge protection, and result references. Application services orchestrate injected storage and an allowlisted OpenCLI subprocess gateway. A thin MCP layer exposes the same structured tools over stdio and authenticated loopback-only Streamable HTTP; a separate CLI owns setup, diagnostics, permissions, approvals, and uninstall.

**Tech Stack:** Python 3.11–3.13, MCP Python SDK 1.28.x, Pydantic 2, `platformdirs`, `filelock`, `tomli-w`, pytest, pytest-asyncio, Ruff, mypy, Node.js 22 for the OpenCLI plugin, GitHub Actions.

## Global Constraints

- Work only in the standalone `cove-douban-mcp` repository; never modify or import the private source application.
- Support macOS and Windows; Linux behavior may work but is not a v0.1.0 release guarantee.
- Keep every Douban operation read-only.
- Expose exactly the 11 approved v0.1.0 MCP tools over both stdio and loopback-only Streamable HTTP.
- Bind HTTP only to `127.0.0.1`, `localhost`, or `::1`; require Bearer authentication and explicit Origin validation.
- Keep internal application data under `platformdirs` paths or an injected test root.
- Keep Markdown export disabled by default; an enabled export remains confined to one user-selected root.
- Never store or expose Douban passwords, cookies, browser credentials, private account data, maintainer paths, or real personal fixtures.
- Do not run public-user setup, plugin installation, or live private-account tests against the maintainer's current environment.
- Use a temporary OpenCLI configuration and a fake OpenCLI executable in automated tests.
- Use strict TDD for production behavior: write and observe a focused failing test before implementation.
- Use Apache License 2.0 and retain required third-party notices.
- Pin reproducible development dependencies in `uv.lock`; runtime requirements remain bounded by tested major versions.

---

### Task 1: Package Foundation, Public Metadata, and Shared Models

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `.gitignore`
- Create: `src/cove_douban_mcp/__init__.py`
- Create: `src/cove_douban_mcp/domain/__init__.py`
- Create: `src/cove_douban_mcp/domain/models.py`
- Create: `src/cove_douban_mcp/domain/errors.py`
- Create: `tests/test_public_package.py`
- Create: `tests/domain/test_models.py`

**Interfaces:**
- Produces: `__version__: str`
- Produces: `SourceFreshness`, `Pagination`, `ToolError`, `ToolEnvelope`, `MovieMark`, `SearchResult`, `Subject`, `Review`, `Doulist`, and `DoulistItem` Pydantic models.
- Produces: `DoubanError(code: str, message: str, action: str = "")`.
- Consumes: no project code.

- [ ] **Step 1: Write failing package and model tests**

```python
from cove_douban_mcp import __version__
from cove_douban_mcp.domain.models import MovieMark, Pagination


def test_public_version_is_initial_release():
    assert __version__ == "0.1.0"


def test_pagination_exposes_terminal_state():
    page = Pagination(total=42, offset=30, limit=30, returned=12)
    assert page.has_more is False
    assert page.next_offset is None


def test_movie_mark_rejects_empty_identity():
    with pytest.raises(ValueError):
        MovieMark(title="", movie_id="", url="")
```

- [ ] **Step 2: Run tests and verify they fail because the package and models do not exist**

Run:

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/test_public_package.py tests/domain/test_models.py -q
```

Expected: import failures for `cove_douban_mcp`.

- [ ] **Step 3: Add the package metadata and minimal models**

Use these bounded runtime dependencies:

```toml
[project]
name = "cove-douban-mcp"
version = "0.1.0"
requires-python = ">=3.11,<3.14"
dependencies = [
  "mcp>=1.28.1,<2",
  "pydantic>=2.11,<3",
  "platformdirs>=4.3,<5",
  "filelock>=3.18,<4",
  "tomli-w>=1.2,<2",
]

[dependency-groups]
dev = [
  "build>=1.2,<2",
  "mypy>=1.17,<2",
  "pytest>=8.4,<9",
  "pytest-asyncio>=1.1,<2",
  "ruff>=0.12,<1",
  "twine>=6.1,<7",
]

[project.scripts]
cove-douban-mcp = "cove_douban_mcp.cli:main"
```

Implement derived `Pagination.has_more` and `Pagination.next_offset`
properties, and require at least one of `movie_id`, `url`, or non-empty
`title` in `MovieMark`. Configure the build backend so the Python package
uses the `src/` layout and the standalone OpenCLI plugin is force-included
inside the wheel as `cove_douban_mcp/opencli_plugin/`.

- [ ] **Step 4: Run focused tests and verify they pass**

Run:

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/test_public_package.py tests/domain/test_models.py -q
```

Expected: all focused tests pass.

- [ ] **Step 5: Create and inspect the dependency lock**

Run:

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv lock --python 3.13
UV_CACHE_DIR="$PWD/.uv-cache" uv sync --python 3.13 --all-groups
```

Expected: `uv.lock` exists and resolves only stable MCP 1.x.

- [ ] **Step 6: Commit the foundation**

```bash
git add pyproject.toml uv.lock .python-version .gitignore src tests
git commit -m "build: initialize standalone MCP package"
```

---

### Task 2: Movie-Mark Normalization, Filtering, and Pagination

**Files:**
- Create: `src/cove_douban_mcp/domain/filters.py`
- Create: `src/cove_douban_mcp/domain/pagination.py`
- Create: `tests/domain/test_filters.py`
- Create: `tests/domain/test_pagination.py`

**Interfaces:**
- Consumes: `MovieMark`, `Pagination`.
- Produces: `normalize_country_terms(value: str) -> tuple[str, ...]`.
- Produces: `parse_exclude_terms(value: str | Sequence[str]) -> tuple[str, ...]`.
- Produces: `filter_movie_marks(items: Sequence[MovieMark], filters: MarkFilters) -> list[MovieMark]`.
- Produces: `paginate(items: Sequence[T], offset: int, limit: int) -> tuple[list[T], Pagination]`.
- Produces: immutable `MarkFilters`.

- [ ] **Step 1: Write failing filter tests with synthetic movies**

```python
def test_filter_combines_country_genre_year_and_exclusion():
    filters = MarkFilters(
        country="示例甲地",
        genre="喜剧",
        year_from=2020,
        exclude="不要这部",
    )
    result = filter_movie_marks(SYNTHETIC_MARKS, filters)
    assert [item.movie_id for item in result] == ["100001"]


def test_country_alias_uses_longest_match_without_short_substring_collision():
    assert normalize_country_terms("中国香港或泰国") == ("中国香港", "泰国")


def test_filter_runs_before_pagination():
    filtered = filter_movie_marks(SYNTHETIC_MARKS, MarkFilters(genre="动画"))
    page, metadata = paginate(filtered, offset=1, limit=1)
    assert metadata.total == 2
    assert [item.movie_id for item in page] == ["100004"]
```

- [ ] **Step 2: Run focused tests and verify expected missing-symbol failures**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/domain/test_filters.py tests/domain/test_pagination.py -q
```

- [ ] **Step 3: Implement strict filtering and pagination**

Implementation rules:

```python
COUNTRY_ALIASES = {
    "大陆": "中国大陆",
    "国产": "中国大陆",
    "香港": "中国香港",
    "台湾": "中国台湾",
}
```

Apply exclusion, full-field query, genre, country OR, director, cast, and
year bounds in that order. Validate `offset >= 0` and `1 <= limit <= 200`
instead of silently clamping invalid external input.

- [ ] **Step 4: Run focused tests and verify green**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/domain/test_filters.py tests/domain/test_pagination.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/cove_douban_mcp/domain tests/domain
git commit -m "feat: add deterministic marks filtering and pagination"
```

---

### Task 3: Non-shrinking Merge and Durable Marks Store

**Files:**
- Create: `src/cove_douban_mcp/domain/merge.py`
- Create: `src/cove_douban_mcp/storage/__init__.py`
- Create: `src/cove_douban_mcp/storage/atomic_json.py`
- Create: `src/cove_douban_mcp/storage/marks_store.py`
- Create: `tests/domain/test_merge.py`
- Create: `tests/storage/test_marks_store.py`

**Interfaces:**
- Consumes: `MovieMark`.
- Produces: `mark_identity(mark: MovieMark) -> str`.
- Produces: `merge_mark_items(existing, latest) -> list[MovieMark]`.
- Produces: `MarksSnapshot`.
- Produces: `MarksStore(path: Path).load()`, `.merge_status()`, and `.save_protected()`.

- [ ] **Step 1: Write failing merge and persistence tests**

```python
def test_latest_present_fields_enrich_without_empty_value_erasure():
    existing = MovieMark(movie_id="100001", title="示例", countries=["示例甲地"])
    latest = MovieMark(movie_id="100001", title="示例", countries=[], genres=["喜剧"])
    merged = merge_mark_items([existing], [latest])
    assert merged[0].countries == ["示例甲地"]
    assert merged[0].genres == ["喜剧"]


def test_short_partial_save_cannot_shrink_long_disk_snapshot(tmp_path):
    store = MarksStore(tmp_path / "marks.json")
    store.save_protected(snapshot_with_ids("100001", "100002", "100003"))
    store.save_protected(snapshot_with_ids("100004"))
    assert store.load().ids("wish") == {"100001", "100002", "100003", "100004"}
```

- [ ] **Step 2: Run tests and verify red**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/domain/test_merge.py tests/storage/test_marks_store.py -q
```

- [ ] **Step 3: Implement atomic JSON writes and defensive merge-on-save**

Write a temporary sibling file, flush and fsync it, and atomically replace
the destination. Before saving a baseline, reload the current disk
snapshot and merge each status so a partial response cannot remove
history.

- [ ] **Step 4: Run focused tests and verify green**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/domain/test_merge.py tests/storage/test_marks_store.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/cove_douban_mcp/domain src/cove_douban_mcp/storage tests/domain tests/storage
git commit -m "feat: protect durable movie-mark baselines"
```

---

### Task 4: Cross-platform Paths, Query Cache, Sync State, and Locks

**Files:**
- Create: `src/cove_douban_mcp/storage/paths.py`
- Create: `src/cove_douban_mcp/storage/query_cache.py`
- Create: `src/cove_douban_mcp/storage/sync_state.py`
- Create: `src/cove_douban_mcp/storage/locks.py`
- Create: `tests/storage/test_paths.py`
- Create: `tests/storage/test_query_cache.py`
- Create: `tests/storage/test_sync_state.py`
- Create: `tests/storage/test_locks.py`

**Interfaces:**
- Produces: `AppPaths.from_root(root: Path)` and `AppPaths.platform_default()`.
- Produces: `QueryCache(path, ttl_seconds=21600, max_entries=80)`.
- Produces: `SyncStateStore(path)`.
- Produces: `acquire_process_lock(path, timeout_seconds)`.

- [ ] **Step 1: Write failing cross-platform storage tests**

```python
def test_expired_query_entry_is_not_returned(tmp_path):
    cache = QueryCache(tmp_path / "queries.json", clock=lambda: 200.0)
    cache.put("key", {"value": 1}, created_at=0.0)
    assert cache.get("key") is None


def test_cache_evicts_oldest_entry_over_limit(tmp_path):
    cache = QueryCache(tmp_path / "queries.json", max_entries=2)
    cache.put("a", 1, created_at=1)
    cache.put("b", 2, created_at=2)
    cache.put("c", 3, created_at=3)
    assert cache.keys() == ["b", "c"]
```

- [ ] **Step 2: Run focused tests and verify red**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/storage/test_paths.py tests/storage/test_query_cache.py tests/storage/test_sync_state.py tests/storage/test_locks.py -q
```

- [ ] **Step 3: Implement storage paths, bounded TTL cache, state, and file locks**

Test roots are always injected. `platform_default()` is the only method
that calls `platformdirs.user_data_path`.

- [ ] **Step 4: Run focused tests and verify green**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/storage -q
```

- [ ] **Step 5: Commit**

```bash
git add src/cove_douban_mcp/storage tests/storage
git commit -m "feat: add isolated cross-platform storage"
```

---

### Task 5: Opaque Result References and Working Cache

**Files:**
- Create: `src/cove_douban_mcp/domain/result_refs.py`
- Create: `src/cove_douban_mcp/storage/working_cache.py`
- Create: `tests/domain/test_result_refs.py`
- Create: `tests/storage/test_working_cache.py`

**Interfaces:**
- Produces: `new_opaque_ref() -> str` with at least 256 bits of entropy.
- Produces: `WorkingCache.put(scope, items, metadata) -> str`.
- Produces: `WorkingCache.read(scope, result_ref, page, page_size)`.
- Produces: `WorkingCache.load_complete(scope, result_ref)`.

- [ ] **Step 1: Write failing result-reference tests**

```python
def test_reference_is_opaque_and_not_sequential():
    first = new_opaque_ref()
    second = new_opaque_ref()
    assert first != second
    assert len(base64.urlsafe_b64decode(first + "==")) >= 32


def test_expired_reference_is_removed(tmp_path):
    cache = WorkingCache(tmp_path, clock=lambda: 90_000)
    ref = cache.put("client-a", SYNTHETIC_ROWS, created_at=0)
    with pytest.raises(DoubanError, match="result_expired"):
        cache.read("client-a", ref, page=1, page_size=30)
```

- [ ] **Step 2: Run focused tests and verify red**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/domain/test_result_refs.py tests/storage/test_working_cache.py -q
```

- [ ] **Step 3: Implement scoped, expiring, bounded working cache**

Use hashed scope-directory names, 16 active references per scope, 8 MiB
per reference, and 64 MiB total per scope. Never encode filters, user IDs,
or paths into the reference.

- [ ] **Step 4: Run tests and verify green**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/domain/test_result_refs.py tests/storage/test_working_cache.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/cove_douban_mcp/domain src/cove_douban_mcp/storage tests
git commit -m "feat: add opaque result working cache"
```

---

### Task 6: Export Configuration, Sandboxed Markdown, and Human Proposals

**Files:**
- Create: `src/cove_douban_mcp/config.py`
- Create: `src/cove_douban_mcp/storage/permissions.py`
- Create: `src/cove_douban_mcp/export/__init__.py`
- Create: `src/cove_douban_mcp/export/markdown.py`
- Create: `src/cove_douban_mcp/export/sandbox.py`
- Create: `src/cove_douban_mcp/export/proposals.py`
- Create: `tests/test_config.py`
- Create: `tests/export/test_markdown.py`
- Create: `tests/export/test_sandbox.py`
- Create: `tests/export/test_proposals.py`

**Interfaces:**
- Produces: `Settings.load(path)` and `.save(path)`.
- Produces: `ExportPolicy.OFF`, `.CONFIRM_EACH`, `.ALLOW_IN_ROOT`.
- Produces: `ExportSandbox.resolve_markdown(relative_or_absolute: str) -> Path`.
- Produces: `render_markdown(result, heading) -> str`.
- Produces: `ProposalStore.create()`, `.approve()`, `.reject()`, `.invalidate_all()`.

- [ ] **Step 1: Write failing permission and sandbox tests**

```python
def test_export_is_disabled_by_default(tmp_path):
    settings = Settings.default(tmp_path)
    assert settings.export.enabled is False
    assert settings.export.policy == ExportPolicy.OFF


def test_parent_escape_is_rejected(tmp_path):
    sandbox = ExportSandbox(tmp_path / "allowed")
    with pytest.raises(DoubanError, match="path_outside_root"):
        sandbox.resolve_markdown("../outside.md")


def test_confirm_each_creates_proposal_without_writing(tmp_path):
    service = export_service(tmp_path, policy=ExportPolicy.CONFIRM_EACH)
    result = service.request(REF, "list.md", mode="create")
    assert result.code == "write_confirmation_required"
    assert not (tmp_path / "allowed" / "list.md").exists()
```

- [ ] **Step 2: Run focused tests and verify red**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/test_config.py tests/export -q
```

- [ ] **Step 3: Implement configuration, sandbox, rendering, and proposals**

Proposal approval requires an out-of-band CLI method; no MCP tool is
allowed to call `ProposalStore.approve`. Proposal IDs are random,
single-use, and invalidated when export permissions change.

- [ ] **Step 4: Add platform escape regression tests**

Add tests for a POSIX symlink escape and a Windows junction/reparse-point
guard abstraction. The Windows CI test must execute the Windows-specific
branch.

- [ ] **Step 5: Run tests and verify green**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/test_config.py tests/export -q
```

- [ ] **Step 6: Commit**

```bash
git add src/cove_douban_mcp/config.py src/cove_douban_mcp/storage src/cove_douban_mcp/export tests
git commit -m "feat: add opt-in sandboxed Markdown export"
```

---

### Task 7: Allowlisted OpenCLI Gateway and Result Parsing

**Files:**
- Create: `src/cove_douban_mcp/opencli/__init__.py`
- Create: `src/cove_douban_mcp/opencli/registry.py`
- Create: `src/cove_douban_mcp/opencli/parser.py`
- Create: `src/cove_douban_mcp/opencli/gateway.py`
- Create: `src/cove_douban_mcp/opencli/diagnostics.py`
- Create: `tests/fixtures/fake_opencli.py`
- Create: `tests/opencli/test_registry.py`
- Create: `tests/opencli/test_parser.py`
- Create: `tests/opencli/test_gateway.py`
- Create: `tests/opencli/test_diagnostics.py`

**Interfaces:**
- Produces: `ALLOWED_COMMANDS`.
- Produces: `OpenCLIResult`.
- Produces: `OpenCLIGateway(binary, timeout_seconds).run(command, args)`.
- Produces: `OpenCLIDiagnostics.check()`.

- [ ] **Step 1: Write failing subprocess-boundary tests**

```python
@pytest.mark.asyncio
async def test_gateway_rejects_non_allowlisted_command(fake_opencli):
    gateway = OpenCLIGateway(fake_opencli)
    with pytest.raises(DoubanError, match="invalid_argument"):
        await gateway.run("download", ["--output", "outside"])


@pytest.mark.asyncio
async def test_gateway_parses_json_without_shell(fake_opencli):
    gateway = OpenCLIGateway(fake_opencli)
    result = await gateway.run("search", ["示例", "--type", "movie"])
    assert result.rows[0]["title"] == "示例影片"


@pytest.mark.asyncio
async def test_gateway_redacts_sensitive_stderr(fake_opencli_sensitive_error):
    result = await gateway.run("search", ["error"])
    assert "cookie" not in result.safe_error.lower()
    assert "token" not in result.safe_error.lower()
```

- [ ] **Step 2: Run focused tests and verify red**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/opencli -q
```

- [ ] **Step 3: Implement argument-array subprocess execution**

Build:

```python
[
    binary,
    "douban",
    command,
    *validated_args,
    "--site-session",
    "persistent",
    "--window",
    "background",
    "-f",
    "json",
]
```

Use `asyncio.create_subprocess_exec`, never a shell. Map known bridge,
login, timeout, malformed-output, and source-shape failures to stable
domain errors.

- [ ] **Step 4: Run focused tests and verify green**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/opencli -q
```

- [ ] **Step 5: Commit**

```bash
git add src/cove_douban_mcp/opencli tests/opencli tests/fixtures
git commit -m "feat: add allowlisted OpenCLI gateway"
```

---

### Task 8: Application Services for the Complete Douban Capability Set

**Files:**
- Create: `src/cove_douban_mcp/services/__init__.py`
- Create: `src/cove_douban_mcp/services/catalog.py`
- Create: `src/cove_douban_mcp/services/marks.py`
- Create: `src/cove_douban_mcp/services/reviews.py`
- Create: `src/cove_douban_mcp/services/doulists.py`
- Create: `src/cove_douban_mcp/services/sync.py`
- Create: `src/cove_douban_mcp/services/status.py`
- Create: `src/cove_douban_mcp/services/container.py`
- Create: `tests/services/test_catalog.py`
- Create: `tests/services/test_marks.py`
- Create: `tests/services/test_reviews.py`
- Create: `tests/services/test_doulists.py`
- Create: `tests/services/test_sync.py`
- Create: `tests/services/test_status.py`

**Interfaces:**
- Consumes: domain models, stores, working cache, OpenCLI gateway.
- Produces: `ServiceContainer`.
- Produces: `CatalogService.search()` and `.subject()`.
- Produces: `MarksService.list_marks()` and `.profile()`.
- Produces: `ReviewsService.list_reviews()`.
- Produces: `DoulistsService.list_doulists()` and `.list_items()`.
- Produces: `SyncService.sync()`.
- Produces: `StatusService.status()`.

- [ ] **Step 1: Write failing cache-first and fallback service tests**

```python
@pytest.mark.asyncio
async def test_marks_uses_baseline_without_opencli_when_not_refreshing(container):
    result = await container.marks.list_marks(status="wish", genre="喜剧")
    assert result.source == "full_cache"
    assert container.gateway.calls == []


@pytest.mark.asyncio
async def test_refresh_failure_returns_stale_baseline(container_with_failing_gateway):
    result = await container_with_failing_gateway.marks.list_marks(
        status="wish",
        refresh=True,
    )
    assert result.ok is True
    assert result.freshness.stale is True
    assert result.warning.code == "browser_bridge_unavailable"


@pytest.mark.asyncio
async def test_nonempty_uid_never_uses_current_user_baseline(container):
    await container.marks.list_marks(status="wish", uid="public-example")
    assert container.gateway.calls[0].command == "marks"
```

- [ ] **Step 2: Run service tests and verify red**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/services -q
```

- [ ] **Step 3: Implement catalog, marks, reviews, and doulists services**

Every successful list service stores the complete verified normalized
result in `WorkingCache` and returns one page plus a `result_ref`.

- [ ] **Step 4: Add failing sync-lock and partial-failure tests**

```python
@pytest.mark.asyncio
async def test_partial_sync_does_not_report_all_success(sync_service):
    result = await sync_service.sync(statuses=["wish", "collect"])
    assert result.ok is False
    assert result.statuses["wish"].ok is True
    assert result.statuses["collect"].ok is False
```

- [ ] **Step 5: Implement due checks, startup catch-up, manual sync, and locks**

Use no LLM. Merge successful statuses into the durable baseline and leave
failed statuses unchanged.

- [ ] **Step 6: Run all service tests and verify green**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/services -q
```

- [ ] **Step 7: Commit**

```bash
git add src/cove_douban_mcp/services tests/services
git commit -m "feat: add complete Douban application services"
```

---

### Task 9: MCP Tool Registration and Identical Structured Transports

**Files:**
- Create: `src/cove_douban_mcp/mcp/__init__.py`
- Create: `src/cove_douban_mcp/mcp/tools.py`
- Create: `src/cove_douban_mcp/mcp/server.py`
- Create: `src/cove_douban_mcp/mcp/auth.py`
- Create: `src/cove_douban_mcp/mcp/transport.py`
- Create: `tests/mcp/test_tools.py`
- Create: `tests/mcp/test_stdio.py`
- Create: `tests/mcp/test_http.py`

**Interfaces:**
- Consumes: `ServiceContainer`.
- Produces: `create_mcp_server(container) -> FastMCP`.
- Produces: `validate_loopback_host(host: str)`.
- Produces: `LocalBearerAuth`.
- Produces: `run_stdio()` and `run_streamable_http()`.

- [ ] **Step 1: Write failing tool-catalog test**

```python
EXPECTED_TOOLS = {
    "douban_status",
    "douban_search",
    "douban_subject",
    "douban_movie_marks",
    "douban_reviews",
    "douban_movie_profile",
    "douban_doulists",
    "douban_doulist_items",
    "douban_sync",
    "douban_working_cache_read",
    "douban_export_markdown",
}


@pytest.mark.asyncio
async def test_server_exposes_exact_v010_tool_surface(test_server):
    tools = await list_tools(test_server)
    assert {tool.name for tool in tools} == EXPECTED_TOOLS
```

- [ ] **Step 2: Run test and verify red**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/mcp/test_tools.py -q
```

- [ ] **Step 3: Implement thin FastMCP tool handlers**

Each handler validates typed arguments, calls exactly one application
service method, and returns the shared structured envelope. It contains
no cache, OpenCLI, export, or provider logic.

- [ ] **Step 4: Write and run failing stdio protocol test**

Start the installed command as a subprocess with an injected temporary
data root and fake OpenCLI. Initialize through the official client,
list tools, call `douban_status`, and assert stderr-only logs.

- [ ] **Step 5: Implement stdio transport and verify green**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/mcp/test_stdio.py -q
```

- [ ] **Step 6: Write failing local HTTP security tests**

Assert:

- missing Bearer token is rejected;
- bad Origin is rejected;
- configured Origin and token initialize successfully;
- non-loopback host fails before bind.

- [ ] **Step 7: Implement authenticated loopback Streamable HTTP**

Wrap the MCP Streamable HTTP application with explicit Bearer and Origin
validation. Do not provide a `--no-auth` production flag.

- [ ] **Step 8: Run all MCP tests and verify green**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/mcp -q
```

- [ ] **Step 9: Commit**

```bash
git add src/cove_douban_mcp/mcp tests/mcp
git commit -m "feat: expose standard local MCP transports"
```

---

### Task 10: CLI Setup, Doctor, Permissions, Approval, and Uninstall

**Files:**
- Create: `src/cove_douban_mcp/opencli/plugin_installer.py`
- Create: `src/cove_douban_mcp/cli.py`
- Create: `tests/install/test_setup.py`
- Create: `tests/install/test_doctor.py`
- Create: `tests/install/test_permissions.py`
- Create: `tests/install/test_uninstall.py`

**Interfaces:**
- Produces CLI commands: `setup`, `serve`, `doctor`, `permissions`,
  `cache`, `export`, `print-config`, and `uninstall`.
- Produces: `SetupPlan`.
- Produces: `PluginInstaller`.

- [ ] **Step 1: Write failing dry-run and conflict tests**

```python
def test_setup_dry_run_has_no_filesystem_side_effects(cli_runner, isolated_env):
    result = cli_runner("setup", "--dry-run")
    assert result.exit_code == 0
    assert isolated_env.changed_paths() == set()


def test_existing_user_adapter_stops_default_install(cli_runner, isolated_env):
    isolated_env.create_user_adapter("douban/search.js")
    result = cli_runner("setup", "--yes")
    assert result.exit_code != 0
    assert "existing adapter" in result.stderr.lower()
```

- [ ] **Step 2: Run install tests and verify red**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/install -q
```

- [ ] **Step 3: Implement standard-library argparse CLI and setup planning**

Every mutating setup action is represented in `SetupPlan`; dry-run
renders it and exits. Interactive setup asks before plugin install,
client-config change, export enablement, and replacement.

- [ ] **Step 4: Implement doctor and generic configuration output**

`print-config` emits generic stdio and HTTP examples. Known-client helpers
remain optional conveniences; unknown standards-compliant clients require
no code change.

- [ ] **Step 5: Implement export approval and uninstall semantics**

Default uninstall preserves application data and exported Markdown.
`--purge-data` requires a second confirmation and still cannot remove
exported Markdown.

- [ ] **Step 6: Run CLI tests and verify green**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/install -q
```

- [ ] **Step 7: Commit**

```bash
git add src/cove_douban_mcp/cli.py src/cove_douban_mcp/opencli tests/install
git commit -m "feat: add explicit cross-platform setup and permissions CLI"
```

---

### Task 11: Standalone OpenCLI Douban Plugin

**Files:**
- Create: `opencli-plugin/package.json`
- Create: `opencli-plugin/opencli.plugin.json`
- Create: `opencli-plugin/clis/douban/search.js`
- Create: `opencli-plugin/clis/douban/subject.js`
- Create: `opencli-plugin/clis/douban/marks.js`
- Create: `opencli-plugin/clis/douban/marks-full.js`
- Create: `opencli-plugin/clis/douban/reviews.js`
- Create: `opencli-plugin/clis/douban/doulists.js`
- Create: `opencli-plugin/clis/douban/doulist.js`
- Create: `opencli-plugin/tests/*.test.mjs`
- Create: `opencli-plugin/tests/fixtures/*.html`
- Create: `opencli-plugin/STRATEGY.md`

**Interfaces:**
- Consumes: OpenCLI registry and typed errors only.
- Produces: seven read-only adapter commands with stable JSON columns.

- [ ] **Step 1: Write the required strategy note before adapter code**

`STRATEGY.md` must state:

```text
Strategy: COOKIE / browser-backed read
Contract: visible logged-in web data
Authentication source: user's live Chrome session
Replay basis: synthetic fixtures plus isolated registry validation
```

It must explain that automated CI cannot validate a real private account
and that optional live smoke tests use a dedicated test account only.

- [ ] **Step 2: Write failing fixture tests for all seven commands**

Each test imports one adapter extraction function against a complete
synthetic fixture and asserts manually derived rows, column order, typed
empty-result errors, and argument errors.

- [ ] **Step 3: Run Node tests and verify red**

```bash
npm --prefix opencli-plugin test
```

Expected: missing adapter modules.

- [ ] **Step 4: Implement minimal read-only adapters**

Do not include `download`, `photos`, generic eval, arbitrary URL fetch, or
write actions. Do not store or print cookies.

- [ ] **Step 5: Reverse-validate one selector per adapter**

Temporarily mutate the selected fixture anchor, verify the focused test
fails, restore it, and verify it passes.

- [ ] **Step 6: Validate against an isolated OpenCLI configuration**

Run OpenCLI validation with temporary configuration and cache roots. Do
not install into the current user's OpenCLI directories.

- [ ] **Step 7: Verify the plugin is available as a packaged resource**

Add a Python packaging test that resolves the bundled plugin directory
through `importlib.resources`, and verify that all seven adapter files
are present after installing the wheel.

- [ ] **Step 8: Run all plugin tests and verify green**

```bash
npm --prefix opencli-plugin test
```

- [ ] **Step 9: Commit**

```bash
git add opencli-plugin
git commit -m "feat: package standalone read-only Douban adapters"
```

---

### Task 12: Public Documentation, License, Examples, and CI

**Files:**
- Create: `README.md`
- Create: `LICENSE`
- Create: `NOTICE`
- Create: `SECURITY.md`
- Create: `CONTRIBUTING.md`
- Create: `docs/security.md`
- Create: `docs/privacy.md`
- Create: `docs/troubleshooting.md`
- Create: `examples/generic-stdio.json`
- Create: `examples/generic-streamable-http.json`
- Create: `examples/python-client/README.md`
- Create: `examples/typescript-client/README.md`
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/live-smoke.yml`
- Create: `tests/test_docs_smoke.py`
- Create: `tests/test_privacy_scan.py`

**Interfaces:**
- Consumes: installed CLI and package metadata.
- Produces: public installation, connection, permissions, troubleshooting,
  security, privacy, and contribution documentation.

- [ ] **Step 1: Write failing documentation smoke and privacy tests**

The smoke test executes every shell-free CLI command shown in generic
configuration examples against an isolated test environment. The privacy
test rejects:

- maintainer usernames;
- `/Users/<name>` and `C:\Users\<name>` literals outside generic security
  patterns;
- private application names;
- real account URLs;
- cookie, token, or authorization assignments;
- runtime cache and fixture artifacts.

- [ ] **Step 2: Run tests and verify red**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/test_docs_smoke.py tests/test_privacy_scan.py -q
```

- [ ] **Step 3: Add Apache-2.0 license, notices, docs, and examples**

README must cover:

- non-affiliation;
- read-only Douban boundary;
- macOS and Windows prerequisites;
- OpenCLI Browser Bridge;
- installation;
- setup dry-run;
- Chrome login;
- stdio and HTTP;
- all 11 tools;
- export policies;
- diagnostics;
- uninstall;
- data locations;
- privacy;
- future roadmap.

- [ ] **Step 4: Add CI and manual live-smoke workflow**

CI matrix:

```text
macos-latest × Python 3.11, 3.12, 3.13
windows-latest × Python 3.11, 3.12, 3.13
```

Node plugin job uses Node.js 22 and an exact OpenCLI 1.8.x test version.
Default CI has no Douban network access. Live smoke is manually triggered,
fork-inaccessible, and uploads no result bodies or browser traces.

- [ ] **Step 5: Run docs and privacy tests and verify green**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest tests/test_docs_smoke.py tests/test_privacy_scan.py -q
```

- [ ] **Step 6: Commit**

```bash
git add README.md LICENSE NOTICE SECURITY.md CONTRIBUTING.md docs examples .github tests
git commit -m "docs: prepare privacy-safe open-source release"
```

---

### Task 13: Full Validation, Packaging, Isolation Audit, and Handoff

**Files:**
- Modify only files revealed by validation failures.
- Create: `CHANGELOG.md`

**Interfaces:**
- Consumes: complete repository.
- Produces: a verified source distribution, wheel, tool manifest, and
  privacy/isolation report.

- [ ] **Step 1: Run complete Python quality checks**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 ruff check .
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 mypy src
UV_CACHE_DIR="$PWD/.uv-cache" uv run --python 3.13 pytest -q
```

Expected: zero errors and zero failed tests.

- [ ] **Step 2: Run plugin tests and isolated validation**

```bash
npm --prefix opencli-plugin test
```

Expected: zero failures.

- [ ] **Step 3: Build and inspect Python artifacts**

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv build
UV_CACHE_DIR="$PWD/.uv-cache" uvx twine check dist/*
```

Inspect archive entries and confirm they exclude:

```text
.git/
.uv-cache/
.venv/
runtime caches
logs
proposals
private fixtures
```

- [ ] **Step 4: Run installed-wheel smoke tests in a fresh environment**

Install the built wheel into a new temporary uv environment. Run:

```text
cove-douban-mcp --version
cove-douban-mcp setup --dry-run
cove-douban-mcp print-config --transport stdio
cove-douban-mcp print-config --transport streamable-http
```

Then initialize the wheel's stdio server with the official MCP client and
confirm the exact 11-tool surface.

- [ ] **Step 5: Audit isolation**

Verify:

- the private source repository status is unchanged from the recorded
  pre-task status;
- the current user OpenCLI registry and adapter files are unchanged;
- no live private-account command was run;
- no private cache or fixture path appears in the new repository;
- all writes are confined to the new repository and temporary test roots.

- [ ] **Step 6: Add changelog and final release notes**

Document v0.1.0 features, known limitations, OpenCLI version range, local
HTTP boundary, and optional export permission.

- [ ] **Step 7: Run the full validation a second time after final edits**

Repeat Python checks, plugin checks, package build, wheel smoke, privacy
scan, and Git diff check. Completion claims must cite this fresh output.

- [ ] **Step 8: Commit final release state**

```bash
git add .
git commit -m "chore: finalize v0.1.0 release candidate"
```

- [ ] **Step 9: Update the engineer handoff without exposing private data**

Record the repository path, branch, commits, validation commands, known
limitations, and the fact that the private application and current
OpenCLI environment were not modified.
