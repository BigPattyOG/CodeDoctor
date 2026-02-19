from __future__ import annotations

import shutil
import subprocess  # nosec B404
from pathlib import Path

from codedoctor.report import CheckResult, CheckStatus, ScanReport


def tool_exists(tool: str) -> bool:
    return shutil.which(tool) is not None


def classify_status(name: str, returncode: int, output: str) -> CheckStatus:
    if returncode != 0:
        return CheckStatus.FAIL

    # Pytest can return 0 but still print nasty shutdown exceptions on Windows.
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
        name=display_name, returncode=proc.returncode, output=output
    )

    return CheckResult(
        name=display_name,
        command=cmd,
        returncode=proc.returncode,
        output=output,
        status=status,
    )


def build_checks(apply_fixes: bool, skip_tests: bool) -> list[tuple[str, list[str]]]:
    checks: list[tuple[str, list[str]]] = []

    # Ruff
    if tool_exists("ruff"):
        if apply_fixes:
            checks.append(("ruff (auto-fix)", ["ruff", "check", ".", "--fix"]))
        checks.append(("ruff (lint)", ["ruff", "check", "."]))
    else:
        checks.append(("ruff (missing)", []))

    # Black
    if tool_exists("black"):
        if apply_fixes:
            checks.append(("black (format)", ["black", "."]))
        checks.append(("black (check)", ["black", ".", "--check"]))
    else:
        checks.append(("black (missing)", []))

    # MyPy
    if tool_exists("mypy"):
        checks.append(("mypy (types)", ["mypy", "src"]))

    # Bandit
    if tool_exists("bandit"):
        checks.append(("bandit (security)", ["bandit", "-r", "src"]))

    # Pytest
    if not skip_tests and tool_exists("pytest"):
        checks.append(("pytest (tests)", ["pytest", "-q"]))

    return checks


def scan_repo(repo_path: Path, apply_fixes: bool, skip_tests: bool) -> ScanReport:
    results: list[CheckResult] = []

    for name, cmd in build_checks(apply_fixes=apply_fixes, skip_tests=skip_tests):
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
