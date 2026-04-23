# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Entry point for the zenzic CLI application."""

from __future__ import annotations

import os
import sys
from typing import Annotated

import typer
from rich import box as rich_box
from rich.console import Console
from rich.panel import Panel

from zenzic import __version__
from zenzic.cli import check_app, clean_app, configure_console, diff, init, plugins_app, score
from zenzic.core.exceptions import PluginContractError, ZenzicError
from zenzic.core.logging import setup_cli_logging
from zenzic.lab import lab
from zenzic.ui import INDIGO, ROSE, ObsidianUI


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"Zenzic v{__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="zenzic",
    help=(
        "[bold #4f46e5]Zenzic[/] — Engine-agnostic linter and security shield "
        "for Markdown documentation.\n\n"
        "Run [bold cyan]zenzic check all[/] for a full audit, or pick individual "
        "checks below."
    ),
    rich_markup_mode="rich",
    no_args_is_help=True,
    rich_help_panel="Core",
    epilog=f"[bold {INDIGO}]PythonWoods[/]  [dim]·  Apache-2.0  ·  https://zenzic.dev[/]",
)


@app.callback()
def _main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-V",
            callback=_version_callback,
            is_eager=True,
            help="Show the Zenzic version and exit.",
        ),
    ] = None,
    no_color: Annotated[
        bool,
        typer.Option(
            "--no-color",
            help="Disable ANSI color and style output (also respects the NO_COLOR env var).",
            envvar="NO_COLOR",
        ),
    ] = False,
    force_color: Annotated[
        bool,
        typer.Option(
            "--force-color",
            help="Force ANSI color output even when stdout is not a TTY (also respects FORCE_COLOR env var).",
            envvar="FORCE_COLOR",
        ),
    ] = False,
) -> None:
    configure_console(no_color=no_color, force_color=force_color)


app.add_typer(check_app, name="check", rich_help_panel="Core")
app.add_typer(clean_app, name="clean", rich_help_panel="Core")
app.add_typer(plugins_app, name="plugins", rich_help_panel="SDK & Plugins")
app.command(name="lab", rich_help_panel="Core")(lab)
app.command(name="score", rich_help_panel="Quality")(score)
app.command(name="diff", rich_help_panel="Quality")(diff)
app.command(name="init", rich_help_panel="SDK & Plugins")(init)

_err_console = Console(
    stderr=True,
    highlight=False,
    no_color=os.environ.get("NO_COLOR") is not None,
    force_terminal=os.environ.get("FORCE_COLOR") is not None and os.environ.get("NO_COLOR") is None,
)


def _sentinel_alert(exc: ZenzicError, *, border_style: str, title: str) -> None:
    """Render a styled Sentinel Alert panel for a ZenzicError."""
    lines = [str(exc.message)]
    if exc.context:
        lines.append("")
        for k, v in exc.context.items():
            lines.append(f"  [dim]{k}:[/] {v}")
    _err_console.print(
        Panel(
            "\n".join(lines),
            title=f"[{border_style}]{title}[/]",
            border_style=border_style,
            box=rich_box.ROUNDED,
            padding=(0, 1),
        )
    )


def _print_banner() -> None:
    """Print the Forge Frame Zenzic banner to stderr."""
    ui = ObsidianUI(_err_console)
    ui.print_header(__version__)
    _err_console.print()


def cli_main() -> None:
    """Wired as the `zenzic` console_scripts entry point."""
    from rich.traceback import install as _rich_tb_install

    _rich_tb_install(show_locals=True, suppress=[typer], word_wrap=True)
    setup_cli_logging()

    # Show an elegant banner on zero args or bare --help
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ("--help", "-h")):
        _print_banner()

    try:
        app()
    except (SystemExit, KeyboardInterrupt):
        raise
    except PluginContractError as exc:
        _sentinel_alert(
            exc,
            border_style=f"bold {INDIGO}",
            title="Zenzic Plugin Contract Violation",
        )
        sys.exit(1)
    except ZenzicError as exc:
        _sentinel_alert(
            exc,
            border_style=f"bold {ROSE}",
            title="Zenzic Error",
        )
        sys.exit(1)
    # Unexpected exceptions propagate to the global rich traceback handler
    # installed above — identical output to bump-my-version.


if __name__ == "__main__":  # pragma: no cover
    cli_main()
