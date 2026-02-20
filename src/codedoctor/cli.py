from __future__ import annotations

import argparse
import time
from dataclasses import replace
from pathlib import Path

from codedoctor.config import (
    CodeDoctorConfig,
    default_config_path,
    load_config,
    save_config,
)
from codedoctor.runner import scan_repo
from codedoctor.storage import get_report_paths, rotate_latest_to_previous
from codedoctor.updater import check_for_update, run_self_update

UPDATE_CHECK_INTERVAL_S = 24 * 60 * 60


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codedoctor",
        description="Beginner-friendly checks for Python repositories.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  codedoctor setup\n"
            "  codedoctor scan .\n"
            "  codedoctor scan . --fix\n"
            "  codedoctor update\n"
        ),
    )
    parser.add_argument(
        "--config",
        type=str,
        default=str(default_config_path()),
        help="Path to codedoctor config JSON (default: %(default)s).",
    )

    subs = parser.add_subparsers(dest="command", required=True)

    setup = subs.add_parser("setup", help="Initialize codedoctor.")
    setup.add_argument("--force", action="store_true", help="Overwrite config file.")

    update = subs.add_parser("update", help="Update codedoctor from PyPI.")
    update.add_argument("--yes", action="store_true", help="Update without prompting.")

    scan = subs.add_parser("scan", help="Scan a repository.")
    scan.add_argument("path", nargs="?", default=".", help="Repo path (default: .)")
    scan.add_argument("--fix", action="store_true", help="Apply safe auto-fixes.")
    scan.add_argument("--skip-tests", action="store_true", help="Skip running pytest.")
    scan.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Disable best-effort gitignore excludes for mypy/bandit.",
    )
    scan.add_argument(
        "--report-dir",
        default=None,
        help="Directory (relative to repo) to store reports (overrides config).",
    )
    scan.add_argument(
        "--assume-defaults",
        action="store_true",
        help="Allow scan without running setup (use built-in defaults).",
    )
    scan.add_argument(
        "--no-update-check",
        action="store_true",
        help="Do not check PyPI for updates during scan.",
    )

    return parser


def cmd_setup(config_path: Path, force: bool) -> int:
    if config_path.exists() and not force:
        print(f"Config already exists: {config_path}")
        print("Run: codedoctor setup --force")
        return 0

    cfg = CodeDoctorConfig(setup_completed=True, last_update_check_unix=0)
    save_config(cfg, path=config_path)
    print(f"Wrote config: {config_path}")
    return 0


def cmd_update(yes: bool) -> int:
    res = check_for_update()
    if res.error:
        print(f"Update check failed: {res.error}")
        return 1

    if not res.is_update_available:
        print(f"codedoctor is up to date ({res.installed}).")
        return 0

    print(f"Update available: {res.installed} -> {res.latest}")
    if not yes:
        answer = input("Update now? [y/N]: ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Canceled.")
            return 0

    rc = run_self_update()
    if rc == 0:
        print("Update completed.")
    else:
        print(f"Update failed (exit code {rc}).")
    return rc


def maybe_print_update_notice(cfg: CodeDoctorConfig) -> CodeDoctorConfig:
    now = int(time.time())
    if now - int(cfg.last_update_check_unix) < UPDATE_CHECK_INTERVAL_S:
        return cfg

    res = check_for_update()
    cfg2 = replace(cfg, last_update_check_unix=now)

    if res.error:
        return cfg2

    if res.is_update_available:
        print(f"Notice: codedoctor update available ({res.installed} -> {res.latest}).")
        print("Run: codedoctor update")

    return cfg2


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    config_path = Path(args.config).expanduser().resolve()
    cfg = load_config(path=config_path)

    if args.command == "setup":
        return cmd_setup(config_path=config_path, force=bool(args.force))

    if args.command == "update":
        return cmd_update(yes=bool(args.yes))

    if args.command == "scan":
        if not cfg.setup_completed and not bool(args.assume_defaults):
            print("codedoctor is not set up yet.")
            print("Run: codedoctor setup")
            print("Or:  codedoctor scan --assume-defaults")
            return 2

        if not bool(args.no_update_check):
            cfg2 = maybe_print_update_notice(cfg)
            if cfg2 != cfg and cfg.setup_completed:
                save_config(cfg2, path=config_path)
                cfg = cfg2

        repo_path = Path(args.path).expanduser().resolve()

        apply_fixes = bool(args.fix) or cfg.apply_fixes
        skip_tests = bool(args.skip_tests) or cfg.skip_tests
        respect_gitignore = (not bool(args.no_gitignore)) and cfg.respect_gitignore

        report_dir = args.report_dir if args.report_dir is not None else cfg.report_dir
        report_root = repo_path / report_dir

        report = scan_repo(
            repo_path=repo_path,
            apply_fixes=apply_fixes,
            skip_tests=skip_tests,
            respect_gitignore=respect_gitignore,
        )

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
