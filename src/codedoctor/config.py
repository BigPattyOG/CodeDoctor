from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class CodeDoctorConfig:
    respect_gitignore: bool = True
    apply_fixes: bool = False
    skip_tests: bool = False
    report_dir: str = ".codedoctor"
    setup_completed: bool = False
    last_update_check_unix: int = 0


def default_config_path() -> Path:
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
        return base / "codedoctor" / "config.json"
    return Path.home() / ".config" / "codedoctor" / "config.json"


def load_config(path: Path) -> CodeDoctorConfig:
    if not path.exists():
        return CodeDoctorConfig()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return CodeDoctorConfig()

    return CodeDoctorConfig(
        respect_gitignore=bool(data.get("respect_gitignore", True)),
        apply_fixes=bool(data.get("apply_fixes", False)),
        skip_tests=bool(data.get("skip_tests", False)),
        report_dir=str(data.get("report_dir", ".codedoctor")),
        setup_completed=bool(data.get("setup_completed", False)),
        last_update_check_unix=int(data.get("last_update_check_unix", 0)),
    )


def save_config(config: CodeDoctorConfig, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(config), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
