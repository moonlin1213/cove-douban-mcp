import re
import subprocess
from pathlib import Path


def test_tracked_public_files_contain_no_private_identity_or_secret_shape() -> None:
    root = Path(__file__).parents[1]
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    staged_or_untracked = [
        path
        for path in (
            "README.md",
            "SECURITY.md",
            "CONTRIBUTING.md",
            "NOTICE",
            "docs/security.md",
            "docs/privacy.md",
            "docs/troubleshooting.md",
            "examples/generic-stdio.json",
            "examples/generic-streamable-http.json",
            ".github/workflows/ci.yml",
            ".github/workflows/live-smoke.yml",
        )
        if (root / path).exists()
    ]
    candidates = sorted(set(tracked + staged_or_untracked))
    forbidden_literals = (
        "moon" + "lin",
        "Aions" + "Home",
        "栖" + "渡",
    )
    secret_shapes = (
        re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
        re.compile(r"(?i)authorization\s*[:=]\s*bearer\s+(?!\\?\$\{)[A-Za-z0-9_-]{20,}"),
        re.compile(r"/Users/(?!<name>|example|user)[A-Za-z0-9._-]+"),
        re.compile(r"(?i)C:\\Users\\(?!<name>|example|user)[A-Za-z0-9._-]+"),
    )

    violations: list[str] = []
    for relative in candidates:
        path = root / relative
        if not path.is_file() or path.suffix in {".pyc", ".png", ".jpg", ".zip"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for literal in forbidden_literals:
            if literal.casefold() in text.casefold():
                violations.append(f"{relative}: forbidden literal {literal}")
        for pattern in secret_shapes:
            if pattern.search(text):
                violations.append(f"{relative}: secret or private-path shape")

    assert violations == []


def test_runtime_artifacts_are_not_tracked() -> None:
    root = Path(__file__).parents[1]
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    forbidden_parts = {
        ".venv",
        ".uv-cache",
        "node_modules",
        "__pycache__",
        ".runtime",
    }
    assert all(not forbidden_parts.intersection(Path(path).parts) for path in tracked)
