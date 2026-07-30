"""Cross-platform command line for setup, serving, permissions, and diagnosis."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TextIO

from cove_douban_mcp import __version__
from cove_douban_mcp.config import ExportPolicy, Settings
from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.export.proposals import ProposalStore
from cove_douban_mcp.mcp.auth import LocalBearerAuth, load_or_create_http_token
from cove_douban_mcp.mcp.server import create_mcp_server
from cove_douban_mcp.mcp.transport import run_stdio, run_streamable_http
from cove_douban_mcp.opencli.diagnostics import OpenCLIDiagnostics
from cove_douban_mcp.opencli.gateway import OpenCLIGateway
from cove_douban_mcp.opencli.plugin_installer import PluginInstaller
from cove_douban_mcp.services.container import ServiceContainer
from cove_douban_mcp.storage.paths import AppPaths


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cove-douban-mcp")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    setup = commands.add_parser("setup", help="plan or perform local setup")
    setup.add_argument("--dry-run", action="store_true")
    setup.add_argument("--yes", action="store_true")

    serve = commands.add_parser("serve", help="run the MCP server")
    serve.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
    )

    doctor = commands.add_parser("doctor", help="run read-only local diagnostics")
    doctor.add_argument("--json", action="store_true")

    permissions = commands.add_parser("permissions", help="manage optional permissions")
    permission_commands = permissions.add_subparsers(dest="permission", required=True)
    export_permission = permission_commands.add_parser("export")
    export_permission.add_argument(
        "--policy",
        choices=["confirm_each", "allow_in_root"],
    )
    export_permission.add_argument("--root")
    export_permission.add_argument("--disable", action="store_true")

    cache = commands.add_parser("cache", help="inspect local application caches")
    cache.add_argument("action", choices=["status"], default="status", nargs="?")

    export = commands.add_parser("export", help="inspect or decide export proposals")
    export.add_argument("action", choices=["list", "show", "approve", "reject"])
    export.add_argument("proposal_id", nargs="?")

    print_config = commands.add_parser(
        "print-config",
        help="print generic MCP client configuration",
    )
    print_config.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
    )

    uninstall = commands.add_parser("uninstall", help="remove the OpenCLI integration")
    uninstall.add_argument("--yes", action="store_true")
    uninstall.add_argument("--purge-data", action="store_true")
    uninstall.add_argument("--confirm-purge", action="store_true")
    return parser


def _paths(environ: Mapping[str, str]) -> AppPaths:
    injected = environ.get("COVE_DOUBAN_DATA_ROOT", "").strip()
    return AppPaths.from_root(Path(injected)) if injected else AppPaths.platform_default()


def _opencli_home(environ: Mapping[str, str]) -> Path:
    injected = environ.get("COVE_DOUBAN_OPENCLI_HOME", "").strip()
    return Path(injected).expanduser().absolute() if injected else Path.home() / ".opencli"


def _opencli_binary(environ: Mapping[str, str]) -> Path:
    configured = environ.get("COVE_DOUBAN_OPENCLI_BINARY", "").strip()
    discovered = configured or shutil.which("opencli") or "opencli"
    return Path(discovered)


def _print_json(value: object, stream: TextIO) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2), file=stream)


def _render_config(settings: Settings, transport: str) -> dict[str, object]:
    if transport == "stdio":
        return {
            "transport": "stdio",
            "command": "cove-douban-mcp",
            "args": ["serve", "--transport", "stdio"],
        }
    return {
        "transport": "streamable-http",
        "url": f"http://{settings.http.host}:{settings.http.port}/mcp",
        "headers": {"Authorization": "Bearer ${COVE_DOUBAN_MCP_TOKEN}"},
        "note": "Read the token locally; never embed it in browser frontend source.",
    }


def _setup(
    args: argparse.Namespace,
    *,
    paths: AppPaths,
    installer: PluginInstaller,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    plan = installer.plan(paths.root)
    if plan.conflicts:
        print(
            "Setup stopped: existing adapter or plugin detected; nothing was replaced.",
            file=stderr,
        )
        return 2
    if args.dry_run:
        print("DRY RUN — no files were changed.", file=stdout)
        for action in plan.actions:
            print(f"- {action}", file=stdout)
        return 0
    if not args.yes:
        print("Setup requires interactive confirmation or --yes.", file=stderr)
        return 2

    paths.ensure()
    settings = Settings.default(paths.root)
    settings.save(paths.config)
    installer.install()
    print("Setup complete. Douban access is permanently read-only.", file=stdout)
    _print_json(_render_config(settings, "stdio"), stdout)
    return 0


async def _doctor_payload(
    paths: AppPaths,
    installer: PluginInstaller,
    binary: Path,
) -> dict[str, object]:
    diagnostics = await OpenCLIDiagnostics(binary).check()
    return {
        "version": __version__,
        "douban_access": "read_only",
        "checks": {
            "config": paths.config.exists(),
            "plugin": installer.target.exists(),
            "opencli": diagnostics.model_dump(mode="json"),
        },
        "next": (
            "Run setup --dry-run, then setup --yes."
            if not paths.config.exists()
            else "Use print-config to connect any standards-compliant MCP client."
        ),
    }


def _permissions(
    args: argparse.Namespace,
    *,
    paths: AppPaths,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    settings = Settings.load(paths.config)
    proposals = ProposalStore(paths.proposals)
    if args.disable:
        settings.export.enabled = False
        settings.export.policy = ExportPolicy.OFF
        settings.export.root = None
        settings.save(paths.config)
        invalidated = proposals.invalidate_all()
        print(f"Markdown export disabled; invalidated {invalidated} proposal(s).", file=stdout)
        return 0
    if not args.policy or not args.root:
        print("Enabling export requires both --policy and --root.", file=stderr)
        return 2
    root = Path(args.root).expanduser().absolute()
    root.mkdir(parents=True, exist_ok=True)
    settings.export.enabled = True
    settings.export.policy = ExportPolicy(args.policy)
    settings.export.root = root
    settings.save(paths.config)
    invalidated = proposals.invalidate_all()
    print(
        f"Markdown export set to {args.policy}; invalidated {invalidated} old proposal(s).",
        file=stdout,
    )
    return 0


def _container(paths: AppPaths, environ: Mapping[str, str]) -> ServiceContainer:
    settings = Settings.load(paths.config)
    return ServiceContainer.create(
        settings=settings,
        paths=paths,
        gateway=OpenCLIGateway(_opencli_binary(environ)),
    )


def _export_command(
    args: argparse.Namespace,
    *,
    paths: AppPaths,
    environ: Mapping[str, str],
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    store = ProposalStore(paths.proposals)
    if args.action == "list":
        _print_json(
            [proposal.model_dump(mode="json") for proposal in store.list_pending()],
            stdout,
        )
        return 0
    if not args.proposal_id:
        print("This export action requires a proposal ID.", file=stderr)
        return 2
    if args.action == "show":
        _print_json(store.load(args.proposal_id).model_dump(mode="json"), stdout)
    elif args.action == "reject":
        _print_json(store.reject(args.proposal_id).model_dump(mode="json"), stdout)
    else:
        outcome = _container(paths, environ).export.exporter.approve_proposal(
            args.proposal_id
        )
        _print_json(outcome.model_dump(mode="json"), stdout)
    return 0


def _safe_purge_target(path: Path) -> bool:
    resolved = path.resolve()
    return (
        resolved != Path(resolved.anchor)
        and resolved != Path.home().resolve()
        and len(resolved.parts) >= 3
    )


def _serve(paths: AppPaths, environ: Mapping[str, str], transport: str) -> int:
    container = _container(paths, environ)
    server = create_mcp_server(container)
    if transport == "stdio":
        run_stdio(server)
        return 0
    token = load_or_create_http_token(paths.root / "http-token")
    run_streamable_http(
        server,
        host=container.settings.http.host,
        port=container.settings.http.port,
        auth=LocalBearerAuth(
            token=token,
            allowed_origins=set(container.settings.http.allowed_origins),
        ),
    )
    return 0


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
    environ: Mapping[str, str] | None = None,
) -> int:
    environment = dict(environ or os.environ)
    args = _parser().parse_args(list(argv) if argv is not None else None)
    paths = _paths(environment)
    installer = PluginInstaller(_opencli_home(environment))

    try:
        if args.command == "setup":
            return _setup(
                args,
                paths=paths,
                installer=installer,
                stdout=stdout,
                stderr=stderr,
            )
        if args.command == "serve":
            return _serve(paths, environment, args.transport)
        if args.command == "doctor":
            payload = asyncio.run(
                _doctor_payload(paths, installer, _opencli_binary(environment))
            )
            if args.json:
                _print_json(payload, stdout)
            else:
                print("Cove Douban MCP doctor", file=stdout)
                _print_json(payload, stdout)
            checks = payload["checks"]
            if not isinstance(checks, dict):
                return 1
            opencli_check = checks.get("opencli")
            ready = (
                bool(checks.get("config"))
                and bool(checks.get("plugin"))
                and isinstance(opencli_check, dict)
                and bool(opencli_check.get("available"))
            )
            return 0 if ready else 1
        if args.command == "permissions":
            return _permissions(
                args,
                paths=paths,
                stdout=stdout,
                stderr=stderr,
            )
        if args.command == "cache":
            snapshot = _container(paths, environment).marks_store.load()
            _print_json(
                {
                    "mark_counts": {
                        name: len(items) for name, items in snapshot.statuses.items()
                    }
                },
                stdout,
            )
            return 0
        if args.command == "export":
            return _export_command(
                args,
                paths=paths,
                environ=environment,
                stdout=stdout,
                stderr=stderr,
            )
        if args.command == "print-config":
            _print_json(
                _render_config(Settings.load(paths.config), args.transport),
                stdout,
            )
            return 0
        if args.command == "uninstall":
            if not args.yes:
                print("Uninstall requires interactive confirmation or --yes.", file=stderr)
                return 2
            if args.purge_data and not args.confirm_purge:
                print("Data purge requires --confirm-purge as a second confirmation.", file=stderr)
                return 2
            installer.uninstall()
            if args.purge_data:
                if not _safe_purge_target(paths.root):
                    print("Refusing to purge an unsafe data path.", file=stderr)
                    return 2
                if paths.root.exists():
                    shutil.rmtree(paths.root)
            print("OpenCLI integration removed. Exported Markdown was not touched.", file=stdout)
            return 0
    except DoubanError as error:
        print(f"{error.code}: {error.message}", file=stderr)
        if error.action:
            print(error.action, file=stderr)
        return 2
    except (OSError, ValueError) as error:
        print(f"local_error: {error}", file=stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
