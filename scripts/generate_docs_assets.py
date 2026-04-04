# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Generate all documentation visual assets via Rich SVG export.

Assets generated
----------------
screenshot.svg        Hero shot — full ``zenzic check all`` run on broken-docs.
                      Demonstrates the Sentinel banner, gutter context, and the
                      summary table.  Used in README.md and docs/index.md.

screenshot-score.svg  Quality Score panel — shows ``zenzic score`` output for a
                      project with a non-trivial breakdown.  Used in the docs
                      Visual Tour section.

Run via nox::

    nox -s screenshot

Or directly::

    uv run python scripts/generate_docs_assets.py
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from zenzic import __version__
from zenzic.cli import _collect_all_results, _to_findings
from zenzic.core.reporter import SentinelReporter
from zenzic.core.scorer import compute_score
from zenzic.models.config import ZenzicConfig
from zenzic.ui import INDIGO, SLATE, emoji


# ── Paths ─────────────────────────────────────────────────────────────────────

BROKEN_DOCS = Path(__file__).parent.parent / "examples" / "broken-docs"
OUT_DIR = Path(__file__).parent.parent / "docs" / "assets" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Shared helpers ─────────────────────────────────────────────────────────────

_INERT = {".css", ".js"}
_CONFIG = {".yml", ".yaml", ".toml"}


def _docs_assets_count(docs_root: Path, project_root: Path | None = None) -> tuple[int, int]:
    """Return (docs_count, assets_count) for *docs_root*.

    *project_root* is scanned (non-recursively) for engine config files
    (``*.yml`` / ``*.yaml``) which are added to *docs_count*.
    """
    if not docs_root.is_dir():
        return 0, 0
    docs = sum(
        1
        for p in docs_root.rglob("*")
        if p.is_file() and (p.suffix.lower() == ".md" or p.suffix.lower() in _CONFIG)
    )
    if project_root is not None:
        docs += sum(
            1
            for p in project_root.iterdir()
            if p.is_file() and p.suffix.lower() in {".yml", ".yaml"}
        )
    assets = sum(
        1
        for p in docs_root.rglob("*")
        if p.is_file()
        and p.suffix.lower() not in _INERT
        and p.suffix.lower() not in _CONFIG
        and p.suffix.lower() != ".md"
    )
    return docs, assets


# ── Asset 1: Hero shot ─────────────────────────────────────────────────────────


def generate_hero() -> Path:
    """Full ``zenzic check all`` run on broken-docs → screenshot.svg."""
    out = OUT_DIR / "screenshot.svg"

    console = Console(highlight=False, record=True, width=88)

    config, _ = ZenzicConfig.load(BROKEN_DOCS)
    docs_root = (BROKEN_DOCS / config.docs_dir).resolve()

    console.print(f"[dim]{emoji('arrow')}[/] [bold]zenzic check all --strict[/bold]")
    console.print()

    t0 = time.monotonic()
    results = _collect_all_results(BROKEN_DOCS, config, strict=True)
    elapsed = time.monotonic() - t0

    all_findings = _to_findings(results, docs_root)
    reporter = SentinelReporter(console, docs_root)
    docs_count, assets_count = _docs_assets_count(docs_root, BROKEN_DOCS)
    reporter.render(
        all_findings,
        version=__version__,
        elapsed=elapsed,
        docs_count=docs_count,
        assets_count=assets_count,
        engine=config.build_context.engine if hasattr(config, "build_context") else "auto",
    )

    # ── Score panel (appended to the same SVG) ────────────────────────────────
    score_report = compute_score(
        link_errors=len(results.link_errors),
        orphans=len(results.orphans),
        snippet_errors=len(results.snippet_errors),
        placeholders=len(results.placeholders),
        unused_assets=len(results.unused_assets),
    )
    if score_report.score >= 80:
        score_style, score_icon = f"bold {INDIGO}", emoji("check")
    elif score_report.score >= 50:
        score_style, score_icon = "bold yellow", emoji("warn")
    else:
        score_style, score_icon = "bold red", emoji("cross")

    score_text = Text()
    score_text.append(f" {score_icon}  {score_report.score}", style=score_style)
    score_text.append("/100 ", style="dim")

    console.print()
    console.print(
        Panel(
            score_text,
            title="[bold]Zenzic Quality Score[/]",
            title_align="left",
            border_style=INDIGO,
            expand=False,
            padding=(0, 2),
        )
    )
    console.print()

    table = Table(
        box=box.ROUNDED,
        title="[bold]Quality Breakdown[/]",
        title_style=SLATE,
        border_style=SLATE,
        show_lines=False,
        pad_edge=True,
        padding=(0, 1),
    )
    table.add_column(emoji("dot"), justify="center", width=4, no_wrap=True)
    table.add_column("Category", min_width=14, style="bold")
    table.add_column("Issues", justify="right")
    table.add_column("Weight", justify="right", style="dim")
    table.add_column("Score", justify="right", style="dim")

    for cat in score_report.categories:
        status_icon = (
            f"[green]{emoji('check')}[/]" if cat.issues == 0 else f"[red]{emoji('cross')}[/]"
        )
        issue_display = f"[green]{cat.issues}[/]" if cat.issues == 0 else f"[red]{cat.issues}[/]"
        table.add_row(
            status_icon,
            cat.name,
            issue_display,
            f"{cat.weight:.0%}",
            f"{cat.contribution:.2f}",
        )
    console.print(table)

    console.save_svg(str(out), title="zenzic check all --strict")
    _cleanup_build_artefact(BROKEN_DOCS)
    return out


