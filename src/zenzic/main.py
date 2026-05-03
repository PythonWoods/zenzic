# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Entry point for the zenzic CLI application."""

from __future__ import annotations

import os
import sys
from typing import Annotated

import typer
from rich.console import Console

from zenzic import __version__
from zenzic.cli import (
    check_app,
    clean_app,
    configure_console,
    diff,
    get_console,
    get_ui,
    init,
    inspect_app,
    lab,
    score,
)
from zenzic.core.exceptions import PluginContractError, ZenzicError
from zenzic.core.logging import setup_cli_logging
from zenzic.core.ui import SentinelPalette, SentinelUI


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"Zenzic v{__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="zenzic",
    help=(
        f"[bold {SentinelPalette.BRAND}]Zenzic[/] — Engine-agnostic linter and security shield "
        "for Markdown documentation.\n\n"
        "Run [bold cyan]zenzic check all[/] for a full audit, or pick individual "
        "checks below."
    ),
    rich_markup_mode="rich",
    no_args_is_help=True,
    rich_help_panel="Core",
    epilog=f"[bold {SentinelPalette.BRAND}]PythonWoods[/]  [dim]·  Apache-2.0  ·  https://zenzic.dev[/]",
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
app.add_typer(inspect_app, name="inspect", rich_help_panel="Introspection")
app.command(name="lab", rich_help_panel="Core")(lab)
app.command(name="score", rich_help_panel="Quality")(score)
app.command(name="diff", rich_help_panel="Quality")(diff)
app.command(name="init", rich_help_panel="SDK & Plugins")(init)


_err_console = Console(
    stderr=True,
    highlight=False,
    no_color=os.environ.get("NO_COLOR") is not None,
    force_terminal=True
    if os.environ.get("FORCE_COLOR") and not os.environ.get("NO_COLOR")
    else None,
)

_err_ui = SentinelUI(_err_console)


def _sentinel_alert(exc: ZenzicError, *, border_style: str, title: str) -> None:
    """Render a styled Sentinel Alert panel for a ZenzicError."""
    _err_ui.print_exception_alert(
        str(exc.message),
        context=dict(exc.context) if exc.context else None,
        title=title,
        border_style=border_style,
    )


def _print_banner() -> None:
    """Print the Forge Frame Zenzic banner to stdout (same console as commands)."""
    get_ui().print_header(__version__)
    get_console().print()


def cli_main() -> None:
    """Wired as the `zenzic` console_scripts entry point."""
    from rich.traceback import install as _rich_tb_install

    _rich_tb_install(show_locals=True, suppress=[typer], word_wrap=True)
    setup_cli_logging()

    # Show an elegant banner on zero args, --help/-h at any nesting level,
    # or when a sub-app (check/clean/inspect) is invoked with no further args
    # — those hit no_args_is_help=True and show only Typer help without our frame.
    _SUBAPPS_WITH_MENU = frozenset({"check", "clean", "inspect"})
    if (
        len(sys.argv) == 1
        or any(arg in sys.argv for arg in ("--help", "-h"))
        or (len(sys.argv) == 2 and sys.argv[1] in _SUBAPPS_WITH_MENU)
    ):
        _print_banner()

    try:
        app()
    except (SystemExit, KeyboardInterrupt):
        raise
    except PluginContractError as exc:
        _sentinel_alert(
            exc,
            border_style=SentinelPalette.STYLE_BRAND,
            title="Zenzic Plugin Contract Violation",
        )
        sys.exit(1)
    except ZenzicError as exc:
        _sentinel_alert(
            exc,
            border_style=SentinelPalette.STYLE_ERR,
            title="Zenzic Error",
        )
        sys.exit(1)
    # Unexpected exceptions propagate to the global rich traceback handler
    # installed above — identical output to bump-my-version.


if __name__ == "__main__":  # pragma: no cover
    cli_main()
