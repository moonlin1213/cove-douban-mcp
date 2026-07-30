# Cove Douban MCP Design Specification

**Status:** Approved design awaiting implementation-plan review
**Date:** 2026-07-30
**Project:** `cove-douban-mcp`
**Initial release:** `v0.1.0`
**License:** Apache License 2.0

## 1. Purpose

`cove-douban-mcp` is an unofficial, local-first MCP server for reading
public Douban subjects and a user's own authorized Douban library through
the user's existing local Chrome session.

The project extracts the reusable behavior of an existing private
integration into a clean, standalone, open-source repository. It must not
depend on, import, modify, or package any private application source,
private cache, private account identifier, private list, private review,
private path, or private model-provider integration.

The server is permanently read-only toward Douban. It may write its own
internal cache and, only when explicitly authorized by the local user,
export verified results as Markdown inside a user-selected directory.

The project is not affiliated with or endorsed by Douban.

## 2. Goals

The initial release must:

1. Run on macOS and Windows.
2. Work with any standards-compliant MCP client rather than depending on
   a fixed list of clients.
3. Support both `stdio` and local-only Streamable HTTP.
4. Expose the current private integration's complete Douban capability
   set:
   - public search for movies, books, and music;
   - movie and book subject details;
   - watched, wish-list, and currently-watching movie marks;
   - personal ratings and short comments;
   - personal long-form reviews;
   - compact movie-profile summaries;
   - doulists, movie lists, and book lists;
   - items within one doulist;
   - local filtering, exclusion, and pagination;
   - short-lived query caching;
   - a durable personal movie-library baseline;
   - non-shrinking merge protection;
   - daily due-check synchronization and manual synchronization;
   - a short-lived result-reference cache;
   - optional Markdown export.
5. Keep Douban-side behavior read-only in every configuration.
6. Make Markdown export discoverable but disabled by default.
7. Store no Douban password, cookie, Chrome profile copy, or browser
   debugging credential.
8. Include no real user's personal information or data.
9. Install and test without modifying the maintainer's existing private
   application or existing user OpenCLI configuration.
10. Ship an Apache-2.0 license, third-party notices, security guidance,
    privacy guidance, and a clear non-affiliation disclaimer.

## 3. Non-goals for v0.1.0

The initial release will not:

- modify marks, ratings, reviews, lists, or profile information on Douban;
- expose arbitrary OpenCLI commands;
- expose a generic browser-control tool;
- expose a shell or command-execution tool;
- read or write arbitrary local files;
- listen on a LAN or public network interface;
- provide remote hosting, multiple users, or cloud account management;
- install a macOS LaunchAgent or Windows Scheduled Task;
- bundle movie-poster download;
- add hot movie lists, hot book lists, Top 250, charts, photo search, or
  other capabilities not present in the current private integration;
- copy private fixtures, site memory, network captures, logs, caches, or
  account data into the repository;
- silently upgrade OpenCLI;
- overwrite an existing user-authored Douban adapter.

These exclusions are scope boundaries, not architectural limitations.
New read-only Douban tools can be added in compatible minor releases.

## 4. Public Identity and Packaging

The project uses the following stable public identity:

| Surface | Name |
|---|---|
| GitHub repository | `cove-douban-mcp` |
| Python distribution | `cove-douban-mcp` |
| Python import package | `cove_douban_mcp` |
| Command-line entry point | `cove-douban-mcp` |
| MCP server name | `Cove Douban MCP` |
| Application data directory name | `cove-douban-mcp` |
| OpenCLI plugin name | `cove-douban` |

The README and server metadata must include:

> Unofficial, local-first, read-only Douban integration. Not affiliated
> with or endorsed by Douban.

The source distribution and Python wheel are the initial portable
artifacts. Standalone macOS arm64, macOS x64, and Windows x64 executables
will be built later from the same source after the Python package passes
the complete cross-platform test matrix. They must not become a separate
implementation.

## 5. Repository Structure

The standalone repository has this intended structure:

