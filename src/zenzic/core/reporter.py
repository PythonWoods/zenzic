# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Sentinel Report Engine — Ruff-inspired CLI output for Zenzic."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console, Group, RenderableType
from rich.markup import escape as _esc
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from zenzic.ui import AMBER, EMERALD, INDIGO, ROSE, SLATE, emoji


@dataclass(slots=True)
class Finding:
    """Normalized finding for display grouping."""

    rel_path: str
    line_no: int  # 0 = file-level finding
    code: str
    severity: str  # "error", "warning", "info"
    message: str
    source_line: str = ""
    col_start: int = 0
    match_text: str = ""


_SEVERITY_STYLE: dict[str, str] = {
    "error": f"bold {ROSE}",
    "warning": f"bold {AMBER}",
    "info": f"bold {INDIGO}",
}


def _strip_prefix(rel_path: str, line_no: int, message: str) -> str:
    """Remove the redundant 'relpath:lineno: ' prefix already shown in the file header."""
    if line_no > 0:
        prefix = f"{rel_path}:{line_no}: "
        if message.startswith(prefix):
            return message[len(prefix) :]
    return message


# Context lines to show before/after the error line in snippets.
_CONTEXT_LINES = 2


def _read_snippet(path: Path, line_no: int) -> tuple[list[str], int] | None:
    """Read a few lines around *line_no* from *path*, or ``None`` on failure."""
    try:
        all_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    if not all_lines or line_no < 1:
        return None
    start = max(0, line_no - 1 - _CONTEXT_LINES)
    end = min(len(all_lines), line_no + _CONTEXT_LINES)
    return all_lines[start:end], start + 1


def _render_snippet(
    abs_path: Path, line_no: int, *, col_start: int = 0, match_text: str = ""
) -> list[Text]:
    """Render code snippet with custom ``│ ❱`` gutter and targeted ``^^^^`` carets.

    Carets are rendered **only** when the caller provides a non-empty
    *match_text* with a valid *col_start* — i.e. when the checker natively
    knows the exact token position.  No guessing, no regex heuristics.
    """
    snippet = _read_snippet(abs_path, line_no)
    if snippet is None:
        return []

    lines, start_line = snippet
    end_line_no = start_line + len(lines) - 1
    gutter_w = len(str(end_line_no))
    result: list[Text] = []

    for i, src in enumerate(lines):
        cur = start_line + i
        is_err = cur == line_no
        num = str(cur).rjust(gutter_w)

        t = Text()
        t.append(f"    {num}  ", style=SLATE)
        if is_err:
            t.append("❱  ", style=f"bold {ROSE}")
            t.append(src)
        else:
            t.append("│  ", style=SLATE)
            t.append(src, style="dim")
        result.append(t)

        # Surgical caret: only when the checker provided native position data
        # and the caret won't be misaligned by terminal line-wrapping.
        if is_err and match_text and col_start >= 0:
            caret_len = len(match_text)
            if col_start + caret_len <= 60:
                ct = Text()
                ct.append(f"    {' ' * gutter_w}  ", style=SLATE)
                ct.append("│  ", style=SLATE)
                ct.append(" " * col_start + "^" * caret_len, style=f"bold {ROSE}")
                result.append(ct)

    return result

    return result


