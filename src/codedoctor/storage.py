from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class ReportPaths:
    directory: Path
    latest: Path
    previous: Path
    timestamped: Path


def get_report_paths(repo_path: Path) -> ReportPaths:
    report_dir = repo_path / ".codedoctor"
    latest = report_dir / "report-latest.txt"
    previous = report_dir / "report-prev.txt"

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    timestamped = report_dir / f"report-{ts}.txt"

    return ReportPaths(
        directory=report_dir,
        latest=latest,
        previous=previous,
        timestamped=timestamped,
    )


def rotate_latest_to_previous(latest: Path, previous: Path) -> None:
    if latest.exists():
        previous.parent.mkdir(parents=True, exist_ok=True)
        if previous.exists():
            previous.unlink()
        latest.replace(previous)
