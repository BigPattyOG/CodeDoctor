# CodeDoctor

**CodeDoctor** is a beginner-friendly Python CLI that runs common quality checks
(linting, formatting, type checking, security scanning, and tests) against **any**
Python repository or folder you point it at, and produces a readable report.

It’s designed to be simple to run, easy to understand, and safe by default.

---

## Requirements

- Python **3.12+**
- (Recommended) `git` available on PATH for best `.gitignore` support

---

## Install

From PyPI:

```bash
python -m pip install codedoctor
```

Verify:

```bash
codedoctor --help
codedoctor scan --help
```

---

## Setup (required)

Before running scans, initialize CodeDoctor once:

```bash
codedoctor setup
```

This creates a small config file in your user profile (JSON) that stores default
behavior (e.g., whether to respect `.gitignore`, default report directory, etc.).

### CI / no-config environments

If you’re running in CI or you don’t want CodeDoctor to create a config file,
you can bypass the setup requirement with:

```bash
codedoctor scan . --assume-defaults
```

---

## Quick Start

Scan the current folder:

```bash
codedoctor scan .
```

Scan a different path:

```bash
codedoctor scan /path/to/repo
```

On Windows:

```powershell
codedoctor scan C:\path\to\repo
```

Apply safe auto-fixes + formatting:

```bash
codedoctor scan . --fix
```

Skip tests:

```bash
codedoctor scan . --skip-tests
```

---

## Commands

### `codedoctor scan`

```bash
codedoctor scan [PATH] [--fix] [--skip-tests] [--report-dir DIR] [--no-gitignore] \
  [--no-update-check] [--assume-defaults]
```

#### Options

- `PATH`  
  Repository/folder to scan (default: `.`)

- `--fix`  
  Apply safe auto-fixes (Ruff `--fix`) and format with Black.

- `--skip-tests`  
  Skip running `pytest`.

- `--report-dir DIR`  
  Directory (relative to the repo) to store reports. If omitted, uses the value
  from your CodeDoctor config.

- `--no-gitignore`  
  Disable best-effort `.gitignore` handling (useful for debugging).

- `--no-update-check`  
  Disable the non-blocking “update available” notice during scans.

- `--assume-defaults`  
  Allow scanning without running `codedoctor setup` (useful for CI).

---

### `codedoctor setup`

```bash
codedoctor setup [--force]
```

Creates or updates the user config file.

- `--force` overwrites an existing config file.

---

### `codedoctor update`

```bash
codedoctor update [--yes]
```

Checks PyPI for the latest version and offers to upgrade CodeDoctor.

- `--yes` updates without prompting.

> Note: if CodeDoctor was installed into a locked or managed Python environment,
> `codedoctor update` may fail due to permissions. In that case, update using
> your environment’s normal package management approach (venv, pipx, etc.).

---

## What gets run during a scan

CodeDoctor invokes the following tools (when installed/available):

- `ruff check .` (and optionally `ruff check . --fix`)
- `black . --check` (and optionally `black .`)
- `mypy .`
- `bandit -r .`
- `pytest -q` (unless `--skip-tests`)

CodeDoctor runs tools in the target repo by setting `cwd` to the repo path.

---

## Reports

Reports are written under the repository (default `.codedoctor/`):

- `report-latest.txt` — newest scan
- `report-prev.txt` — previous scan (rotated)
- `report-YYYYMMDD-HHMMSS.txt` — timestamped snapshot

---

## `.gitignore` behavior (best effort)

Different tools treat ignore rules differently:

- **Ruff** and **Black** already respect `.gitignore` in typical setups.
- **MyPy** and **Bandit** do not consistently honor `.gitignore` the same way.

To provide consistent behavior, CodeDoctor will **attempt** to use git’s ignore
information when scanning a git repository by running:

```bash
git ls-files -ci --exclude-standard
```

Those ignored paths are then excluded from MyPy/Bandit runs.

If any of the following are true:
- the target folder is not a git repo
- `git` is not installed
- the git command fails

…CodeDoctor falls back to excluding common junk directories like `.venv`, `.git`,
caches, `build/`, and `dist/`.

---

## Exit Codes

CodeDoctor returns an exit code that matches the overall result:

- `0` — all checks passed
- `1` — warnings (non-fatal issues)
- `2` — failures (one or more checks failed)

Missing tools are treated as failures for that check (return code `127`) so the
report remains explicit and beginner-friendly.

---

## Development

Clone and install editable:

```bash
git clone https://github.com/BigPattyOG/CodeDoctor.git
cd CodeDoctor
python -m pip install -e .
```

Run setup:

```bash
codedoctor setup
```

Run a scan:

```bash
codedoctor scan .
```

---

## License

MIT License. See `LICENSE`.