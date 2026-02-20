from __future__ import annotations

import re
import shutil
import subprocess  # nosec B404
from pathlib import Path
from typing import Iterable

from codedoctor.report import CheckResult, CheckStatus, ScanReport


def tool_exists(tool: str) -> bool:
    return shutil.which(tool) is not None


def is_git_repo(repo_path: Path) -> bool:
    return (repo_path / ".git").exists()


def get_gitignored_paths(repo_path: Path) -> list[str]:
    git = shutil.which("git")
    if git is None or not is_git_repo(repo_path):
        return []

    proc = subprocess.run(  # nosec B603
        [git, "ls-files", "-ci", "--exclude-standard"],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return []

    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def to_mypy_exclude_regex(ignored_paths: Iterable[str]) -> str:
    base_dirs = (
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "build",
        "dist",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
    )
    patterns = [rf"(^|/){re.escape(d)}(/|$)" for d in base_dirs]

    for p in ignored_paths:
        p = p.replace("\\", "/").strip("/")
        if p:
            patterns.append(rf"(^|/){re.escape(p)}(/|$)")

    return "|".join(patterns)


def to_bandit_exclude_csv(ignored_paths: Iterable[str]) -> str:
    base = [
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "build",
        "dist",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        "tests",
    ]
    items = base + [p.replace("\\", "/").strip("/") for p in ignored_paths if p.strip()]

    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            out.append(item)
            seen.add(item)

    return ",".join(out)


def classify_status(name: str, returncode: int, output: str) -> CheckStatus:
    if returncode != 0:
        return CheckStatus.FAIL

    warning_signatures = [
        "Exception ignored in atexit callback",
        "PermissionError: [WinError 5]",
        "Traceback (most recent call last):",
    ]
    if name.startswith("pytest") and any(s in output for s in warning_signatures):
        return CheckStatus.WARN

    return CheckStatus.PASS


def run_command(display_name: str, cmd: list[str], cwd: Path) -> CheckResult:
    proc = subprocess.run(  # nosec B603
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    status = classify_status(
        name=display_name,
        returncode=proc.returncode,
        output=output,
    )

    return CheckResult(
        name=display_name,
        command=cmd,
        returncode=proc.returncode,
        output=output,
        status=status,
    )


def build_checks(
    repo_path: Path,
    apply_fixes: bool,
    skip_tests: bool,
    respect_gitignore: bool,
) -> list[tuple[str, list[str]]]:
    checks: list[tuple[str, list[str]]] = []
    ignored = get_gitignored_paths(repo_path) if respect_gitignore else []

    if tool_exists("ruff"):
        if apply_fixes:
            checks.append(("ruff (auto-fix)", ["ruff", "check", ".", "--fix"]))
        checks.append(("ruff (lint)", ["ruff", "check", "."]))
    else:
        checks.append(("ruff (missing)", []))

    if tool_exists("black"):
        if apply_fixes:
            checks.append(("black (format)", ["black", "."]))
        checks.append(("black (check)", ["black", ".", "--check"]))
    else:
        checks.append(("black (missing)", []))

    if tool_exists("mypy"):
        mypy_exclude = to_mypy_exclude_regex(ignored_paths=ignored)
        checks.append(
            (
                "mypy (types)",
                [
                    "mypy",
                    ".",
                    "--pretty",
                    "--show-error-codes",
                    "--exclude",
                    mypy_exclude,
                ],
            )
        )
    else:
        checks.append(("mypy (missing)", []))

    if tool_exists("bandit"):
        bandit_exclude = to_bandit_exclude_csv(ignored_paths=ignored)
        checks.append(
            ("bandit (security)", ["bandit", "-r", ".", "-x", bandit_exclude])
        )
    else:
        checks.append(("bandit (missing)", []))

    if skip_tests:
        return checks

    if tool_exists("pytest"):
        checks.append(("pytest (tests)", ["pytest", "-q"]))
    else:
        checks.append(("pytest (missing)", []))

    return checks


def scan_repo(
    repo_path: Path,
    apply_fixes: bool,
    skip_tests: bool,
    respect_gitignore: bool,
) -> ScanReport:
    results: list[CheckResult] = []

    for name, cmd in build_checks(
        repo_path=repo_path,
        apply_fixes=apply_fixes,
        skip_tests=skip_tests,
        respect_gitignore=respect_gitignore,
    ):
        if not cmd:
            tool = name.split(" ", 1)[0]
            results.append(
                CheckResult(
                    name=name,
                    command=[],
                    returncode=127,
                    output=(
                        f"{tool} is not installed or not on PATH.\n"
                        f"Install it with: python -m pip install {tool}"
                    ),
                    status=CheckStatus.FAIL,
                )
            )
            continue

        results.append(run_command(display_name=name, cmd=cmd, cwd=repo_path))

    return ScanReport(repo=str(repo_path), results=results)
