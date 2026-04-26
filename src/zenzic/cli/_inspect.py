# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Inspect sub-commands: introspect the Zenzic scanner arsenal and plugin registry."""

from __future__ import annotations

import typer
from rich import box
from rich.table import Table
from rich.text import Text

from zenzic.core.codes import CORE_SCANNERS
from zenzic.core.ui import ObsidianPalette

from . import _shared


inspect_app = typer.Typer(
    name="inspect",
    help=f"[bold {ObsidianPalette.BRAND}]Inspect[/] — Introspect the Zenzic scanner arsenal and plugin registry.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def _inspect_capabilities() -> None:
    """Show the full Zenzic scanner arsenal.

    **Section A — Core Scanners (Built-in):** seven scanners compiled into
    Zenzic itself.  The Shield (Z201) and Blood Sentinel (Z202–203) exit with
    codes 2 and 3 respectively — neither is suppressible with ``--exit-zero``.

    **Section B — Extensible Rules (Plugin System):** rules registered via the
    ``zenzic.rules`` entry-point group from any installed third-party package.
    """
    from zenzic import __version__
    from zenzic.core.rules import list_plugin_rules

    _shared._ui.print_header(__version__)
    _shared.console.print()

    # ── Section A: Core Scanners ──────────────────────────────────────────
    core_table = Table(
        title=f"[bold {ObsidianPalette.BRAND}]Core Scanners[/]  [dim](built-in)[/dim]",
        title_justify="left",
        box=box.ROUNDED,
        border_style=ObsidianPalette.DIM,
        header_style=ObsidianPalette.STYLE_BRAND,
        pad_edge=True,
        padding=(0, 1),
    )
    core_table.add_column("Codes", style="bold cyan", min_width=8, no_wrap=True)
    core_table.add_column("Scanner", style="bold", min_width=16)
    core_table.add_column("Capability")
    core_table.add_column("Exit", min_width=6, justify="center")

    for scanner in CORE_SCANNERS:
        if scanner.non_suppressible:
            exit_cell = Text.from_markup(f"[bold red]{scanner.primary_exit} \u26a0[/bold red]")
        else:
            exit_cell = Text(str(scanner.primary_exit))
        core_table.add_row(scanner.codes, scanner.name, scanner.capability, exit_cell)

    _shared.console.print(core_table)
    _shared.console.print()
    _shared.console.print(
        Text.from_markup(
            f"  [{ObsidianPalette.DIM}]\u26a0  Exit 2 and Exit 3 are non-suppressible \u2014 "
            f"--exit-zero has no effect on Shield or Blood Sentinel.[/{ObsidianPalette.DIM}]"
        )
    )
    _shared.console.print()

    # ── Section B: Extensible Rules ───────────────────────────────────────
    rules = list_plugin_rules()

    rules_table = Table(
        title=(
            f"[bold {ObsidianPalette.BRAND}]Extensible Rules[/]  "
            f"[dim](plugin system \u2014 zenzic.rules entry-point group)[/dim]"
        ),
        title_justify="left",
        box=box.ROUNDED,
        border_style=ObsidianPalette.DIM,
        header_style=ObsidianPalette.STYLE_BRAND,
        pad_edge=True,
        padding=(0, 1),
    )
    rules_table.add_column("Rule", style="bold cyan", min_width=14)
    rules_table.add_column("Code", style="bold", min_width=6)
    rules_table.add_column("Origin", min_width=8)
    rules_table.add_column("Class", style="dim")

    if rules:
        for info in rules:
            origin_badge = (
                "[cyan](core)[/]" if info.origin == "zenzic" else f"[green]({info.origin})[/]"
            )
            rules_table.add_row(info.source, info.rule_id, origin_badge, info.class_name)
    else:
        rules_table.add_row(
            "[dim]\u2014[/dim]",
            "[dim]\u2014[/dim]",
            "[dim]\u2014[/dim]",
            (
                f"[{ObsidianPalette.DIM}]No third-party plugins installed. "
                f"Register rules via the zenzic.rules entry-point group.[/{ObsidianPalette.DIM}]"
            ),
        )

    _shared.console.print(rules_table)
    _shared.console.print()

    rule_count = len(rules)
    _shared.console.print(
        Text.from_markup(
            f"  [{ObsidianPalette.DIM}]{len(CORE_SCANNERS)} built-in scanners \u00b7 "
            f"{rule_count} extensible rule{'s' if rule_count != 1 else ''} registered"
            f"[/{ObsidianPalette.DIM}]"
        )
    )
    _shared.console.print()

    # ── Section C: Engine-specific Link Bypasses ──────────────────────────
    bypass_table = Table(
        title=(
            f"[bold {ObsidianPalette.BRAND}]Engine-specific Link Bypasses[/]  "
            f"[dim](Rule R21 \u2014 Protocol Sovereignty)[/dim]"
        ),
        title_justify="left",
        box=box.ROUNDED,
        border_style=ObsidianPalette.DIM,
        header_style=ObsidianPalette.STYLE_BRAND,
        pad_edge=True,
        padding=(0, 1),
    )
    bypass_table.add_column("Engine", style="bold cyan", min_width=12, no_wrap=True)
    bypass_table.add_column("Adapter", style="bold", min_width=20)
    bypass_table.add_column("Bypass Schemes")

    _BYPASS_ROWS = [
        (
            "docusaurus",
            "DocusaurusAdapter",
            Text.from_markup(
                f"[bold]pathname:[/bold]  [{ObsidianPalette.DIM}](static-asset routing escape hatch)[/{ObsidianPalette.DIM}]"
            ),
        ),
        (
            "mkdocs",
            "MkDocsAdapter",
            Text.from_markup(f"[{ObsidianPalette.DIM}](none)[/{ObsidianPalette.DIM}]"),
        ),
        (
            "zensical",
            "ZensicalAdapter",
            Text.from_markup(f"[{ObsidianPalette.DIM}](none)[/{ObsidianPalette.DIM}]"),
        ),
        (
            "standalone",
            "StandaloneAdapter",
            Text.from_markup(f"[{ObsidianPalette.DIM}](none)[/{ObsidianPalette.DIM}]"),
        ),
    ]
    for _engine, _adapter, _bypasses in _BYPASS_ROWS:
        bypass_table.add_row(_engine, _adapter, _bypasses)

    _shared.console.print(bypass_table)
    _shared.console.print()
    _shared.console.print(
        Text.from_markup(
            f"  [{ObsidianPalette.DIM}]R21: engine-specific behaviour is declared in the adapter "
            f"via get_link_scheme_bypasses() \u2014 validator.py never hardcodes engine names."
            f"[/{ObsidianPalette.DIM}]"
        )
    )


# Canonical command
inspect_app.command(
    name="capabilities",
    help="Show all built-in scanners, plugin rules, and engine-specific link bypasses.",
)(_inspect_capabilities)
