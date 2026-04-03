# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Sentinel Report Engine — Ruff-inspired CLI output for Zenzic."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.markup import escape as _esc
from rich.panel import Panel
from rich.table import Table

from zenzic.ui import AMBER, INDIGO, ROSE, SLATE, emoji, make_sentinel_header


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


def _strip_prefix(rel_path: str, line_no: int, message: str) -> str:
    """Remove the redundant 'relpath:lineno: ' prefix already shown in the file header."""
    if line_no > 0:
        prefix = f"{rel_path}:{line_no}: "
        if message.startswith(prefix):
            return message[len(prefix) :]
    return message


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
        docs_count: int = 0,
        assets_count: int = 0,
        engine: str = "auto",
        security_events: int = 0,
        target: str | None = None,
    ) -> tuple[int, int]:
        """Print the full Sentinel Report.

        Returns:
            ``(error_count, warning_count)`` so the caller can decide the
            exit code.
        """
        errors = sum(1 for f in findings if f.severity == "error")
        warnings = sum(1 for f in findings if f.severity == "warning")

        # ── Banner ────────────────────────────────────────────────────────────
        self._con.print()
        header = make_sentinel_header(
            version,
            engine=engine,
            docs_count=docs_count,
            assets_count=assets_count,
            elapsed=elapsed,
            target=target,
        )
        self._con.print(
            Panel(
                header,
                border_style=f"bold {INDIGO}",
                expand=True,
                padding=(0, 2),
            )
        )
        self._con.print()

        # ── Security ─────────────────────────────────────────────────────────
        if security_events:
            self._con.print(
                f"[bold red]{emoji('shield')} SECURITY CRITICAL:[/] {security_events} "
                f"credential(s) detected — rotate immediately.\n"
            )

        if not findings:
            self._con.print(f"[green]{emoji('check')} All checks passed.[/]")
            return 0, 0

        # ── Grouped findings ─────────────────────────────────────────────────
        grouped: dict[str, list[Finding]] = defaultdict(list)
        for f in findings:
            grouped[f.rel_path].append(f)

        for rel_path in sorted(grouped):
            self._con.print(f"[bold underline]{rel_path}[/]")
            for f in sorted(grouped[rel_path], key=lambda x: (x.line_no, x.code)):
                style = _SEVERITY_STYLE.get(f.severity, "dim")
                sev_icon = (
                    emoji("cross")
                    if f.severity == "error"
                    else emoji("warn")
                    if f.severity == "warning"
                    else emoji("info")
                )
                loc = f"{f.line_no}:" if f.line_no else "–"
                msg = _esc(_strip_prefix(f.rel_path, f.line_no, f.message))
                self._con.print(
                    f"  [{style}]{sev_icon}[/] [dim]{loc:<6}[/] [{style}]\\[{f.code}][/]  {msg}"
                )
                if f.source_line:
                    # Gutter — rustc/ruff style.
                    # 4-char prefix keeps │ at the same column on blank+source lines.
                    self._con.print(f"    [{SLATE}]│[/]")
                    self._con.print(
                        f"[{SLATE}]{f.line_no:>3} │[/] [italic]{_esc(f.source_line)}[/]"
                    )
                    self._con.print(f"    [{SLATE}]│[/]")
            self._con.print()

        # ── Summary table ────────────────────────────────────────────────────
        summary = Table.grid(padding=(0, 1))
        summary.add_column(style="bold")
        summary.add_column()
        if errors:
            summary.add_row(
                f"[{ROSE}]{emoji('cross')}[/]",
                f"[{ROSE}]{errors}[/] error{'s' if errors != 1 else ''}",
            )
        if warnings:
            summary.add_row(
                f"[{AMBER}]{emoji('warn')}[/]",
                f"[{AMBER}]{warnings}[/] warning{'s' if warnings != 1 else ''}",
            )
        n_files = len(grouped)
        summary.add_row(
            f"[{SLATE}]{emoji('dot')}[/]",
            f"[{INDIGO}]{n_files}[/] [dim]file{'s' if n_files != 1 else ''} with findings[/]",
        )
        self._con.print(summary)
        return errors, warnings

    # ── Quiet mode (pre-commit) ──────────────────────────────────────────────

    def render_quiet(self, findings: list[Finding]) -> tuple[int, int]:
        """Minimal one-line output for pre-commit hooks."""
        errors = sum(1 for f in findings if f.severity == "error")
        warnings = sum(1 for f in findings if f.severity == "warning")
        if errors or warnings:
            self._con.print(f"zenzic: {errors} error(s), {warnings} warning(s)")
        return errors, warnings
