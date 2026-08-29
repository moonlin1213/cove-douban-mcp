# Changelog

All notable changes to this project are documented here.

## 0.2.0 — 2026-08-29

Compatible feature release adding fixed, read-only public charts.

### Added

- A twelfth MCP tool, `douban_chart`, covering the movie weekly chart,
  North America box office, new releases, movie Top 250, popular books, and
  popular music.
- An eighth bundled OpenCLI adapter that maps six allowlisted board keys to
  fixed Douban URLs and normalizes visible public rows.
- Bounded Top 250 pagination, successful-query caching, per-client result
  references, and a safe cached fallback when an explicit refresh fails.

### Security

- Chart calls cannot supply arbitrary URLs, page offsets, browser scripts,
  headers, cookies, export paths, or shell arguments.
- Existing cache schemas and all eleven v0.1.x MCP tool contracts are
  unchanged.

## 0.1.1 — 2026-08-20

Bugfix release for browser-backed extraction and synchronization reliability.

### Fixed

- Prefer semantic title and information links over earlier cover links in
  search, movie-mark, review, and doulist extractors.
- Wait for the client-side `/mine/` profile redirect before deciding that the
  active browser session is not signed in.
- Refresh the durable movie-mark baseline through bounded, lightweight list
  chunks instead of opening one detail page for every mark.
- Clear interrupted synchronization state, reconcile abandoned `running`
  state after one hour, and serialize Browser Bridge access across local MCP
  processes.

## 0.1.0 — 2026-07-30

Initial release candidate.

### Added

- Eleven structured MCP tools covering status, search, subject details,
  movie marks, reviews, movie profile, lists, list entries, synchronization,
  working-result paging, and optional Markdown export.
- Identical stdio and loopback-only Streamable HTTP transports.
- Seven bundled, permanently read-only OpenCLI 1.8.x Douban adapters.
- macOS and Windows application-data paths, setup, doctor, permission,
  proposal, configuration, and uninstall commands.
- Four bounded local storage layers with atomic writes, non-shrinking marks
  merge, per-client opaque references, and daily no-LLM synchronization.
- Export policies `off`, `confirm_each`, and `allow_in_root`, including path,
  symlink, junction, extension, byte-limit, atomic-write, and backup guards.
- Apache License 2.0, public security and privacy documentation, generic MCP
  client examples, synthetic fixture tests, and CI for Python 3.11–3.13 on
  macOS and Windows.

### Security defaults

- Douban operations cannot be configured to write.
- Markdown export is disabled.
- HTTP is restricted to loopback and requires a 256-bit-or-greater local
  credential. POSIX uses mode `0600`; Windows removes inherited ACL entries
  with `icacls` and grants access only to the current user.
- Setup refuses adapter conflicts and has no force-overwrite mode.
- Default tests and release archives contain no private account fixture.

### Known limitations

- Visible Douban page structure may change and require an adapter update.
- Automated CI cannot validate a real signed-in private account; optional
  protected smoke checks require a dedicated test account.
- OpenCLI 1.8.x and a working local Chrome Browser Bridge are required.
- Windows local HTTP startup aborts if `icacls` cannot establish the required
  current-user-only credential ACL.
