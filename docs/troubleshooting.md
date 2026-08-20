# Troubleshooting

## Start with doctor

```bash
cove-douban-mcp doctor --json
```

Doctor checks only local readiness. It does not fetch private account rows.

## OpenCLI is missing or unsupported

Install OpenCLI 1.8.x and confirm:

```bash
opencli --version
opencli doctor
```

The MCP package never silently upgrades a global OpenCLI installation.

## Browser Bridge unavailable

Open Chrome normally, make sure the OpenCLI Browser Bridge is connected, then
run `opencli doctor`. A refresh failure can return a stale durable baseline
when one exists; the result includes a warning and `freshness.stale=true`.

## Login required

Sign in through the normal Douban page in the same Chrome session OpenCLI
uses. Do not paste cookies into configuration or issue reports.

## Another browser request is already in progress

All local MCP processes share one Browser Bridge session. If a request returns
`operation_in_progress`, let the active request finish and retry. The gateway
rejects overlapping browser work instead of letting two processes navigate the
same page at once.

An interrupted synchronization clears its `running` state on exit. A state
left behind by a hard process termination is treated as abandoned after one
hour and does not permanently block later diagnostics or synchronization.

## Setup reports an existing adapter

Setup refuses to replace a same-name user adapter. Back up and remove the
conflicting file yourself, use the existing adapter knowingly, or cancel.
The project does not provide a force-overwrite switch.

## A result reference expired

Run the original query again. References expire and are scoped to the client
that created them; copying a reference into another client is intentionally
unsupported.

## Markdown path rejected

Confirm that export is enabled, the path is inside the selected root, the
extension is `.md` or `.markdown`, and no parent component is a symbolic link
or Windows junction leading outside the root.

## HTTP returns 401 or 403

- 401: the local Bearer credential is missing or incorrect.
- 403: the request supplied an Origin that is not locally allowed.

Do not expose the service on a LAN address. Non-loopback binds are rejected
before server startup.

## Windows reports a credential ACL error

Run the terminal as the same Windows account that will run the MCP client and
confirm the built-in `icacls` command is available. The service intentionally
refuses local HTTP startup when it cannot remove inherited access and grant
the credential only to the current user. Stdio transport does not create an
HTTP credential and remains available.

## Source layout changed

Run the synthetic plugin tests and isolated validation, then open a minimal
issue containing the command, stable error code, operating system, Python
version, OpenCLI version, and a redacted description. Never attach cookies,
account pages, full browser traces, or private result bodies.