```text
cove-douban-mcp/
├── src/
│   └── cove_douban_mcp/
│       ├── domain/
│       │   ├── models.py
│       │   ├── filters.py
│       │   ├── merge.py
│       │   ├── pagination.py
│       │   ├── result_refs.py
│       │   └── errors.py
│       ├── storage/
│       │   ├── paths.py
│       │   ├── atomic_json.py
│       │   ├── query_cache.py
│       │   ├── marks_store.py
│       │   ├── sync_state.py
│       │   ├── working_cache.py
│       │   ├── permissions.py
│       │   └── locks.py
│       ├── opencli/
│       │   ├── gateway.py
│       │   ├── registry.py
│       │   ├── parser.py
│       │   ├── diagnostics.py
│       │   └── plugin_installer.py
│       ├── services/
│       │   ├── catalog.py
│       │   ├── marks.py
│       │   ├── reviews.py
│       │   ├── doulists.py
│       │   ├── sync.py
│       │   └── status.py
│       ├── export/
│       │   ├── markdown.py
│       │   ├── proposals.py
│       │   └── sandbox.py
│       ├── mcp/
│       │   ├── server.py
│       │   ├── tools.py
│       │   ├── transport.py
│       │   └── auth.py
│       ├── config.py
│       └── cli.py
├── opencli-plugin/
│   ├── package.json
│   ├── opencli.plugin.json
│   ├── clis/
│   │   └── douban/
│   │       ├── search.js
│   │       ├── subject.js
│   │       ├── marks.js
│   │       ├── marks-full.js
│   │       ├── reviews.js
│   │       ├── doulists.js
│   │       └── doulist.js
│   └── tests/
├── tests/
│   ├── domain/
│   ├── storage/
│   ├── opencli/
│   ├── services/
│   ├── export/
│   ├── mcp/
│   └── install/
├── docs/
│   ├── security.md
│   ├── privacy.md
│   ├── troubleshooting.md
│   └── superpowers/
│       ├── specs/
│       └── plans/
├── examples/
│   ├── generic-stdio.json
│   ├── generic-streamable-http.json
│   ├── python-client/
│   └── typescript-client/
├── pyproject.toml
├── uv.lock
├── LICENSE
├── NOTICE
├── SECURITY.md
├── CONTRIBUTING.md
└── README.md
```

Files may be split further when a module would otherwise acquire more
than one responsibility. The implementation must not collapse domain,
transport, storage, and installation concerns into one large module.

## 6. Dependency Direction

The architecture uses one-way dependencies:

```text
MCP and CLI
    ↓
Application services
    ↓
Pure domain logic
    ↓
Injected OpenCLI gateway and storage interfaces
```

The boundaries are:

- `domain` contains pure data models, filtering, merging, pagination,
  result-reference semantics, and domain errors. It does not import MCP,
  OpenCLI, filesystem paths, environment variables, or a model-provider
  SDK.
- `storage` owns only the server's application-data directory and an
  explicitly authorized export root.
- `opencli` owns command construction, subprocess execution, JSON
  parsing, diagnostics, and plugin installation.
- `services` orchestrate cache-first reads, explicit refreshes, fallback,
  synchronization, and result-reference creation.
- `export` owns Markdown generation, proposals, path confinement,
  backups, and atomic file replacement.
- `mcp` converts domain inputs and outputs to standard MCP tool schemas
  and structured results.
- `cli` exposes setup, diagnostics, serving, permissions, cache, export
  approval, and uninstall commands.

The repository must contain no provider-specific ToolSearch, Codeflow,
Qidian, role-persona, or chat-history compaction logic.

## 7. Runtime Requirements

The supported Python range is:

```text
>= 3.11, < 3.14
```

CI tests Python 3.11, 3.12, and 3.13 on macOS and Windows.

OpenCLI compatibility for v0.1.0 is:

```text
>= 1.8.6, < 2.0.0
```

OpenCLI plugin CI uses Node.js 22 and one exact OpenCLI 1.8.x release.
The implementation plan must confirm and lock an exact official MCP
Python SDK release and all other direct dependencies. Runtime dependency
ranges must be bounded by a tested major version, while `uv.lock` must
make development and CI reproducible.

## 8. Installation Experience

The initial developer-oriented installation options are:

```bash
uvx cove-douban-mcp setup
```

and:

