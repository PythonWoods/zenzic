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

from zenzic.ui import AMBER, BLOOD, EMERALD, INDIGO, ROSE, SLATE, ObsidianUI, emoji


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
    "security_breach": f"bold white on {ROSE}",
    "security_incident": f"bold white on {BLOOD}",
}


def _obfuscate_secret(raw: str) -> str:
    """Partially redact a secret for safe display in logs and CI output.

    Preserves the first four and last four characters so reviewers can
    identify the secret type and suffix without exposing the full credential.
    Strings of length ≤ 8 are fully redacted.

    This function is the only place where raw secret material is allowed
    to be formatted for human consumption.  It **must never** be bypassed.

    Args:
        raw: The raw matched secret string from the Shield.

    Returns:
        A partially-redacted string safe for log output.
    """
    if len(raw) <= 8:  # too short to redact partially — hide the whole thing
        return "*" * len(raw)
    return raw[:4] + "*" * (len(raw) - 8) + raw[-4:]


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
        target: str | None = None,
        strict: bool = False,
        ok_message: str | None = None,
        show_info: bool = False,
    ) -> tuple[int, int]:
        """Print the full Sentinel Report.

        Breach findings (``severity=="security_breach"``) are rendered as
        dedicated red panels **before** the grouped findings section and are
        excluded from the grouped view to avoid noise.  All other findings flow
        through the normal grouped pipeline.

        Args:
            ok_message: Optional success message shown when no hard failures are
                found.  Defaults to ``"All checks passed. Your documentation is
                secure."`` (all-clear panel) or ``"All checks passed."`` (with
                warnings).  Individual commands should pass a specific message
                such as ``"No broken links found."``.

        Returns:
            ``(error_count, warning_count)`` — breaches are counted separately
            by the caller (``cli.py``) and cause Exit 2, not Exit 1.
        """
        errors = sum(1 for f in findings if f.severity == "error")
        warnings = sum(1 for f in findings if f.severity == "warning")

        # ── Split: breach findings get dedicated panels; rest goes to the grouped view
        breach_findings = [f for f in findings if f.severity == "security_breach"]
        normal_findings = [f for f in findings if f.severity != "security_breach"]

        # ── Info filter: suppress advisory findings unless opt-in ─────────────
        if not show_info:
            _info = [f for f in normal_findings if f.severity == "info"]
            normal_findings = [f for f in normal_findings if f.severity != "info"]
            info_count = len(_info)
        else:
            info_count = 0

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
            if total:
                throughput = total / elapsed
                parts.append(f"[{INDIGO}]{throughput:.0f}[/] files/s")
        telemetry = Text.from_markup(f"[{SLATE}]{f' {dot} '.join(parts)}[/]")

        # ── Security breach panels (rendered BEFORE main panel) ───────────────
        if breach_findings:
            for bf in breach_findings:
                obfuscated = _obfuscate_secret(bf.match_text) if bf.match_text else "[redacted]"
                breach_body = Group(
                    Text.from_markup(f"  {emoji('cross')} [bold]Finding:[/]    {_esc(bf.message)}"),
                    Text.from_markup(
                        f"  {emoji('cross')} [bold]Location:[/]   "
                        f"[bold]{_esc(self._full_rel(bf.rel_path))}[/]:{bf.line_no}"
                    ),
                    Text.from_markup(
                        f"  {emoji('cross')} [bold]Credential:[/] "
                        f"[bold reverse] {_esc(obfuscated)} [/]"
                    ),
                    Text(),
                    Text.from_markup(
                        "  [bold]Action:[/] Rotate this credential immediately "
                        "and purge it from the repository history."
                    ),
                )
                self._con.print()
                self._con.print(
                    Panel(
                        breach_body,
                        title=f"[bold white on {ROSE}]  SECURITY BREACH DETECTED  ",
                        title_align="center",
                        border_style=f"bold {ROSE}",
                        padding=(1, 2),
                        expand=True,
                    )
                )

        if not normal_findings and not breach_findings:
            # ── All-clear panel ───────────────────────────────────────────────
            _ok = ok_message or (
                f"[bold {EMERALD}]Obsidian Seal:[/bold {EMERALD}]"
                f" [{EMERALD}]All statically-detectable links, credentials,"
                f" and references verified.[/{EMERALD}]"
            )
            _ok_items: list[RenderableType] = [
                telemetry,
                Text(),
                Rule(style=SLATE),
                Text(),
                Text.from_markup(f"{emoji('sparkles')} {_ok}")
                if not ok_message
                else Text.from_markup(f"[{EMERALD}]{emoji('check')} {_ok}[/]"),
            ]
            if info_count:
                _ok_items.append(Text())
                _ok_items.append(
                    Text.from_markup(
                        f"  [{SLATE}]{emoji('info')} {info_count} info finding"
                        f"{'s' if info_count != 1 else ''} suppressed"
                        f" — use --show-info for details.[/]"
                    )
                )
            self._con.print()
            self._con.print(ObsidianUI.make_panel(Group(*_ok_items)))
            return 0, 0

        # ── Grouped findings (non-breach only) ───────────────────────────────
        grouped: dict[str, list[Finding]] = defaultdict(list)
        for f in normal_findings:
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
                    if f.severity in {"error", "security_incident"}
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
                    if snippet_lines:
                        renderables.extend(snippet_lines)
                    else:
                        # Fallback: file unreadable, use source_line directly
                        gutter_w = len(str(f.line_no))
                        t = Text()
                        t.append(f"    {str(f.line_no).rjust(gutter_w)}  ", style=SLATE)
                        t.append("❱  ", style=f"bold {ROSE}")
                        t.append(f.source_line)
                        renderables.append(t)

            renderables.append(Text())  # spacing after file group

        # ── Summary (inside the panel) ────────────────────────────────────────
        renderables.append(Rule(style=SLATE))
        renderables.append(Text())  # breathing after Rule
        summary_parts: list[str] = []
        incidents_count = sum(1 for f in normal_findings if f.severity == "security_incident")
        if incidents_count:
            summary_parts.append(
                f"[bold white on {BLOOD}]{emoji('cross')} {incidents_count}"
                f" security incident{'s' if incidents_count != 1 else ''}[/]"
            )
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
        has_failures = (incidents_count > 0) or (errors > 0) or (strict and warnings > 0)
        if has_failures:
            renderables.append(
                Text.from_markup(f"[bold {ROSE}]FAILED:[/] One or more checks failed.")
            )
        else:
            _ok = ok_message or (
                f"[bold {EMERALD}]Obsidian Seal:[/bold {EMERALD}]"
                f" [{EMERALD}]All statically-detectable links, credentials,"
                f" and references verified.[/{EMERALD}]"
            )
            renderables.append(
                Text.from_markup(f"{emoji('sparkles')} {_ok}")
                if not ok_message
                else Text.from_markup(f"[{EMERALD}]{emoji('check')} {_ok}[/]")
            )

        if info_count:
            renderables.append(Text())
            renderables.append(
                Text.from_markup(
                    f"  [{SLATE}]{emoji('info')} {info_count} info finding"
                    f"{'s' if info_count != 1 else ''} suppressed"
                    f" — use --show-info for details.[/]"
                )
            )

        # ── Single unified panel ──────────────────────────────────────────────
        self._con.print()
        self._con.print(ObsidianUI.make_panel(Group(telemetry, Text(), *renderables)))
        # ── Usage hint (outside the audit box) ───────────────────────────────
        self._con.print(Text.from_markup(f"[{SLATE}]Try 'zenzic check --help' for options.[/]"))
        return errors, warnings

    # ── Quiet mode (pre-commit) ──────────────────────────────────────────────

    def render_quiet(self, findings: list[Finding]) -> tuple[int, int]:
        """Minimal output for pre-commit hooks.

        Breach findings always produce a one-liner even in quiet mode — silent
        failure on a credential leak is more dangerous than noisy CI output.
        """
        breaches = [f for f in findings if f.severity == "security_breach"]
        errors = sum(1 for f in findings if f.severity == "error")
        warnings = sum(1 for f in findings if f.severity == "warning")
        if breaches:
            self._con.print(
                f"[bold red]SECURITY CRITICAL:[/] {len(breaches)} secret(s) detected — "
                f"rotate immediately. Exit 2."
            )
        if errors or warnings:
            self._con.print(f"zenzic: {errors} error(s), {warnings} warning(s)")
        return errors, warnings
