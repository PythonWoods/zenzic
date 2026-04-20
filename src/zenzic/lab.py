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
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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
from zenzic.ui import emoji


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
        "Minimum Viable",
        "MISSING_DIRECTORY_INDEX info on a bare Markdown tree",
        "vanilla-markdown",
        expected_pass=True,
        show_info=True,
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
        title="\n[bold]Lab Summary[/]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold",
    )
    table.add_column("Act", justify="center", style="dim", width=5)
    table.add_column("Title", min_width=22)
    table.add_column("Engine", style="cyan", min_width=10)
    table.add_column("Result", min_width=26)
    table.add_column("Time", justify="right", style="dim", min_width=7)

    unexpected = sum(1 for r in results if not r.met_expectation)
    for r in results:
        table.add_row(
            str(r.act.id),
            r.act.title,
            r.engine,
            _status_cell(r),
            f"{r.elapsed:.2f}s",
        )

    _console.print(table)
    if unexpected == 0:
        _console.print(
            f"\n[bold green]{emoji('check')} All {len(results)} act(s) met expectations.[/]"
        )
    else:
        _console.print(
            f"\n[bold red]{emoji('cross')} {unexpected}/{len(results)} "
            "act(s) did not meet expectations.[/]"
        )


def _print_act_index() -> None:
    table = Table(
        title="[bold]Zenzic Lab — Act Index[/]",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold",
    )
    table.add_column("Act", justify="center", width=5)
    table.add_column("Title", min_width=22)
    table.add_column("Description")
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
    act_number: int | None = typer.Option(
        None,
        "--act",
        "-a",
        help="Run only the specified act (0–8). Omit to run all.",
        show_default=False,
    ),
    list_acts: bool = typer.Option(
        False,
        "--list",
        "-l",
        help="Print the act index without running checks.",
    ),
) -> None:
    """Showcase bundled examples — pure Python, zero subprocess.

    Runs all nine acts in sequence, demonstrating every check class:
    broken links, orphaned files, credential exposure, multi-locale
    routing, versioned documentation, and bare Markdown auditing.
    Use [bold cyan]--act N[/] to run a single act (0–8).
    """
    if list_acts:
        _print_act_index()
        return

    if act_number is not None and not (0 <= act_number <= 8):
        _console.print(f"[bold red]ERROR:[/] Act number must be between 0 and 8, got {act_number}.")
        raise typer.Exit(1)

    try:
        examples_root = _examples_root()
    except FileNotFoundError as exc:
        _console.print(f"[bold red]ERROR:[/] {exc}")
        raise typer.Exit(1) from exc

    acts_to_run = (
        [a for a in _ACTS if a.id == act_number] if act_number is not None else list(_ACTS)
    )

    act_results: list[_ActResult] = []
    for act in acts_to_run:
        _console.print()
        _console.print(
            Panel(
                f"[bold]{act.description}[/]",
                title=f"[bold #4f46e5]Act {act.id} — {act.title}[/]",
                border_style="#4f46e5",
                expand=False,
            )
        )
        result = _run_act(act, examples_root)
        act_results.append(result)

    if len(act_results) > 1:
        _print_summary(act_results)