```bash
pipx install cove-douban-mcp
cove-douban-mcp setup
```

Installing the Python distribution alone must not modify OpenCLI, Chrome,
an MCP client configuration, or an export directory.

The interactive `setup` command must:

1. detect macOS or Windows;
2. locate and version-check OpenCLI;
3. diagnose the Browser Bridge and Chrome extension;
4. show the exact plugin files and actions it proposes;
5. ask before installing the OpenCLI plugin;
6. guide the user to log into Douban in Chrome themselves;
7. run a public-search smoke check;
8. optionally run a personal read-only smoke check;
9. create the server's application-data directory;
10. ask whether Markdown export should remain disabled or be configured;
11. print generic `stdio` and Streamable HTTP examples;
12. detect selected known MCP clients as a convenience;
13. show and back up any known-client configuration before modifying it;
14. leave unknown clients fully supported through generic configuration.

`setup --dry-run` must print the complete action plan without changing
anything.

The implementation and automated tests must use a temporary application
data directory and a temporary OpenCLI configuration. Development must
not run public-user setup against the maintainer's current environment.

## 9. Cross-platform Data Directories

`platformdirs` determines the application data root.

Expected macOS layout:

```text
~/Library/Application Support/cove-douban-mcp/
├── config.toml
├── cache/
│   ├── queries.json
│   ├── movie-marks.json
│   ├── sync-state.json
│   └── working/
├── proposals/
└── logs/
```

Expected Windows layout:

```text
%LOCALAPPDATA%\cove-douban-mcp\
├── config.toml
├── cache\
├── proposals\
└── logs\
```

No source file, test, documentation example, or default configuration may
contain a maintainer's username, private absolute path, personal list
name, private account identifier, or private export location.

The runtime must not store:

- Douban passwords;
- Douban cookies;
- Chrome profile copies;
- browser-debugging credentials;
- MCP client chat histories;
- complete raw browser traces in the normal log directory.

Sensitive configuration files, local HTTP credentials, caches, and
proposals use owner-only permissions where the platform supports POSIX
mode bits. Windows installation applies a current-user-only ACL. Failure
to establish the required access control aborts HTTP credential creation
rather than silently creating a broadly readable secret.

## 9.1 Default Runtime Settings

The initial defaults are:

```toml
[cache]
query_ttl_seconds = 21600
query_max_entries = 80
working_ttl_seconds = 86400
working_max_refs_per_scope = 16
working_max_bytes_per_ref = 8388608
working_max_total_bytes_per_scope = 67108864

[marks]
default_page_size = 30
maximum_page_size = 200

[sync]
enabled = true
local_time = "05:10"
statuses = ["wish", "collect"]
include_doulists = true
startup_delay_seconds = 90

[export]
enabled = false
policy = "off"
maximum_write_bytes = 10485760

[http]
host = "127.0.0.1"
port = 8765
authentication_required = true
```

The local HTTP token is generated with at least 256 bits of
cryptographically secure entropy. Result references and proposal IDs use
the same minimum entropy and are not sequential.

## 10. MCP Transports

### 10.1 stdio

The default server command is:

```bash
cove-douban-mcp serve --transport stdio
```

In `stdio` mode:

- stdout contains only valid MCP messages;
- logs use stderr;
- the client owns the child-process lifecycle;
- no network listener is opened;
- the tool surface is identical to the HTTP tool surface.

### 10.2 Local Streamable HTTP

The local HTTP command is:

```bash
cove-douban-mcp serve \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port 8765
```

For v0.1.0:

- only `127.0.0.1`, `localhost`, and `::1` are valid hosts;
- LAN and public bind addresses are rejected before server startup;
- a per-installation local Bearer token is required by default;
- the token never appears in logs or MCP tool results;
- an incoming `Origin` header must match an explicit configured origin;
- wildcard origins are forbidden;
- browser frontends must explicitly configure their local origin;
- a local frontend should preferably connect through its own local
  backend rather than embedding the token in frontend source.

Generic configuration:

```json
{
  "url": "http://127.0.0.1:8765/mcp",
  "headers": {
    "Authorization": "Bearer <local-token>"
  }
}
```

