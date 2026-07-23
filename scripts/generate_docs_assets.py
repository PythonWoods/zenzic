# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""
generate_docs_assets.py — Zenzic

Generates SVG terminal assets for the documentation using Rich's native
SVG export with the agnostic brand color system.

Run from the zenzic-doc root:

    python scripts/generate_docs_assets.py

Output: static/assets/terminal/
    - integrity-clean.svg     — 100/100 Integrity Seal
    - security-breach.svg     — Z201 Security Breach
    - quality-findings.svg    — Diagnostic report (3 findings, score 67/100)

Requirements: rich (already a transitive dep via zenzic)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.terminal_theme import TerminalTheme
from rich.text import Text


def _resolve_core_src_for_acl(root: Path) -> Path:
    """Resolve local core source path for fail-closed ACL imports."""
    candidates: list[str] = []

    env_override = os.environ.get("ZENZIC_CORE_PATH")
    if env_override:
        candidates.append(env_override)
    candidates.extend(["_zenzic_core", "../zenzic"])

    checked: list[str] = []
    for raw in candidates:
        base = Path(raw).expanduser()
        if not base.is_absolute():
            base = (root / base).resolve()
        else:
            base = base.resolve()
        checked.append(str(base))

        src_candidate = base / "src"
        if (src_candidate / "zenzic").is_dir():
            return src_candidate

        if (base / "zenzic").is_dir():
            return base

    checked_lines = "\n".join(f"- {item}" for item in checked)
    raise ModuleNotFoundError(
        "Unable to import zenzic.core.regex in fail-closed mode.\n"
        "Required precedence: ZENZIC_CORE_PATH -> ./_zenzic_core -> ../zenzic\n"
        "Each candidate must contain src/zenzic.\n"
        f"Checked candidates:\n{checked_lines}\n"
        "PyPI fallback is prohibited for docs tooling."
    )


_REPO_ROOT = Path(__file__).resolve().parent.parent
_CORE_SRC = _resolve_core_src_for_acl(_REPO_ROOT)
if str(_CORE_SRC) not in sys.path:
    sys.path.insert(0, str(_CORE_SRC))

# Fail-closed ACL policy: tooling uses the same RE2 facade as core.
from zenzic.core import regex as re  # noqa: E402


OUT = Path(__file__).parent.parent / "static" / "assets" / "terminal"
OUT.mkdir(parents=True, exist_ok=True)

WIDTH = 76  # characters — matches narrow terminal for docs readability

# ── Core Brand Theme ───────────────────────────────────────────────────────
# Exact Zenzic brand colors for SVG export — matches zenzic-brand-system.html
# Background: #09090b (Core Lead), Foreground: #E2E8F0 (Ghost)
ZENZIC_THEME = TerminalTheme(
    background=(9, 9, 11),  # #09090b — Core Lead
    foreground=(226, 232, 240),  # #E2E8F0 — Ghost (primary text)
    normal=[
        (9, 9, 11),  # black → Core
        (255, 59, 48),  # red → Breach Red
        (16, 185, 129),  # green → Success (Emerald)
        (245, 158, 11),  # yellow → Warning (Amber)
        (56, 189, 248),  # blue → Harbor Cyan
        (255, 45, 115),  # magenta → Signal Magenta
        (56, 189, 248),  # cyan → Harbor Cyan
        (226, 232, 240),  # white → Ghost
    ],
    bright=[
        (15, 15, 19),  # bright black → #0f0f13 Void
        (244, 63, 94),  # bright red → Rose (Error)
        (52, 211, 153),  # bright green → Emerald-400
        (251, 191, 36),  # bright yellow → Amber-400
        (79, 70, 229),  # bright blue → Core Indigo
        (167, 139, 250),  # bright magenta → Violet-400
        (125, 211, 252),  # bright cyan → Sky-300
        (248, 250, 252),  # bright white → Slate-50
    ],
)

# ── SVG chrome stripper ─────────────────────────────────────────────────────
# Rich's export_svg() wraps content in a terminal chrome: outer border rect,
# title bar, and 3 traffic-light dots.  The TerminalWindow React component
# provides the single macOS frame — so SVGs must be "naked" (text only).
#
# Invariant: Rich v13+ produces a fixed chrome layout:
#   translate(26,22)  → dot circles group
#   translate(9, 41)  → content group (41px = title bar height)
# These constants are verified across all 3 SVG assets.

_CHROME_RECT_RE = re.compile(r'\s*<rect[^>]*stroke="[^"]*"[^>]*/>\n?')
_DOTS_GROUP_RE = re.compile(
    r'\s*<g transform="translate\(26,22\)">.*?</g>\n?',
    re.DOTALL,
)
_CONTENT_TRANSLATE_RE = re.compile(r"translate\(9, 41\)")
_VIEWBOX_HEIGHT_RE = re.compile(r'(viewBox="0 0 \d+ )([\d.]+)(")')

# Title bar occupies 41px; content shifts up to y=8 (leaves 8px top padding).
_CHROME_HEIGHT = 41 - 8  # = 33 px removed from the viewBox