class SentinelReporter:
    """Render check results as a Ruff-inspired grouped report."""

    def __init__(self, console: Console, docs_root: Path, *, docs_dir: str = "docs") -> None:
        self._con = console
        self._docs_root = docs_root
        self._docs_dir = docs_dir

    def _full_rel(self, rel_path: str) -> str:
        """Return project-relative path including docs_dir prefix."""
        return f"{self._docs_dir}/{rel_path}"

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
        strict: bool = False,
    ) -> tuple[int, int]:
        """Print the full Sentinel Report.

        Returns:
            ``(error_count, warning_count)`` so the caller can decide the
            exit code.
        """
        errors = sum(1 for f in findings if f.severity == "error")
        warnings = sum(1 for f in findings if f.severity == "warning")

        # ── Telemetry line ────────────────────────────────────────────────────
        dot = emoji("dot")
        total = docs_count + assets_count
        parts = [engine]
        if target is not None:
            parts.append(target)
        if total:
            breakdown = f"([{INDIGO}]{docs_count}[/] docs, [{INDIGO}]{assets_count}[/] assets)"
            parts.append(f"[{INDIGO}]{total}[/] file{'s' if total != 1 else ''} {breakdown}")
        if elapsed:
            parts.append(f"[{INDIGO}]{elapsed:.1f}[/]s")
        telemetry = Text.from_markup(f"[{SLATE}]{f' {dot} '.join(parts)}[/]")

        if not findings:
            # ── All-clear panel ───────────────────────────────────────────────
            self._con.print()
            self._con.print(
                Panel(
                    Group(
                        telemetry,
                        Text(),
                        Rule(style=SLATE),
                        Text(),
                        Text.from_markup(
                            f"[{EMERALD}]{emoji('check')} All checks passed. "
                            f"Your documentation is secure.[/]"
                        ),
                    ),
                    title=f"[bold white on {INDIGO}] {emoji('shield')}  ZENZIC SENTINEL  v{version} [/]",
                    title_align="center",
                    border_style=f"bold {INDIGO}",
                    padding=(1, 2),
                    expand=True,
                )
            )
            return 0, 0

        # ── Security ──────────────────────────────────────────────────────────
        security_line: list[RenderableType] = []
        if security_events:
            security_line = [
                Text.from_markup(
                    f"[{ROSE}]{emoji('shield')} SECURITY CRITICAL:[/] {security_events} "
                    f"credential(s) detected — rotate immediately."
                ),
                Text(),
            ]

        # ── Grouped findings ──────────────────────────────────────────────────
        grouped: dict[str, list[Finding]] = defaultdict(list)
        for f in findings:
            grouped[f.rel_path].append(f)

        renderables: list[RenderableType] = []
        for rel_path in sorted(grouped):
            abs_path = self._docs_root / rel_path
            # File separator — Rule with full project-relative path
            renderables.append(Rule(self._full_rel(rel_path), style=SLATE))
            renderables.append(Text())  # breathing after Rule

            for idx, f in enumerate(sorted(grouped[rel_path], key=lambda x: (x.line_no, x.code))):
                if idx > 0:
                    renderables.append(Text())  # breathing between findings

                sev_icon = (
                    emoji("cross")
                    if f.severity == "error"
                    else emoji("warn")
                    if f.severity == "warning"
                    else emoji("info")
                )
                style = _SEVERITY_STYLE.get(f.severity, "dim")
                msg = _strip_prefix(f.rel_path, f.line_no, f.message)
                # Finding line
                renderables.append(
                    Text.from_markup(
                        f"  [{style}]{sev_icon}[/] [{style}]\\[{f.code}][/]  {_esc(msg)}"
                    )
                )
                # Snippet with native position data — no guessing
                if f.line_no and f.source_line:
                    renderables.append(Text())  # breathing before snippet
                    snippet_lines = _render_snippet(
                        abs_path,
                        f.line_no,
                        col_start=f.col_start,
                        match_text=f.match_text,
                    )
                    renderables.extend(snippet_lines)

            renderables.append(Text())  # spacing after file group

        # ── Summary (inside the panel) ────────────────────────────────────────
        renderables.append(Rule(style=SLATE))
        renderables.append(Text())  # breathing after Rule
        summary_parts: list[str] = []
        if errors:
            summary_parts.append(
                f"[{ROSE}]{emoji('cross')} {errors} error{'s' if errors != 1 else ''}[/]"
            )
        if warnings:
            summary_parts.append(
                f"[{AMBER}]{emoji('warn')} {warnings} warning{'s' if warnings != 1 else ''}[/]"
            )
        n_files = len(grouped)
        summary_parts.append(
            f"[{SLATE}]{emoji('dot')} {n_files} file{'s' if n_files != 1 else ''} with findings[/]"
        )
        renderables.append(Text.from_markup("  ".join(summary_parts)))

        # ── Status line (verdict) ─────────────────────────────────────────────
        renderables.append(Text())  # breathing before verdict
        has_failures = (errors > 0) or (strict and warnings > 0)
        if has_failures:
            renderables.append(
                Text.from_markup(f"[bold {ROSE}]FAILED:[/] One or more checks failed.")
            )
        else:
            renderables.append(
                Text.from_markup(f"[{EMERALD}]{emoji('check')} All checks passed.[/]")
            )

        # ── Single unified panel ──────────────────────────────────────────────
        self._con.print()
        self._con.print(
            Panel(
                Group(telemetry, Text(), *security_line, *renderables),
                title=f"[bold white on {INDIGO}] {emoji('shield')}  ZENZIC SENTINEL  v{version} [/]",
                title_align="center",
                border_style=f"bold {INDIGO}",
                padding=(1, 2),
                expand=True,
            )
        )
        # ── Usage hint (outside the audit box) ───────────────────────────────
        self._con.print(Text.from_markup(f"[{SLATE}]Try 'zenzic check --help' for options.[/]"))
        return errors, warnings

    # ── Quiet mode (pre-commit) ──────────────────────────────────────────────

    def render_quiet(self, findings: list[Finding]) -> tuple[int, int]:
        """Minimal one-line output for pre-commit hooks."""
        errors = sum(1 for f in findings if f.severity == "error")
        warnings = sum(1 for f in findings if f.severity == "warning")
        if errors or warnings:
            self._con.print(f"zenzic: {errors} error(s), {warnings} warning(s)")
        return errors, warnings