The core protocol implementation must not branch on Claude, Codex,
Cursor, or another client brand.

## 11. Permission Model

The server has three independent permission layers.

### 11.1 Douban permission

This layer is permanently read-only and cannot be changed through
configuration.

It permits:

- public subject reads;
- reads of data visible to the user's current local Chrome session;
- local processing and caching of those reads.

It prohibits:

- creating, editing, or deleting marks;
- changing ratings;
- publishing or editing reviews;
- creating, editing, or deleting lists;
- changing account data.

### 11.2 Internal application-data permission

The server may always read and write within its own application-data
directory for:

- query cache;
- durable movie-marks baseline;
- sync state;
- working-result references;
- pending export proposals;
- redacted diagnostic logs;
- configuration.

It may not use this permission to access unrelated local files.

### 11.3 Markdown export permission

Markdown export is present but disabled by default:

```toml
[export]
enabled = false
policy = "off"
```

Supported policies are:

- `off`: no export proposal or write is allowed;
- `confirm_each`: every write creates a one-time proposal that a human
  approves outside the model;
- `allow_in_root`: an explicitly authorized user allows direct Markdown
  writes within one configured root.

An enabled export configuration includes an absolute root selected by the
local user:

```toml
[export]
enabled = true
root = "<user-selected-directory>"
policy = "confirm_each"
```

No public example may use a maintainer's private path.

`confirm_each` approval flow:

```text
MCP export tool call
→ validate result reference and result completeness
→ validate target path and mode
→ create one-time proposal
→ return proposal ID without writing
→ human inspects with CLI or local approval page
→ human approves or rejects
→ approved proposal performs exactly one write
→ proposal becomes unusable
```

CLI approval commands:

```bash
cove-douban-mcp export list
cove-douban-mcp export show <proposal-id>
cove-douban-mcp export approve <proposal-id>
cove-douban-mcp export reject <proposal-id>
```

The MCP model cannot approve its own proposal.

The export sandbox must:

- resolve normalized and real paths;
- reject parent traversal;
- reject absolute paths outside the configured root;
- reject symlink or Windows junction escape;
- allow only `.md` and `.markdown`;
- limit one write's byte count;
- use atomic writes;
- make a recoverable backup before replacement;
- invalidate pending proposals when permission is revoked;
- never provide arbitrary local-file reading;
- never expose a shell.

Export modes are:

- `create`;
- `append`;
- `replace`.

Structured Markdown-table replacement must preserve unrelated document
content and stop safely when the expected table structure is not
recognized.

## 12. MCP Tool Surface

v0.1.0 exposes exactly these tools:

1. `douban_status`
2. `douban_search`
3. `douban_subject`
4. `douban_movie_marks`
5. `douban_reviews`
6. `douban_movie_profile`
7. `douban_doulists`
8. `douban_doulist_items`
9. `douban_sync`
10. `douban_working_cache_read`
11. `douban_export_markdown`

`douban_export_markdown` remains discoverable when export is disabled.
Calling it then returns the stable `permission_required` error and makes
no write attempt.

The server does not expose OpenCLI's generic registry, browser controls,
poster download, photo listing, or arbitrary adapter passthrough.

## 13. Tool Contracts

### 13.1 `douban_status`

Reports:

- server version;
- cache schema version;
- OpenCLI availability and supported version;
- Browser Bridge availability;
- whether a Douban login appears usable;
- installed plugin version;
- the age and status of internal caches;
- whether a sync is running or due;
- export policy and configured-state boolean;
- supported transports.

It must not return:

- cookies or tokens;
- account identifiers;
- personal list contents;
- private filesystem paths beyond a safe display label;
- HTTP Bearer token.

### 13.2 `douban_search`

Inputs:

- `query: str`, required and non-empty;
- `type: "movie" | "book" | "music"`, default `movie`;
- `limit: int`, default `5`, range `1..10`;
- `refresh: bool`, default `false`.

Returns normalized subject candidates with title, rating when present,
abstract, URL, and extracted subject ID when present.

### 13.3 `douban_subject`

Inputs:

- `id: str`, required and normalized to a numeric subject ID;
- `type: "movie" | "book"`, default `movie`;
- `refresh: bool`, default `false`.

