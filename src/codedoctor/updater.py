from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from importlib import metadata
from subprocess import run  # nosec B404

PYPI_JSON_URL = "https://pypi.org/pypi/codedoctor/json"


@dataclass(frozen=True)
class UpdateCheckResult:
    installed: str
    latest: str
    is_update_available: bool
    error: str | None = None


def _parse_semver_loose(v: str) -> tuple[int, ...]:
    parts: list[int] = []
    for chunk in v.split("."):
        digits = ""
        for ch in chunk:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def _is_newer(installed: str, latest: str) -> bool:
    return _parse_semver_loose(latest) > _parse_semver_loose(installed)


def get_installed_version() -> str:
    return metadata.version("codedoctor")


def get_latest_version_from_pypi(timeout_s: float = 5.0) -> str:
    req = urllib.request.Request(
        PYPI_JSON_URL,
        headers={"User-Agent": "codedoctor (update check)"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # nosec B310
        data = json.loads(resp.read().decode("utf-8"))
    return str(data["info"]["version"])


def check_for_update(timeout_s: float = 5.0) -> UpdateCheckResult:
    installed = "unknown"
    try:
        installed = get_installed_version()
        latest = get_latest_version_from_pypi(timeout_s=timeout_s)
        return UpdateCheckResult(
            installed=installed,
            latest=latest,
            is_update_available=_is_newer(installed, latest),
        )
    except metadata.PackageNotFoundError as e:
        return UpdateCheckResult(
            installed=installed,
            latest="unknown",
            is_update_available=False,
            error=str(e),
        )
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
        return UpdateCheckResult(
            installed=installed,
            latest="unknown",
            is_update_available=False,
            error=str(e),
        )


def run_self_update() -> int:
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "codedoctor"]
    proc = run(cmd, text=True)  # nosec B603
    return int(proc.returncode)
