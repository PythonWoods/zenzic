# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Entry point for the zenzic CLI application."""

from __future__ import annotations

import sys
from typing import Annotated

import typer
from rich.console import Console

from zenzic import __version__
from zenzic.cli import check_app, clean_app, diff, init, score, serve
from zenzic.core.exceptions import ConfigurationError
from zenzic.core.logging import setup_cli_logging


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"Zenzic v{__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="zenzic",
    help="Engineering-grade documentation linter for MkDocs and Zensical.",
    rich_markup_mode="rich",
    no_args_is_help=True,
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


app.add_typer(check_app, name="check")
app.add_typer(clean_app, name="clean")
app.command(name="score")(score)
app.command(name="diff")(diff)
app.command(name="serve")(serve)
app.command(name="init")(init)

_err_console = Console(stderr=True, highlight=False)


def cli_main() -> None:
    """Wired as the `zenzic` console_scripts entry point."""
    setup_cli_logging()

    # Show an elegant banner on zero args or when starting the dev server
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == "serve"):
        from rich.panel import Panel

        _err_console.print(
            Panel.fit(
                f"[bold cyan]ZENZIC[/] [dim]v{__version__}[/]\n"
                "[italic]Engineering-grade documentation linter for MkDocs and Zensical.[/]",
                border_style="cyan",
                padding=(1, 4),
                title="PythonWoods",
                title_align="left",
            )
        )
        _err_console.print()

    try:
        app()
    except ConfigurationError as exc:
        _err_console.print(f"\n[bold red]Configuration Error[/]\n\n{exc.message}")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    cli_main()