Returns the normalized subject model appropriate to the selected type.

### 13.4 `douban_movie_marks`

Inputs:

- `status: "collect" | "wish" | "do" | "all"`, default `collect`;
- `limit: int`, default `30`, range `1..200`;
- `offset: int`, default `0`, minimum `0`;
- `uid: str`, optional;
- `refresh: bool`, default `false`;
- `query: str`, optional;
- `exclude: str | list[str]`, optional;
- `genre: str`, optional;
- `country: str`, optional;
- `director: str`, optional;
- `cast: str`, optional;
- `year_from: int`, optional;
- `year_to: int`, optional.

The service filters before paginating. It returns the current page,
complete matching count, next offset, terminal state, source freshness,
and an opaque `result_ref` for the complete verified match set.

An empty `uid` means the current local login. A non-empty `uid` never
reads or writes the current user's durable private baseline; it uses a
separate query-cache namespace so data from different users cannot be
mixed.

### 13.5 `douban_reviews`

Inputs:

- `limit: int`, default `20`, range `1..50`;
- `uid: str`, optional;
- `full: bool`, default `false`;
- `refresh: bool`, default `false`.

Returns normalized reviews without exposing session details.

### 13.6 `douban_movie_profile`

Inputs:

- `statuses: list["collect" | "wish" | "do"]`, default all three;
- `limit_per_status: int`, default `20`, range `1..80`;
- `refresh: bool`, default `false`.

Returns compact sections and source freshness for each requested status.

### 13.7 `douban_doulists`

Inputs:

- `kind: "all" | "movie" | "book"`, default `all`;
- `limit: int`, default `30`, range `1..80`;
- `uid: str`, optional;
- `refresh: bool`, default `false`.

Returns normalized list metadata and an opaque result reference.

As with movie marks, a non-empty `uid` uses a separate cache namespace
and cannot reuse the current user's private baseline or cached list
index.

### 13.8 `douban_doulist_items`

Inputs:

- `id: str`, numeric doulist ID or valid Douban doulist URL;
- `limit: int`, default `40`, range `1..120`;
- `refresh: bool`, default `false`.

Returns normalized list entries and an opaque result reference.

### 13.9 `douban_sync`

Inputs:

- `statuses: list["collect" | "wish" | "do"]`, default `wish` and
  `collect`;
- `include_doulists: bool`, default `true`;
- `force: bool`, default `false`.

The tool writes only internal cache and sync-state files. It cannot alter
Douban or user documents. Concurrent processes coordinate through a
cross-platform file lock.

### 13.10 `douban_working_cache_read`

Inputs:

- `result_ref: str`, required;
- `page: int`, default `0`;
- `page_size: int`, default `30`, range `1..200`.

Page zero returns only a safe index and metadata. Positive pages return a
slice of the cached verified result. Expired references return
`result_expired`.

### 13.11 `douban_export_markdown`

Inputs:

- `result_ref: str`, required;
- `path: str`, required and resolved within the configured export root;
- `mode: "create" | "append" | "replace"`, default `create`;
- `heading: str`, optional.

Outcomes:

- `permission_required` under `off`;
- a one-time proposal under `confirm_each`;
- a completed confined write under `allow_in_root`;
- a stable validation or conflict error.

The body is always generated from the server-side verified result rather
than model-supplied rows.

## 14. Structured Result Envelope

All tools return a stable structured envelope:

```json
{
  "ok": true,
  "source": "full_cache",
  "freshness": {
    "checked_at": "2026-01-02T05:10:00+08:00",
    "stale": false,
    "refreshed": false
  },
  "filters": {},
  "pagination": {
    "total": 42,
    "offset": 0,
    "limit": 30,
    "returned": 30,
    "has_more": true,
    "next_offset": 30
  },
  "result_ref": "opaque-local-reference",
  "items": []
}
```

Each successful result also includes a compact text representation for
clients that do not consume structured output. Text compaction is
deterministic code, not an LLM summary.

An error result uses:

