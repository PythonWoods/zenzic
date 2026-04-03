# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Entry point for the zenzic CLI application."""

from __future__ import annotations

import sys
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from zenzic import __version__
from zenzic.cli import check_app, clean_app, diff, init, plugins_app, score, serve
from zenzic.core.exceptions import ConfigurationError
from zenzic.core.logging import setup_cli_logging
from zenzic.ui import INDIGO, make_banner


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
) -> None:
    pass


app.add_typer(check_app, name="check", rich_help_panel="Core")
app.add_typer(clean_app, name="clean", rich_help_panel="Core")
app.add_typer(plugins_app, name="plugins", rich_help_panel="SDK & Plugins")
app.command(name="score", rich_help_panel="Quality")(score)
app.command(name="diff", rich_help_panel="Quality")(diff)
app.command(name="serve", rich_help_panel="Development")(serve)
app.command(name="init", rich_help_panel="SDK & Plugins")(init)

_err_console = Console(stderr=True, highlight=False)


def _print_banner() -> None:
    """Print the Indigo-branded Zenzic banner to stderr."""
    from rich import box as rich_box

    _err_console.print(
        Panel(
            make_banner(__version__),
            border_style=f"bold {INDIGO}",
            box=rich_box.HEAVY,
            padding=(1, 3),
            title=f"[{INDIGO}]PythonWoods[/]",
            title_align="left",
            subtitle="[dim]Apache-2.0[/]",
            subtitle_align="right",
            expand=False,
        )
    )
    _err_console.print()


def cli_main() -> None:
    """Wired as the `zenzic` console_scripts entry point."""
    setup_cli_logging()

    # Show an elegant banner on zero args or when starting the dev server
    if len(sys.argv) == 1 or (len(sys.argv) >= 2 and sys.argv[1] == "serve"):
        _print_banner()

    try:
        app()
    except ConfigurationError as exc:
        _err_console.print(f"\n[bold red]Configuration Error[/]\n\n{exc.message}")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    cli_main()
