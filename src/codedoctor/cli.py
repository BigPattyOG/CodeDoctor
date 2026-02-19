from __future__ import annotations

import argparse
from pathlib import Path

from codedoctor.runner import scan_repo
from codedoctor.storage import get_report_paths, rotate_latest_to_previous


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codedoctor",
        description="Beginner-friendly checks for Python repositories.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Scan a repository.")
    scan.add_argument("path", nargs="?", default=".", help="Repo path (default: .)")
    scan.add_argument(
        "--fix", action="store_true", help="Apple safe auto_fixes (ruff --fix, black)."
    )
    scan.add_argument("--skip-tests", action="store_true", help="Skip running pytest.")
    scan.add_argument(
        "--report-dir",
        default=".codedoctor",
        help="Directory (relative to repo) to store reports.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_path = Path(args.path).resolve()

    if args.command == "scan":
        report = scan_repo(
            repo_path=repo_path,
            apply_fixes=bool(args.fix),
            skip_tests=bool(args.skip_tests),
        )

        report_root = repo_path / args.report_dir
        paths = get_report_paths(repo_path=repo_path)

        paths = paths.__class__(
            directory=report_root,
            latest=report_root / "report-latest.txt",
            previous=report_root / "report-prev.txt",
            timestamped=report_root / paths.timestamped.name,
        )

        report_root.mkdir(parents=True, exist_ok=True)
        rotate_latest_to_previous(latest=paths.latest, previous=paths.previous)

        text = report.to_full_text()
        paths.latest.write_text(text, encoding="utf-8")
        paths.timestamped.write_text(text, encoding="utf-8")

        print(text)
        print(f"\nWrote: {paths.latest}")
        print(f"Wrote: {paths.timestamped}")
        if paths.previous.exists():
            print(f"Previous: {paths.previous}")

        return report.exit_code

    return 1