# ── Asset 1b: Hero (compact, from readme-hero example) ────────────────────────

README_HERO = Path(__file__).parent.parent / "examples" / "readme-hero"


def generate_hero_crop() -> Path:
    """Compact ``zenzic check all`` on readme-hero → screenshot-hero.svg.

    Uses the lightweight *examples/readme-hero* project (1 error + 3 warnings)
    to produce a naturally compact SVG that fits the README hero area without
    any viewBox hacking.
    """
    out = OUT_DIR / "screenshot-hero.svg"

    console = Console(highlight=False, record=True, width=88)

    config, _ = ZenzicConfig.load(README_HERO)
    docs_root = (README_HERO / config.docs_dir).resolve()

    console.print(f"[dim]{emoji('arrow')}[/] [bold]zenzic check all[/bold]")
    console.print()

    t0 = time.monotonic()
    results = _collect_all_results(README_HERO, config, strict=True)
    elapsed = time.monotonic() - t0

    all_findings = _to_findings(results, docs_root)
    reporter = SentinelReporter(console, docs_root)
    docs_count, assets_count = _docs_assets_count(docs_root, README_HERO)
    reporter.render(
        all_findings,
        version=__version__,
        elapsed=elapsed,
        docs_count=docs_count,
        assets_count=assets_count,
        engine=config.build_context.engine if hasattr(config, "build_context") else "auto",
    )

    console.save_svg(str(out), title="zenzic check all")
    _cleanup_build_artefact(README_HERO)
    return out


# ── Asset 2: Quality score standalone ─────────────────────────────────────────


def generate_score() -> Path:
    """Score panel only → screenshot-score.svg."""
    out = OUT_DIR / "screenshot-score.svg"

    console = Console(highlight=False, record=True, width=60)

    config, _ = ZenzicConfig.load(BROKEN_DOCS)
    results = _collect_all_results(BROKEN_DOCS, config, strict=False)

    score_report = compute_score(
        link_errors=len(results.link_errors),
        orphans=len(results.orphans),
        snippet_errors=len(results.snippet_errors),
        placeholders=len(results.placeholders),
        unused_assets=len(results.unused_assets),
    )
    score_style = (
        f"bold {INDIGO}"
        if score_report.score >= 80
        else "bold yellow"
        if score_report.score >= 50
        else "bold red"
    )
    score_icon = (
        emoji("check")
        if score_report.score >= 80
        else emoji("warn")
        if score_report.score >= 50
        else emoji("cross")
    )

    score_text = Text()
    score_text.append(f" {score_icon}  {score_report.score}", style=score_style)
    score_text.append("/100 ", style="dim")

    console.print(
        Panel(
            score_text,
            title="[bold]Zenzic Quality Score[/]",
            title_align="left",
            border_style=INDIGO,
            expand=False,
            padding=(0, 2),
        )
    )
    console.print()

    table = Table(
        box=box.ROUNDED,
        title="[bold]Quality Breakdown[/]",
        title_style=SLATE,
        border_style=SLATE,
        show_lines=False,
        pad_edge=True,
        padding=(0, 1),
    )
    table.add_column(emoji("dot"), justify="center", width=4, no_wrap=True)
    table.add_column("Category", min_width=14, style="bold")
    table.add_column("Issues", justify="right")
    table.add_column("Weight", justify="right", style="dim")
    table.add_column("Score", justify="right", style="dim")

    for cat in score_report.categories:
        status_icon = (
            f"[green]{emoji('check')}[/]" if cat.issues == 0 else f"[red]{emoji('cross')}[/]"
        )
        issue_display = f"[green]{cat.issues}[/]" if cat.issues == 0 else f"[red]{cat.issues}[/]"
        table.add_row(
            status_icon,
            cat.name,
            issue_display,
            f"{cat.weight:.0%}",
            f"{cat.contribution:.2f}",
        )
    console.print(table)

    console.save_svg(str(out), title="zenzic score")
    _cleanup_build_artefact(BROKEN_DOCS)
    return out


# ── Helpers ────────────────────────────────────────────────────────────────────


def _cleanup_build_artefact(project_root: Path) -> None:
    """Remove the mkdocs ``site/`` directory produced by validate_links."""
    site_dir = project_root / "site"
    if site_dir.exists():
        shutil.rmtree(site_dir)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = Path(__file__).parent.parent

    hero = generate_hero()
    print(f"Saved → {hero.relative_to(root)}")

    hero_crop = generate_hero_crop()
    print(f"Saved → {hero_crop.relative_to(root)}")

    score = generate_score()
    print(f"Saved → {score.relative_to(root)}")
