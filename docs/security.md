# Security model

## Trust boundaries

Cove Douban MCP has four explicit boundaries:

1. MCP clients may request only the 11 registered tools.
2. The Python gateway may start only seven allowlisted OpenCLI commands and
   always uses an argument array, never a shell.
3. The OpenCLI adapters are permanently read-only and rely on pages already
   visible to the user's Chrome session.
4. Optional Markdown writes are separate from Douban access and confined to
   one user-authorized directory.

## Douban boundary

No configuration can enable a Douban write. The adapter package contains no
rating, mark mutation, review publication, list mutation, download, arbitrary
URL, or evaluation command.

The Browser Bridge supplies the live browser context. This project does not
ask users to paste browser credentials, does not read profile files, and does
not persist or print session cookies.

## Subprocess boundary

The gateway uses `asyncio.create_subprocess_exec` with a fixed command
registry. Unsupported command names and flags fail before process creation.
Timeouts, malformed output, login requirements, source changes, and bridge
failures map to stable public error codes. Raw tracebacks and full stderr are
not returned through MCP. A shared local file lock prevents separate MCP
processes from navigating the same Browser Bridge session concurrently.

## Local HTTP

Streamable HTTP:

- accepts only `localhost`, `127.0.0.1`, or `::1`;
- has no production `--no-auth` switch;
- requires a randomly generated token with at least 256 bits of entropy;
- compares credentials in constant time;
- rejects any supplied Origin not explicitly allowed;
- stores the token with owner-only mode `0600` on POSIX;
- uses shell-free `icacls` on Windows to remove inherited entries and grant
  access only to the current user;
- aborts local HTTP startup and removes a newly created credential if the
  required Windows ACL cannot be established.

A browser frontend should never embed this token in public JavaScript. Use a
same-machine backend or stdio.

## Cache and references

Working-result references are random, scoped to one client/session, expire
after 24 hours by default, and contain no filter, user ID, or path. Per-scope
count and byte limits prevent unbounded growth.

Movie-mark saves re-read the current disk state and merge before atomic
replacement. Ordinary partial refreshes cannot shorten the durable baseline.

## Export sandbox

Export is off by default. When enabled, the sandbox:

- resolves lexical and real paths;
- rejects parent traversal and absolute-path escape;
- rejects symlink and Windows reparse-point escape;
- permits only Markdown extensions;
- enforces a maximum final byte count;
- uses atomic replacement;
- backs up an existing document before a structured replace;
- prevents an MCP tool from approving its own `confirm_each` proposal.

## Known limitations

Visible website structure can change. A changed selector should produce a
typed source error, but a new layout may require an adapter update. CI uses
synthetic fixtures and cannot prove that a private account page is currently
unchanged. Optional live smoke checks must use a dedicated test account.