```json
{
  "ok": false,
  "error": {
    "code": "browser_bridge_unavailable",
    "message": "OpenCLI Browser Bridge is not connected.",
    "action": "Run `cove-douban-mcp doctor` and reconnect the Chrome extension."
  },
  "fallback": {
    "used": true,
    "source": "full_cache",
    "stale": true,
    "checked_at": "2026-01-01T05:10:00+08:00"
  }
}
```

No result includes a raw traceback, cookie, HTTP token, complete process
environment, or private path.

## 15. OpenCLI Plugin

The bundled plugin contains only:

```text
douban search
douban subject
douban marks
douban marks-full
douban reviews
douban doulists
douban doulist
```

The initial adapter strategy is:

```text
Strategy: COOKIE / browser-backed read
Contract: visible logged-in web data
Authentication source: user's live Chrome session
```

The implementation:

- does not export or persist cookies;
- does not ask users to copy cookies;
- does not read Chrome profile files;
- does not bypass verification, risk controls, or access controls;
- returns typed login and source-change errors;
- double-validates inputs in JavaScript and Python;
- uses only allowed OpenCLI registry and error imports;
- keeps adapter columns aligned with returned object keys;
- never returns a fabricated sentinel row for failure.

The source plugin remains inert until a public user explicitly approves
installation through `setup`.

If an existing same-name adapter is detected, setup stops by default and
offers:

- use the existing adapter;
- install into an isolated project namespace;
- back up and replace after confirmation;
- cancel.

The setup command must not silently replace a user-authored adapter or
silently upgrade global OpenCLI.

## 16. Caching

The system uses four storage layers.

### 16.1 Query cache

- default TTL: six hours;
- maximum entries: 80;
- cache key: operation plus normalized sorted parameters;
- only valid successful results are stored;
- explicit refresh bypasses reads;
- cache writes are atomic.

### 16.2 Durable movie-marks baseline

The baseline stores versioned lists for `collect`, `wish`, and `do`,
plus checked time, updated time, counts, and metadata coverage.

Identity preference:

```text
movie ID → canonical URL → normalized title
```

Merge rules:

- latest present fields enrich old fields;
- latest missing or empty fields do not erase old present fields;
- duplicate identities merge;
- partial new responses never shorten an existing complete history;
- saving performs a final defensive merge with the current disk cache;
- real deletion reconciliation requires a separately validated complete
  rebuild, not an ordinary incremental sync.

### 16.3 Sync state

Stores:

- last checked time;
- last successful time and local date;
- reason;
- per-status outcomes;
- last redacted error;
- whether a sync is running;
- plugin and cache schema versions.

### 16.4 Working-result cache

Stores a complete normalized verified result behind an opaque random
reference.

Defaults:

- 24-hour expiry;
- 16 active references per client/session scope;
- 8 MiB maximum serialized data per reference;
- 64 MiB maximum total working-cache data per client/session scope;
- ID-first deduplication;
- no filter terms encoded in the reference;
- page-on-demand reading;
- automatic expiry cleanup.

Export uses this complete server-side data. The model does not reconstruct
multiple pages.

## 17. Filtering and Pagination

Movie-mark processing order:

1. load selected status or merge `all`;
2. normalize items;
3. apply excluded-title terms;
4. apply full-field query;
5. apply genre;
6. normalize and apply country or region terms;
7. apply director;
8. apply cast;
9. apply year bounds;
10. calculate complete match count;
11. apply offset and limit;
12. create a result reference for the complete match set.

Country aliases use longest-match and canonical-name rules. Multi-country
requests use OR semantics. A short substring must not accidentally match
an unrelated country name.

Pagination reports:

- complete match count;
- current offset;
- current limit;
- returned count;
- `has_more`;
- next offset or `null`;
- explicit terminal state.

## 18. Synchronization

The server preserves daily synchronization without installing an
operating-system scheduler.

Behavior:

1. server startup checks whether today's sync is due;
2. the first personal-library call checks again;
3. a long-running process performs the configured daily due check;
4. a process that was not running catches up on next startup or call;
5. `douban_sync` allows explicit manual synchronization;
6. an in-process async lock prevents duplicate work;
7. a cross-process file lock prevents multiple local MCP processes from
   refreshing simultaneously;
