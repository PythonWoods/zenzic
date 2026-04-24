# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Clean sub-commands: safely remove unused documentation files."""

from __future__ import annotations

import typer
from rich.text import Text

from zenzic.core.scanner import find_repo_root, find_unused_assets
from zenzic.core.ui import ObsidianPalette, emoji
from zenzic.models.config import ZenzicConfig

from . import _shared


clean_app = typer.Typer(
    name="clean",
    help=f"[bold {ObsidianPalette.BRAND}]Clean[/] — Safely remove unused documentation files.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@clean_app.command(name="assets")
def clean_assets(
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip interactive confirmation and delete immediately."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show which files would be deleted without actually deleting them."
    ),
) -> None:
    """Delete unused images and assets from the documentation."""
    repo_root = find_repo_root()
    config, _ = ZenzicConfig.load(repo_root)
    docs_root = repo_root / config.docs_dir
    exclusion_mgr = _shared._build_exclusion_manager(config, repo_root, docs_root)

    unused = find_unused_assets(docs_root, exclusion_mgr, config=config)
    if not unused:
        from zenzic import __version__

        _shared._ui.print_header(__version__)
        _shared.console.print(
            Text.from_markup(
                f"{emoji('sparkles')} "
                f"[bold {ObsidianPalette.SUCCESS}]Obsidian Seal:[/bold {ObsidianPalette.SUCCESS}]"
                f" [{ObsidianPalette.SUCCESS}]No unused assets found \u2014 documentation tree is clean.[/{ObsidianPalette.SUCCESS}]"
            )
        )
        return

    _shared.console.print(f"\n[yellow]Found {len(unused)} unused asset(s):[/]")
    for path in unused:
        _shared.console.print(f"  [dim]{path}[/]")

    if dry_run:
        _shared.console.print("\n[blue]DRY RUN:[/] No files were deleted.")
        return

    if not yes:
        _shared.console.print()
        if not typer.confirm(
            f"Are you sure you want to permanently delete these {len(unused)} file(s)?",
            default=False,
        ):
            _shared.console.print("Cancelled.")
            raise typer.Exit(1)

    for path in unused:
        abs_path = docs_root / path
        abs_path.unlink(missing_ok=True)

    _shared.console.print(f"\n[green]SUCCESS:[/] Deleted {len(unused)} unused asset(s).")
