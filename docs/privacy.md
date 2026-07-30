# Privacy

## Data processed

When a user invokes a tool, the local process may handle:

- public subject search and detail information;
- marks, reviews, and lists visible to the current browser session;
- normalized query parameters;
- locally generated result references;
- a user-selected Markdown destination, only after export is enabled.

All processing is local unless Chrome itself loads a Douban page as part of
the user's authorized browser session.

## Data stored

The application data directory may contain:

- bounded query cache;
- durable movie-mark baseline;
- synchronization state;
- expiring working results;
- pending export proposals;
- configuration and a local HTTP credential;
- short redacted diagnostic messages.

It does not intentionally store:

- Douban passwords or cookies;
- Chrome profiles or browser-debugging credentials;
- raw browser traces in the normal log directory;
- MCP client conversations;
- maintainer or contributor account data;
- exported Markdown outside the directory explicitly selected by the user.

## Retention

Query entries expire after six hours by default. Working results expire after
24 hours. The durable marks baseline remains until the user purges application
data. Export proposals remain local and become single-use, rejected,
completed, or invalidated when permissions change.

## Isolation

An empty `uid` refers to the current local login. A non-empty `uid` receives a
separate hashed query-cache namespace and cannot read or modify the current
login's durable baseline. Working results are scoped to the MCP client/session
that created them.

## User control

Users can inspect status with `doctor`, disable export at any time, reject
pending proposals, uninstall the OpenCLI integration while preserving cache,
or explicitly purge application data. Exported Markdown is never deleted by
the uninstaller.