8. synchronization calls OpenCLI directly and uses no LLM;
9. successful rows merge into the durable baseline;
10. partial or failed synchronization preserves the previous baseline;
11. per-status failure prevents a false all-success result.

## 19. Error Codes and Fallback

Stable error codes:

```text
dependency_missing
browser_bridge_unavailable
login_required
adapter_missing
adapter_incompatible
source_changed
timeout
invalid_argument
cache_unavailable
result_expired
permission_required
path_outside_root
write_confirmation_required
write_conflict
internal_error
```

Fallback rules:

- a valid old cache may be returned after refresh failure;
- fallback results must be marked stale with their checked time;
- missing reliable data produces an honest error;
- raw page failure must not be converted into invented data;
- detailed diagnostics remain local and redacted;
- error messages include a safe next action when available.

## 20. Uninstall

Default uninstall removes only:

- client configuration entries created by this project;
- the OpenCLI plugin installed by this project;
- the installed command-line package.

It preserves:

- application cache;
- permission configuration;
- exported Markdown;
- user-authored OpenCLI configuration;
- Chrome extension;
- Chrome login state.

Data purge requires:

```bash
cove-douban-mcp uninstall --purge-data
```

and a second confirmation. Purge still does not delete exported
Markdown.

## 21. Testing Strategy

Implementation follows strict test-driven development: each production
behavior is preceded by a focused test that is observed failing for the
expected missing behavior.

Default tests use synthetic data and temporary directories. They do not
connect to a real private Douban account.

### 21.1 Domain tests

Cover:

- all mark statuses;
- every filter;
- multi-region OR;
- aliases and longest match;
- exclusion parsing;
- filter-before-pagination;
- first, middle, terminal, and past-terminal pages;
- identity fallback;
- field enrichment;
- non-erasure by empty values;
- non-shrinking cache protection;
- result-reference expiry;
- deduplication;
- Markdown generation and structured merge.

### 21.2 Storage and permission tests

Cover:

- atomic cache writes;
- recovery from malformed JSON;
- cross-process locks;
- schema migration;
- working-cache expiry;
- export disabled by default;
- authorized-root confinement;
- parent and absolute-path escape;
- symlink and Windows junction escape;
- extension allowlist;
- write-size limit;
- one-time proposal semantics;
- model-ineligible confirmation;
- backup before replacement;
- permission-revocation invalidation.

### 21.3 OpenCLI gateway and plugin tests

A test-only fake `opencli` executable verifies the real subprocess
boundary:

- argument-array execution without a shell;
- command allowlist;
- correct argument mapping;
- JSON parsing;
- malformed output;
- timeouts;
- redaction;
- stable error mapping.

Plugin fixtures are synthetic and must:

- contain complete fake shapes rather than fragments tailored only to
  tests;
- include no real account data;
- assert exact normalized columns and types;
- use typed errors for empty, login, and argument failures;
- include a reverse validation that breaks a selector and proves the
  regression test fails;
- validate in an isolated temporary OpenCLI directory.

### 21.4 MCP protocol tests

Use an official MCP client against a real test server.

`stdio` tests:

- initialize;
- list tools;
- call tools;
- validate structured content;
- verify stdout protocol purity;
- close normally.

Streamable HTTP tests:

- bind a random loopback port;
- reject missing token;
- reject invalid origin;
- accept valid token and origin;
- initialize;
- list and call tools;
- reject a non-loopback host configuration;
- close normally.

Both transports must expose identical tool names and schemas.

### 21.5 Setup and uninstall tests

Use temporary HOME and LOCALAPPDATA values to verify:

- package installation has no setup side effects;
- dry-run has no side effects;
- unapproved setup has no side effects;
- existing adapter conflict stops safely;
- generic configuration generation;
- known-client backup before change;
- default uninstall preserves data;
- purge requires confirmation;
- exported Markdown is never removed.

## 22. Continuous Integration

GitHub Actions matrix:

```text
macos-latest:
  Python 3.11
  Python 3.12
  Python 3.13

windows-latest:
  Python 3.11
  Python 3.12
  Python 3.13
```

Plugin jobs use Node.js 22 and the exact tested OpenCLI 1.8.x version.

Every pull request runs:

