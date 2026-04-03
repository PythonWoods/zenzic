# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Sentinel Report Engine — Ruff-inspired CLI output for Zenzic."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console


@dataclass(slots=True)
class Finding:
    """Normalized finding for display grouping."""

    rel_path: str
    line_no: int  # 0 = file-level finding
    code: str
    severity: str  # "error", "warning", "info"
    message: str
    source_line: str = ""


_SEVERITY_STYLE: dict[str, str] = {
    "error": "bold red",
    "warning": "yellow",
    "info": "blue",
}


class SentinelReporter:
    """Render check results as a Ruff-inspired grouped report."""

    def __init__(self, console: Console, docs_root: Path) -> None:
        self._con = console
        self._docs_root = docs_root

    def _rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self._docs_root))
        except ValueError:
            return str(path)

    # ── Full report ───────────────────────────────────────────────────────────

    def render(
        self,
        findings: list[Finding],
        *,
        version: str,
        elapsed: float,
        file_count: int,
        engine: str = "auto",
        security_events: int = 0,
    ) -> tuple[int, int]:
        """Print the full Sentinel Report.

        Returns:
            ``(error_count, warning_count)`` so the caller can decide the
            exit code.
        """
        errors = sum(1 for f in findings if f.severity == "error")
        warnings = sum(1 for f in findings if f.severity == "warning")

        # ── Banner ────────────────────────────────────────────────────────────
        self._con.print(f"\n[bold]zenzic[/] {version}")
        self._con.print(
            f"[dim]Engine: {engine} · Scanned {file_count} file(s) · {elapsed:.1f}s[/]\n"
        )

        # ── Security ─────────────────────────────────────────────────────────
        if security_events:
            self._con.print(
                f"[bold red]SECURITY CRITICAL:[/] {security_events} "
                f"credential(s) detected — rotate immediately.\n"
            )

        if not findings:
            self._con.print("[green]All checks passed.[/]")
            return 0, 0

        # ── Grouped findings ─────────────────────────────────────────────────
        grouped: dict[str, list[Finding]] = defaultdict(list)
        for f in findings:
            grouped[f.rel_path].append(f)

        for rel_path in sorted(grouped):
            self._con.print(f"[bold underline]{rel_path}[/]")
            for f in sorted(grouped[rel_path], key=lambda x: (x.line_no, x.code)):
                style = _SEVERITY_STYLE.get(f.severity, "dim")
                loc = f"{f.line_no}:" if f.line_no else "  –"
                self._con.print(
                    f"  [dim]{loc:<6}[/][{style}]{f.severity:<8}[/][bold]{f.code:<12}[/]{f.message}"
                )
                if f.source_line:
                    self._con.print(f"        [dim]│[/] [italic]{f.source_line}[/]")
            self._con.print()

        # ── Summary ──────────────────────────────────────────────────────────
        parts: list[str] = []
        if errors:
            parts.append(f"[bold red]{errors} error{'s' if errors != 1 else ''}[/]")
        if warnings:
            parts.append(f"[yellow]{warnings} warning{'s' if warnings != 1 else ''}[/]")
        n_files = len(grouped)
        self._con.print(f"Found {', '.join(parts)} in {n_files} file{'s' if n_files != 1 else ''}.")
        return errors, warnings

    # ── Quiet mode (pre-commit) ──────────────────────────────────────────────

    def render_quiet(self, findings: list[Finding]) -> tuple[int, int]:
        """Minimal one-line output for pre-commit hooks."""
        errors = sum(1 for f in findings if f.severity == "error")
        warnings = sum(1 for f in findings if f.severity == "warning")
        if errors or warnings:
            self._con.print(f"zenzic: {errors} error(s), {warnings} warning(s)")
        return errors, warnings
