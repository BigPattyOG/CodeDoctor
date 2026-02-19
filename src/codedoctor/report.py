from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CheckStatus(str, Enum):
    PASS = "PASS"  # nosec B105
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass(frozen=True)
class CheckResult:
    name: str
    command: list[str]
    returncode: int
    output: str
    status: CheckStatus

    @property
    def ok(self) -> bool:
        return self.status in {CheckStatus.PASS, CheckStatus.WARN}


@dataclass(frozen=True)
class ScanReport:
    repo: str
    results: list[CheckResult]

    @property
    def ok(self) -> bool:
        return all(r.ok for r in self.results)

    @property
    def has_failures(self) -> bool:
        return any(r.status == CheckStatus.FAIL for r in self.results)

    @property
    def has_warnings(self) -> bool:
        return any(r.status == CheckStatus.WARN for r in self.results)

    @property
    def overall_status(self) -> CheckStatus:
        if self.has_failures:
            return CheckStatus.FAIL
        if self.has_warnings:
            return CheckStatus.WARN
        return CheckStatus.PASS

    @property
    def exit_code(self) -> int:
        if self.has_failures:
            return 2
        if self.has_warnings:
            return 1
        return 0

    def to_tldr(self) -> str:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == CheckStatus.PASS)
        warned = sum(1 for r in self.results if r.status == CheckStatus.WARN)
        failed = sum(1 for r in self.results if r.status == CheckStatus.FAIL)

        lines: list[str] = []
        lines.append("CodeDoctor Report TL;DR")
        lines.append("----------------------")
        lines.append(f"Overall: {self.overall_status.value}")
        lines.append(
            f"Checks:  {passed} passed / {warned} warned / {failed} failed / "
            f"{total} total"
        )
        lines.append("")

        if failed:
            lines.append("Failures:")
            for r in self.results:
                if r.status == CheckStatus.FAIL:
                    lines.append(f" - {r.name}")
            lines.append("")

        if warned:
            lines.append("Warnings:")
            for r in self.results:
                if r.status == CheckStatus.WARN:
                    lines.append(f" - {r.name}")
            lines.append("")

        return "\n".join(lines)

    def to_full_text(self) -> str:
        lines: list[str] = []
        lines.append(self.to_tldr())
        lines.append(f"Repository: {self.repo}")
        lines.append("")
        lines.append("Details")
        lines.append("-------")
        lines.append("")

        for r in self.results:
            lines.append(f"== {r.name} : {r.status.value} ==")
            if r.command:
                lines.append(f"$ {' '.join(r.command)}")
            lines.append(r.output if r.output else "(no output)")
            lines.append("")

        lines.append("Next steps:")
        lines.append(" - Re-run with safe auto-fixes: codedoctor scan . --fix")
        lines.append("")
        return "\n".join(lines)

    def to_human_text(self) -> str:
        return self.to_full_text()