- Python tests;
- static typing;
- lint;
- package build;
- stdio protocol tests;
- local HTTP protocol tests;
- OpenCLI fixture and validation tests;
- macOS and Windows setup simulation;
- sensitive-data and secret scanning;
- license and dependency reporting;
- executable README command smoke checks.

Default CI does not access Douban.

An optional maintainer-triggered live smoke workflow may use a dedicated
test account. It must not:

- run on fork pull requests;
- save result bodies as artifacts;
- expose login data;
- upload private browser traces;
- use a maintainer's personal account.

## 23. Release Contents

The `v0.1.0` preview release contains:

- PyPI source distribution and wheel;
- GitHub source archive;
- the OpenCLI plugin;
- generic stdio and HTTP configuration;
- Python and TypeScript client examples;
- macOS and Windows installation documentation;
- SHA-256 checksums;
- a software bill of materials;
- Apache-2.0 `LICENSE`;
- third-party `NOTICE`;
- `SECURITY.md`;
- privacy and troubleshooting documentation;
- non-affiliation disclaimer.

## 24. Backward-compatible Extension

Future compatible minor releases may add:

```text
douban_movie_hot
douban_book_hot
douban_movie_top250
douban_movie_photos
douban_music_search_enhanced
douban_chart
douban_people
```

New read-only tools do not require new export permission.

A future poster-download tool would require its own explicit file-write
permission and must not inherit Markdown export permission.

Semantic versioning rules:

- compatible new tools or optional fields increment the minor version;
- adapter fixes increment the patch version;
- incompatible changes to published tool contracts increment the major
  version;
- existing field meanings are not silently changed;
- cache migrations are explicit and versioned.

## 25. Security and Privacy Invariants

The implementation is unacceptable if any invariant is violated:

1. No tool writes to Douban.
2. No password or cookie enters MCP content, logs, config, fixtures, or
   the repository.
3. No generic command execution or arbitrary browser control is exposed.
4. HTTP never binds a non-loopback interface in v0.1.0.
5. HTTP validates authentication and Origin.
6. Internal writes remain inside the server application-data directory.
7. Export is disabled by default.
8. Export cannot escape its configured root.
9. A model cannot approve `confirm_each` proposals.
10. Partial refresh cannot shrink a durable complete baseline.
11. Failed reads cannot produce invented rows.
12. Setup cannot overwrite an existing adapter without informed consent.
13. Uninstall cannot delete exported documents.
14. Tests and release artifacts contain no real user's private data.
15. The public repository neither imports nor modifies a private source
    application.

## 26. v0.1.0 Acceptance Criteria

The release is complete only when:

1. all 11 MCP tools are discoverable through stdio and local Streamable
   HTTP;
2. both transports expose matching names and schemas;
3. public search, subject details, marks, reviews, movie profile,
   doulists, doulist items, sync, result references, and optional export
   have tests and implementations;
4. all filter, pagination, merge, and fallback behavior is covered;
5. Douban-side behavior is demonstrably read-only;
6. export is disabled by default;
7. enabled export obeys the selected policy and root;
8. macOS and Windows test matrices pass;
9. a clean environment can install and run the package;
10. setup is explicit and dry-runnable;
11. README instructions allow a user without project context to install,
    log in, connect, diagnose, configure export, and uninstall;
12. package, plugin, and documentation pass sensitive-information scans;
13. no existing private application, cache, OpenCLI configuration, or
    browser state was modified during development;
14. completion is supported by fresh test, build, protocol, packaging,
    and isolation evidence.

## 27. Approved Decisions

The following product decisions were explicitly approved:

- support macOS and Windows;
- preserve the complete current Douban capability set;
- keep Douban permanently read-only;
- retain Markdown export as an optional user-controlled permission;
- support all standards-compliant MCP clients;
- expose both stdio and local-only Streamable HTTP;
- defer remote and multi-user operation;
- use Python MCP plus an OpenCLI plugin and CLI setup wizard;
- use the public name `cove-douban-mcp`;
- use Apache License 2.0;
- keep non-current capabilities such as hot charts as future upgrades;
- build a new standalone repository without changing the private source
  application or current user environment.
