# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""``zenzic lab`` — interactive showcase of bundled documentation examples.

Each act runs a fresh check against one of the bundled example projects using
Zenzic's internal Python APIs (zero subprocess).  Examples are resolved from
the installed wheel via :func:`importlib.resources.files`, or from the
repository checkout when running in editable mode.
"""

from __future__ import annotations

import importlib.resources as _ilr
import time
from dataclasses import dataclass
from pathlib import Path

import typer
from rich import box
from rich.console import Console, Group
from rich.table import Table
from rich.text import Text

from zenzic import __version__
from zenzic.cli import (
    _apply_target,
    _collect_all_results,
    _count_docs_assets,
    _to_findings,
)
from zenzic.core.exclusion import LayeredExclusionManager
from zenzic.core.reporter import Finding, SentinelReporter
from zenzic.models.config import ZenzicConfig
from zenzic.ui import EMERALD, INDIGO, ROSE, SLATE, ObsidianUI, emoji


_console = Console(highlight=False)


# ── Path resolution ──────────────────────────────────────────────────────────


def _examples_root() -> Path:
    """Locate the bundled examples directory.

    Resolution order:

    1. **Installed wheel** — ``zenzic/examples/`` inside the package tree, as
       populated by the ``force-include`` hatchling directive.
    2. **Editable / source checkout** — three directories above ``lab.py``
       (``<repo>/examples/``).

    Raises :exc:`FileNotFoundError` when neither location resolves to a
    directory.
    """
    pkg_root = Path(str(_ilr.files("zenzic")))
    installed = pkg_root / "examples"
    if installed.is_dir():
        return installed
    # lab.py is at src/zenzic/lab.py; the repo root is three levels above.
    dev = Path(__file__).resolve().parent.parent.parent / "examples"
    if dev.is_dir():
        return dev
    raise FileNotFoundError(
        "Cannot locate examples/ — reinstall zenzic or run from the repository root."
    )


# ── Act definitions ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _Act:
    id: int
    title: str
    description: str
    example_dir: str
    expected_pass: bool
    expected_breach: bool = False
    show_info: bool = False
    docs_root_override: str | None = None
    single_file: str | None = None


_ACTS: list[_Act] = [
    _Act(
        0,
        "Linter Demo",
        "FILE_NOT_FOUND and BROKEN_ANCHOR on a MkDocs 1.x project",
        "mkdocs-basic",
        expected_pass=False,
    ),
    _Act(
        1,
        "The Gold Standard",
        "100/100 multi-locale MkDocs project — zero findings",
        "i18n-standard",
        expected_pass=True,
    ),
    _Act(
        2,
        "The Broken Docs",
        "Every error class in a single fixture",
        "broken-docs",
        expected_pass=False,
    ),
    _Act(
        3,
        "The Shield",
        "Credential exposure detected — security_breach severity",
        "security_lab",
        expected_pass=False,
        expected_breach=True,
    ),
    _Act(
        4,
        "Single-File Target",
        "Scope the audit to README.md only — 1 file, zero findings",
        "single-file-target",
        expected_pass=True,
        single_file="README.md",
    ),
    _Act(
        5,
        "Custom Dir Target",
        "Audit content/ at runtime without modifying zenzic.toml",
        "custom-dir-target",
        expected_pass=True,
        docs_root_override="content",
    ),
    _Act(
        6,
        "Transparent Proxy",
        "SENTINEL banner — Zensical bridge with mkdocs.yml only",
        "zensical-bridge",
        expected_pass=True,
    ),
    _Act(
        7,
        "The Flagship",
        "Versioned docs + @site/ aliases + i18n Ghost Routing",
        "docusaurus-v3-enterprise",
        expected_pass=True,
    ),
    _Act(
        8,
        "Standalone Excellence",
        "The ONLY engine for config-free folders: full link + Shield + Z401 checks, zero nav contract required",
        "standalone-markdown",
        expected_pass=True,
        show_info=True,
    ),
    _Act(
        9,
        "MkDocs Favicon Guard",
        "Z404 fired for theme.favicon + theme.logo declared but missing (MkDocs engine)",
        "mkdocs-z404",
        expected_pass=False,
    ),
    _Act(
        10,
        "Zensical Logo Guard",
        "Z404 fired for [project].favicon + [project].logo declared but missing (Zensical engine)",
        "zensical-z404",
        expected_pass=False,
    ),
]


# ── Act runner ───────────────────────────────────────────────────────────────


@dataclass
class _ActResult:
    act: _Act
    errors: int
    warnings: int
    has_breach: bool
    elapsed: float
    engine: str
    docs_count: int = 0
    assets_count: int = 0

    @property
    def total_files(self) -> int:
        return self.docs_count + self.assets_count

    @property
    def throughput(self) -> float:
        """Files per second — 0.0 when elapsed is zero."""
        return self.total_files / self.elapsed if self.elapsed > 0 else 0.0

    @property
    def met_expectation(self) -> bool:
        if self.act.expected_breach:
            return self.has_breach
        if self.act.expected_pass:
            return self.errors == 0
        return self.errors > 0 or self.warnings > 0


def _run_act(act: _Act, examples_root: Path) -> _ActResult:
    """Run all checks for *act* against its example directory."""
    example_dir = examples_root / act.example_dir
    config, _ = ZenzicConfig.load(example_dir)

    single_file: Path | None = None
    target_hint: str | None = None

    if act.single_file is not None:
        config, single_file, _, target_hint = _apply_target(example_dir, config, act.single_file)
    elif act.docs_root_override is not None:
        config, _, _, target_hint = _apply_target(example_dir, config, act.docs_root_override)

    docs_root = (example_dir / config.docs_dir).resolve()
    exclusion_mgr = LayeredExclusionManager(config, repo_root=example_dir, docs_root=docs_root)

    t0 = time.monotonic()
    results = _collect_all_results(example_dir, docs_root, config, exclusion_mgr, strict=False)
    elapsed = time.monotonic() - t0

    findings: list[Finding] = _to_findings(results, docs_root)

    if single_file is not None:
        sf_rel = str(single_file.relative_to(docs_root))
        findings = [f for f in findings if f.rel_path == sf_rel]

    docs_count, assets_count = _count_docs_assets(docs_root, example_dir, exclusion_mgr, config)
    if single_file is not None:
        docs_count, assets_count = 1, 0

    reporter = SentinelReporter(_console, docs_root, docs_dir=str(config.docs_dir))
    errors, warnings = reporter.render(
        findings,
        version=__version__,
        elapsed=elapsed,
        docs_count=docs_count,
        assets_count=assets_count,
        engine=config.build_context.engine,
        target=target_hint,
        show_info=act.show_info,
    )

    has_breach = any(f.severity == "security_breach" for f in findings)
    return _ActResult(
        act=act,
        errors=errors,
        warnings=warnings,
        has_breach=has_breach,
        elapsed=elapsed,
        engine=config.build_context.engine,
        docs_count=docs_count,
        assets_count=assets_count,
    )


# ── Output helpers ────────────────────────────────────────────────────────────


def _status_cell(r: _ActResult) -> str:
    if r.act.expected_breach:
        if r.has_breach:
            return "[bold red]BREACH[/] [green]✓[/]"
        return "[yellow]BREACH expected — not triggered[/] [red]✗[/]"
    if r.act.expected_pass:
        if r.errors == 0:
            return "[bold green]PASS[/] [green]✓[/]"
        return "[bold red]FAIL (unexpected)[/] [red]✗[/]"
    if r.errors > 0 or r.warnings > 0:
        return "[yellow]EXPECTED FAIL[/] [green]✓[/]"
    return "[yellow]EXPECTED FAIL — nothing found[/] [red]✗[/]"


def _print_summary(results: list[_ActResult]) -> None:
    table = Table(
        title=f"\n[bold {INDIGO}]⬡  ZENZIC LAB — Full Run Summary[/]",
        box=box.ROUNDED,
        show_header=True,
        header_style=f"bold {INDIGO}",
    )
    table.add_column("Act", justify="center", style=f"bold {INDIGO}", width=5)
    table.add_column("Title", style="bold", min_width=22)
    table.add_column("Engine", style="cyan", min_width=10)
    table.add_column("Files", justify="right", style=SLATE, min_width=7)
    table.add_column("files/s", justify="right", style=SLATE, min_width=8)
    table.add_column("Result", min_width=26)
    table.add_column("Time", justify="right", style="dim", min_width=7)

    unexpected = sum(1 for r in results if not r.met_expectation)
    total_files = sum(r.total_files for r in results)
    total_elapsed = sum(r.elapsed for r in results)
    for r in results:
        table.add_row(
            str(r.act.id),
            r.act.title,
            r.engine,
            str(r.total_files),
            f"{r.throughput:.0f}",
            _status_cell(r),
            f"{r.elapsed:.2f}s",
        )

    _console.print(table)

    # ── Obsidian Seal footer ──────────────────────────────────────────────────
    avg_throughput = total_files / total_elapsed if total_elapsed > 0 else 0.0
    seal_items = [
        Text.from_markup(
            f"[{SLATE}]{total_files} files scanned across {len(results)} acts"
            f" {emoji('dot')} {total_elapsed:.2f}s total"
            f" {emoji('dot')} {avg_throughput:.0f} files/s[/]"
        ),
        Text(),
    ]
    if unexpected == 0:
        seal_items.append(
            Text.from_markup(
                f"[bold {EMERALD}]{emoji('check')} All {len(results)} act(s) met expectations."
                " The Obsidian Mirror is clear.[/]"
            )
        )
    else:
        seal_items.append(
            Text.from_markup(
                f"[bold {ROSE}]{emoji('cross')} {unexpected}/{len(results)} act(s)"
                " did not meet expectations.[/]"
            )
        )

    _console.print()
    ui = ObsidianUI(_console)
    ui.print_header(__version__)
    _console.print()
    _console.print(
        Group(
            Text.from_markup(f"[bold {INDIGO}]{emoji('shield')} OBSIDIAN SEAL — Lab Complete[/]"),
            Text(),
            *seal_items,
        ),
    )


def _print_act_seal(r: _ActResult) -> None:
    """Render an Obsidian Seal footer after a single-act run."""
    files_line = (
        f"{r.total_files} file{'s' if r.total_files != 1 else ''} scanned"
        f" {emoji('dot')} {r.elapsed:.2f}s"
        + (f" {emoji('dot')} {r.throughput:.0f} files/s" if r.total_files else "")
    )
    seal_items: list[Text] = [
        Text.from_markup(f"[{SLATE}]{files_line}[/]"),
        Text(),
    ]
    if r.met_expectation:
        verdict = f"{emoji('check')} Act {r.act.id} — {r.act.title} — expectation met."
        seal_items.append(Text.from_markup(f"[bold {EMERALD}]{verdict}[/]"))
    else:
        verdict = f"{emoji('cross')} Act {r.act.id} — {r.act.title} — expectation NOT met."
        seal_items.append(Text.from_markup(f"[bold {ROSE}]{verdict}[/]"))

    _console.print()
    ui = ObsidianUI(_console)
    ui.print_header(__version__)
    _console.print()
    _console.print(
        Group(
            Text.from_markup(f"[bold {INDIGO}]{emoji('shield')} OBSIDIAN SEAL[/]"),
            Text(),
            *seal_items,
        ),
    )


def _print_act_index() -> None:
    table = Table(
        title=f"[bold #4f46e5]⬡  ZENZIC LAB[/]  [dim]v{__version__}[/]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Act", justify="center", style="bold cyan", width=5)
    table.add_column("Title", style="bold", min_width=22)
    table.add_column("Description", style="#f59e0b")
    table.add_column("Expects", justify="center", min_width=10)

    for act in _ACTS:
        expects = (
            "[red]BREACH[/]"
            if act.expected_breach
            else "[green]PASS[/]"
            if act.expected_pass
            else "[yellow]FAIL[/]"
        )
        table.add_row(str(act.id), act.title, act.description, expects)

    _console.print(table)


# ── CLI command ───────────────────────────────────────────────────────────────


def lab(
    act_number: int | None = typer.Argument(
        None,
        help="Act number to run (0–10). Omit to display the act menu.",
        show_default=False,
    ),
    list_acts: bool = typer.Option(
        False,
        "--list",
        "-l",
        help="Print the act index without running checks.",
    ),
) -> None:
    """Zenzic Lab — interactive showcase of bundled documentation examples.

    Run without arguments to display the act menu.  Pass an act number to
    execute that single act:

        [bold cyan]zenzic lab[/]      — show act menu
        [bold cyan]zenzic lab 0[/]    — run Act 0 (Linter Demo)
        [bold cyan]zenzic lab 3[/]    — run Act 3 (The Shield)
        [bold cyan]zenzic lab --list[/] — print act index without running
        [bold cyan]zenzic lab 9[/]    — run Act 9 (MkDocs Favicon Guard)
        [bold cyan]zenzic lab 10[/]   — run Act 10 (Zensical Logo Guard)
    """
    _console.print()
    ui = ObsidianUI(_console)
    ui.print_header(__version__)

    if list_acts:
        _print_act_index()
        return

    if act_number is None:
        # No argument: show the menu and instructions, do not run any act.
        _print_act_index()
        _console.print(
            "\n[bold]Welcome to the Zenzic Lab.[/] Choose an act to see the Sentinel in action.\n"
            "  Run [bold cyan]zenzic lab <N>[/] to execute a specific act (e.g. [cyan]zenzic lab 0[/]).\n"
        )
        return

    if not (0 <= act_number <= 10):
        _console.print(
            f"[bold red]ERROR:[/] Act number must be between 0 and 10, got {act_number}."
        )
        raise typer.Exit(1)

    try:
        examples_root = _examples_root()
    except FileNotFoundError as exc:
        _console.print(f"[bold red]ERROR:[/] {exc}")
        raise typer.Exit(1) from exc

    acts_to_run = [a for a in _ACTS if a.id == act_number]

    act_results: list[_ActResult] = []
    for act in acts_to_run:
        _console.print()
        ui = ObsidianUI(_console)
        ui.print_header(__version__)
        _console.print()
        _console.print(
            Group(
                Text.from_markup(f"[bold {INDIGO}]Act {act.id} — {act.title}[/]"),
                Text(),
                Text.from_markup(f"[bold]{act.description}[/]"),
            )
        )
        result = _run_act(act, examples_root)
        act_results.append(result)

    if len(act_results) == 1:
        _print_act_seal(act_results[0])
    elif len(act_results) > 1:
        _print_summary(act_results)