def _strip_chrome(raw: str) -> str:
    """Remove Rich's terminal chrome, leaving naked text on #09090b background."""
    # 1. Remove the stroked outer border rect (Rich's terminal window chrome).
    raw = _CHROME_RECT_RE.sub("\n", raw, count=1)
    # 2. Inject a clean, stroke-free background rect immediately after <style>.
    raw = raw.replace(
        "    <defs>",
        '    <rect width="100%" height="100%" fill="#09090b"/>\n    <defs>',
        1,
    )
    # 3. Remove the 3 traffic-light dot circles.
    raw = _DOTS_GROUP_RE.sub("\n", raw, count=1)
    # 4. Shift content up, eliminating the title bar space.
    raw = _CONTENT_TRANSLATE_RE.sub("translate(9, 8)", raw, count=1)
    # 5. Shrink the viewBox height to match (remove 33px title bar).
    raw = _VIEWBOX_HEIGHT_RE.sub(
        lambda m: f"{m.group(1)}{float(m.group(2)) - _CHROME_HEIGHT:.1f}{m.group(3)}",
        raw,
        count=1,
    )
    return raw


# ── helpers ────────────────────────────────────────────────────────────────


def _make_console() -> Console:
    return Console(record=True, width=WIDTH, force_terminal=True, highlight=False)


def _save(console: Console, name: str) -> None:
    raw = console.export_svg(title="", theme=ZENZIC_THEME)
    raw = _strip_chrome(raw)
    (OUT / name).write_text(raw, encoding="utf-8")
    print(f"  ✔  {name}")


# ── Asset 1: Integrity Seal — 100/100 clean ────────────────────────────────


def gen_integrity_clean() -> None:
    c = _make_console()

    c.print()
    table = Table(
        box=box.SIMPLE,
        show_header=False,
        show_edge=False,
        padding=(0, 1),
        expand=True,
    )
    table.add_column(style="bright_green", no_wrap=True)
    table.add_column(style="dim white", no_wrap=True)
    table.add_column(style="bright_white", justify="right", no_wrap=True)
    table.add_row("✔  Link Integrity", "35 pts", "0 broken links")
    table.add_row("✔  Orphan Detection", "20 pts", "0 orphaned pages")
    table.add_row("✔  Snippet Validation", "20 pts", "0 broken snippets")
    table.add_row("✔  Content Quality", "15 pts", "0 placeholders")
    table.add_row("✔  Asset Integrity", "10 pts", "0 missing assets")
    c.print(table)

    c.print()
    c.rule(style="bright_cyan")
    score_line = Text()
    score_line.append("    🏆  Quality Score:  ", style="bright_white")
    score_line.append("100 / 100", style="bold bright_cyan")
    score_line.append("   ◆  Integrity Seal", style="bright_cyan")
    c.print(score_line)
    c.rule(style="bright_cyan")
    c.print()

    c.print("  [bright_green]✔[/]  Security: no credentials detected")
    c.print("  [bright_green]✔[/]  Path Defense: no path-traversal attempts")
    meta = Text()
    meta.append("  Files scanned: 47", style="dim")
    meta.append("    Elapsed: 0.28 s", style="dim")
    c.print(meta)
    c.print()

    _save(c, "integrity-clean.svg")


# ── Asset 2: Security Breach — Z201 ────────────────────────────────────────


def gen_security_breach() -> None:
    c = _make_console()

    c.print()
    title = Text(" SECURITY BREACH DETECTED ", style="bold bright_white on red")
    c.print(Panel(title, style="red", expand=True, padding=(0, 0)))
    c.print()

    c.print(
        "  [red]✘[/]  [dim]Finding:   [/][bright_white]Secret detected (aws-access-key) — rotate immediately.[/]"
    )
    c.print(
        "  [red]✘[/]  [dim]Location:  [/][bright_white]docs/how-to/configure.md:4[/]"
    )
    c.print(
        "  [red]✘[/]  [dim]Credential:[/] [bold red on bright_black] AKIA************MPLE [/]"
    )
    c.print()
    c.print("  [dim]Exit code [bold]2[/] — this finding is never suppressible.[/]")
    c.print(
        "  [dim]Rotate the credential, then run [italic]zenzic check all[/] to verify.[/]"
    )
    c.print()

    _save(c, "security-breach.svg")


# ── Asset 3: Diagnostic findings — 3 errors, score 67/100 ─────────────────


def gen_quality_findings() -> None:
    c = _make_console()

    c.print()
    c.print(
        "  [red]✘[/]  [dim]Z101[/]  [cyan]docs/guides/setup.md:14[/]"
        "      [white]Broken link → 'install.md' (target not found)[/]"
    )
    c.print(
        "  [red]✘[/]  [dim]Z402[/]  [cyan]docs/guides/old-api.md[/]"
        "        [white]Orphan page — not reachable from any navigation[/]"
    )
    c.print(
        "  [yellow]⚠[/]  [dim]Z501[/]  [cyan]docs/reference/config.md:3[/]"
        '   [white]Placeholder: "TODO: describe this parameter"[/]'
    )
    c.print()
    c.rule(style="dim")
    c.print(
        "  [red]3 errors[/]   [yellow]0 warnings[/]"
        "   [bright_white]Score: [bold]67 / 100[/][/]"
        "   Files: 42   Elapsed: 0.31 s"
    )
    c.print()

    _save(c, "quality-findings.svg")


# ── main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\nGenerating SVG assets → {OUT}\n")
    gen_integrity_clean()
    gen_security_breach()
    gen_quality_findings()
    print(f"\nDone. {len(list(OUT.glob('*.svg')))} SVG files in {OUT}\n")
