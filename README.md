# CodeDoctor - v0.1.0

**CodeDoctor** is a beginner-friendly Python CLI that scans a repository and
summarizes common quality checks (linting, formatting, typing, security, and
tests) in one readable report.

It can also generate a **TL;DR summary** at the top of the report and save
results to a `.txt` report file so you can compare runs over time.

---

## What it checks

Depending on what you have installed, CodeDoctor can run:

- **ruff** — linting (and optional auto-fixes)
- **black** — formatting (and optional formatting changes)
- **mypy** — static type checking
- **bandit** — basic security checks
- **pytest** — test runner

If a tool is missing, CodeDoctor will report it clearly.

---

## Installation

### Option A: Install from PyPI (recommended once published)

```bash
pip install codedoctor
```

### Option B: Install from source (for development)

```bash
git clone https://github.com/BigPattyOG/CodeDoctor.git
cd CodeDoctor
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

python -m pip install -U pip
python -m pip install -e .
```

To include developer tools (recommended for contributors):

```bash
python -m pip install -e ".[dev]"
```

---

## Quick start

From inside any repo you want to scan:

```bash
codedoctor scan .
```

CodeDoctor prints a report to the terminal and also writes a report file under:

- `.codedoctor/report-latest.txt`
- `.codedoctor/report-prev.txt` (previous run)
- `.codedoctor/report-YYYYMMDD-HHMMSS.txt` (timestamped history)

---

## Example output (TL;DR)

```text
CodeDoctor Report TL;DR
----------------------
Overall: WARN
Checks:  6 passed / 1 warned / 0 failed / 7 total

Warnings:
 - pytest (tests)
```

---

## Commands

### Scan a repo

```bash
codedoctor scan .
```

### Apply safe auto-fixes (where supported)

```bash
codedoctor scan . --fix
```

This may run tools like:

- `ruff check . --fix`
- `black .`

### Skip running tests

```bash
codedoctor scan . --skip-tests
```

---

## Exit codes (for CI)

CodeDoctor uses simple exit codes so it can be used in CI:

- **0** — all checks PASS
- **1** — at least one WARN, and no FAIL
- **2** — one or more FAIL

---

## Notes (Windows + pytest warnings)

On Windows, `pytest` may sometimes print messages like:

- `Exception ignored in atexit callback`
- `PermissionError: [WinError 5] Access is denied`

Even if tests pass, CodeDoctor may classify the result as **WARN** so the run is
not marked as perfectly clean.

---

## Contributing

PRs welcome. A typical workflow:

```bash
python -m pip install -e ".[dev]"
pre-commit run --all-files
pytest -q
```

---

## License

MIT — see [LICENSE](./LICENSE).