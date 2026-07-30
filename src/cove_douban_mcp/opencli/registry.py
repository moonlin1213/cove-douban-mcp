"""Allowlist and argument validation for OpenCLI subprocess calls."""

from __future__ import annotations

from dataclasses import dataclass

from cove_douban_mcp.domain.errors import DoubanError


@dataclass(frozen=True, slots=True)
class CommandSpec:
    minimum_positionals: int
    maximum_positionals: int
    flags: dict[str, frozenset[str] | None]


ALLOWED_COMMANDS: dict[str, CommandSpec] = {
    "search": CommandSpec(
        1,
        1,
        {
            "--type": frozenset({"movie", "book", "music"}),
            "--limit": None,
        },
    ),
    "subject": CommandSpec(
        1,
        1,
        {"--type": frozenset({"movie", "book"})},
    ),
    "marks": CommandSpec(
        0,
        0,
        {
            "--status": frozenset({"wish", "collect", "do"}),
            "--uid": None,
            "--limit": None,
            "--offset": None,
        },
    ),
    "marks-full": CommandSpec(
        0,
        0,
        {
            "--status": frozenset({"wish", "collect", "do"}),
            "--uid": None,
            "--limit": None,
        },
    ),
    "reviews": CommandSpec(
        0,
        0,
        {
            "--uid": None,
            "--limit": None,
            "--full": frozenset({"true", "false"}),
        },
    ),
    "doulists": CommandSpec(
        0,
        0,
        {
            "--kind": frozenset({"all", "movie", "book"}),
            "--uid": None,
            "--limit": None,
        },
    ),
    "doulist": CommandSpec(1, 1, {"--limit": None}),
}

_INTEGER_FLAGS = {"--limit", "--offset"}


def _invalid(message: str) -> DoubanError:
    return DoubanError("invalid_argument", message, "Use a documented tool argument.")


def validate_arguments(command: str, arguments: list[str]) -> list[str]:
    spec = ALLOWED_COMMANDS.get(command)
    if spec is None:
        raise _invalid("the requested OpenCLI command is not allowed")

    positionals: list[str] = []
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if not argument.startswith("--"):
            if not argument.strip() or "\x00" in argument:
                raise _invalid("positional arguments cannot be empty")
            positionals.append(argument)
            index += 1
            continue

        allowed_values = spec.flags.get(argument)
        if argument not in spec.flags:
            raise _invalid(f"unsupported option for {command}")
        if index + 1 >= len(arguments):
            raise _invalid(f"{argument} requires a value")
        value = arguments[index + 1]
        if value.startswith("--") or "\x00" in value:
            raise _invalid(f"{argument} requires a valid value")
        if allowed_values is not None and value not in allowed_values:
            raise _invalid(f"invalid value for {argument}")
        if argument in _INTEGER_FLAGS:
            try:
                integer = int(value)
            except ValueError as error:
                raise _invalid(f"{argument} must be an integer") from error
            if integer < 0 or (argument == "--limit" and integer < 1):
                raise _invalid(f"invalid value for {argument}")
        index += 2

    if not spec.minimum_positionals <= len(positionals) <= spec.maximum_positionals:
        raise _invalid(f"invalid number of positional arguments for {command}")
    return list(arguments)
