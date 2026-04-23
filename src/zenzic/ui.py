# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Sentinel Palette — brand constants, terminal detection, and UI helpers.

This module centralises all visual identity decisions for the Zenzic CLI.
Every colour, emoji map, and graceful degradation rule lives here so that
the rest of the codebase can call ``ui.INDIGO`` or ``ui.emoji("check")``
without worrying about CI, dumb terminals, or NO_COLOR.
"""

from __future__ import annotations

import os
import sys
from typing import Any

from rich import box as _rich_box
from rich.console import RenderableType
from rich.panel import Panel


# ── Brand colours (Sentinel Palette) ────────────────────────────────────────

INDIGO = "#4f46e5"
SLATE = "#64748b"
EMERALD = "#10b981"
AMBER = "#f59e0b"
ROSE = "#f43f5e"
BLOOD = "#8b0000"  # blood red — system-path traversal security incident

# Rich style strings
STYLE_BRAND = f"bold {INDIGO}"
STYLE_DIM = f"{SLATE}"
STYLE_OK = f"bold {EMERALD}"
STYLE_WARN = f"bold {AMBER}"
STYLE_ERR = f"bold {ROSE}"

# ── Terminal capability detection ───────────────────────────────────────────


def _detect_capabilities() -> tuple[bool, bool]:
    """Detect whether the terminal supports colour and unicode emoji.

    Returns ``(supports_color, supports_emoji)``.

    Heuristics (conservative — false negatives are fine, false positives are not):

    * **NO_COLOR** env var (https://no-color.org/) → colour off.
    * **CI** env var → emoji off (many CI log viewers mangle multi-byte chars).
    * **TERM=dumb** → both off.
    * Not a TTY → colour off (piped output), emoji preserved.
    """
    no_color = bool(os.environ.get("NO_COLOR"))
    is_ci = bool(os.environ.get("CI"))
    term = os.environ.get("TERM", "")
    is_dumb = term == "dumb"
    is_tty = hasattr(sys.stderr, "isatty") and sys.stderr.isatty()

    supports_color = not no_color and not is_dumb and is_tty
    supports_emoji = not is_ci and not is_dumb

    return supports_color, supports_emoji


SUPPORTS_COLOR, SUPPORTS_EMOJI = _detect_capabilities()

# ── Emoji map with ASCII fallback ──────────────────────────────────────────

_EMOJI: dict[str, tuple[str, str]] = {
    # key: (unicode, ascii_fallback)
    "check": ("\u2714", "*"),  # ✔
    "cross": ("\u2718", "x"),  # ✘
    "warn": ("\u26a0", "!"),  # ⚠
    "info": ("\U0001f4a1", "i"),  # 💡
    "shield": ("\U0001f6e1", "#"),  # 🛡
    "bolt": ("\u26a1", ">"),  # ⚡
    "dot": ("\u2022", "-"),  # •
    "arrow": ("\u279c", "->"),  # ➜
    "sparkles": ("\u2728", "*"),  # ✨
}


def emoji(name: str) -> str:
    """Return the emoji for *name*, or its ASCII fallback in degraded terminals."""
    pair = _EMOJI.get(name)
    if pair is None:
        return name
    return pair[0] if SUPPORTS_EMOJI else pair[1]


# ── Banner ──────────────────────────────────────────────────────────────────


def make_banner(version: str) -> str:
    """Return the Zenzic startup banner as a Rich-markup string.

    The banner is wrapped inside a :class:`rich.panel.Panel` by the caller —
    this function only builds the *content* string.
    """
    shield = emoji("shield")
    lines = [
        f"[bold white]{shield}  ZENZIC SENTINEL[/]  [{STYLE_DIM}]v{version}[/]",
        f"[{STYLE_DIM}]Engine-agnostic Markdown integrity & security shield[/]",
    ]
    return "\n".join(lines)


def make_sentinel_header(
    version: str,
    *,
    engine: str = "auto",
    docs_count: int = 0,
    assets_count: int = 0,
    elapsed: float = 0.0,
    target: str | None = None,
) -> str:
    """Return the compact Sentinel Report header for ``check all`` output.

    Used by :class:`~zenzic.core.reporter.SentinelReporter` as the top-of-report
    banner.  Separate from :func:`make_banner` (which is the CLI startup panel).

    Telemetry is unified: *docs_count* (Markdown + engine config files) and
    *assets_count* (images and static files) are shown as a breakdown inside
    the total file count.  This makes the banner's total directly comparable
    to the footer's "files with findings" count.

    When *target* is set (a custom file or directory was passed on the CLI),
    it is shown in the meta line so the user can confirm what is being scanned.
    """
    shield = emoji("shield")
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
    meta = f" {dot} ".join(parts)
    return (
        f"[{STYLE_BRAND}]{shield}  ZENZIC SENTINEL[/]  [{STYLE_DIM}]v{version}[/]\n"
        f"[{STYLE_DIM}]{meta}[/]"
    )


# ── ObsidianUI: Centralized UI Bridge ──────────────────────────────────────


class ObsidianUI:
    """Central UI bridge for all Zenzic CLI output.

    All header, seal, telemetry, and alert panels must go through this interface.
    This ensures consistent Forge Frame styling across all commands.
    """

    def __init__(self, console: Any):
        self.console = console

    @staticmethod
    def make_panel(
        content: RenderableType,
        *,
        title: str = "PythonWoods",
        subtitle: str = "Apache-2.0",
        border_style: str | None = None,
    ) -> Panel:
        """Create a canonical Forge Frame panel.

        The frame features a left-aligned title, bottom-right subtitle, and an
        Indigo rounded border. Every Zenzic Sentinel output panel must be created
        through this factory to guarantee visual consistency.
        """
        return Panel(
            content,
            title=f"[bold {INDIGO}]{title}[/]",
            title_align="left",
            subtitle=f"[dim]{subtitle}[/]",
            subtitle_align="right",
            border_style=border_style if border_style is not None else INDIGO,
            box=_rich_box.ROUNDED,
            padding=(1, 2),
        )

    def print_header(self, version: str) -> None:
        """Print the standardized Zenzic banner panel."""
        banner = make_banner(version)
        panel = self.make_panel(banner)
        self.console.print()
        self.console.print(panel)
        self.console.print()


__all__ = [
    "ObsidianUI",
    "make_banner",
    "make_sentinel_header",
    "emoji",
    "INDIGO",
    "SLATE",
    "EMERALD",
    "AMBER",
    "ROSE",
    "BLOOD",
    "STYLE_BRAND",
    "STYLE_DIM",
    "STYLE_OK",
    "STYLE_WARN",
    "STYLE_ERR",
    "SUPPORTS_COLOR",
    "SUPPORTS_EMOJI",
]
