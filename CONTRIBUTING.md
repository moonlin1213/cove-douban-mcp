# Contributing

## Development setup

```bash
uv sync --all-groups
npm --prefix opencli-plugin ci
```

Run all local checks:

```bash
uv run ruff check .
uv run mypy src
uv run pytest -q
npm --prefix opencli-plugin test
```

## Test data

All default tests must be offline and use synthetic identities, URLs, titles,
reviews, and lists. Never commit a real account page, cookie, result body,
browser trace, private export path, or maintainer filesystem path.

DOM adapter changes require:

1. a minimal noise-stripped synthetic fixture;
2. explicit expected rows and column ordering;
3. typed argument, empty, authentication, and source errors;
4. reverse-validation proving the changed selector makes a focused test fail;
5. isolated OpenCLI 1.8.x validation with a temporary home directory.

## Compatibility

Keep the existing 11 MCP tool names and structured fields backward compatible.
New capabilities such as popular charts should normally use new tools. Both
stdio and Streamable HTTP must expose identical contracts.

## Pull requests

Explain the user-visible change, permission impact, tests run, and whether any
cache schema or adapter selector changed. Contributions that weaken the
read-only Douban boundary, allow non-loopback HTTP, bypass export confirmation,
or introduce real personal fixtures will not be accepted.

