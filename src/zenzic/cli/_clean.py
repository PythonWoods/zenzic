# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Clean sub-commands: safely remove unused documentation files."""

from __future__ import annotations

from pathlib import Path

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
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Minimal one-line output for pre-commit hooks."
    ),
    engine: str | None = typer.Option(
        None,
        "--engine",
        help="Override the build engine adapter (e.g. mkdocs, zensical). "
        "Auto-detected from zenzic.toml when omitted.",
        metavar="ENGINE",
    ),
    exclude_dir: list[str] | None = typer.Option(
        None,
        "--exclude-dir",
        help="Additional directories to exclude from scanning (repeatable).",
        metavar="DIR",
    ),
    include_dir: list[str] | None = typer.Option(
        None,
        "--include-dir",
        help="Directories to force-include even if excluded by config (repeatable). "
        "Cannot override system guardrails.",
        metavar="DIR",
    ),
    path: str | None = typer.Argument(
        None,
        help=(
            "Limit the asset scan to a specific directory. "
            "Accepts paths relative to the repo root or to the docs directory. "
            "When omitted, the full docs directory is scanned."
        ),
        show_default=False,
    ),
) -> None:
    """Delete unused images and assets from the documentation."""
    # CEO-052 "The Sovereign Root Fix": when an explicit target PATH is given,
    # derive repo_root by searching upward FROM that path — not from CWD.
    _search_from: Path | None = None
    if path is not None:
        _pre = Path(path).resolve()
        _search_from = _pre.parent if _pre.is_file() else _pre
    repo_root = find_repo_root(search_from=_search_from)
    config, loaded_from_file = ZenzicConfig.load(repo_root)
    if not loaded_from_file and not quiet:
        _shared._print_no_config_hint()
    config = _shared._apply_engine_override(config, engine)

    from zenzic.core.adapters import get_adapter

    docs_root = (repo_root / config.docs_dir).resolve()
    adapter = get_adapter(config.build_context, docs_root, repo_root)
    adapter_meta = adapter.get_metadata_files()
    exclusion_mgr = _shared._build_exclusion_manager(
        config,
        repo_root,
        docs_root,
        exclude_dirs=exclude_dir,
        include_dirs=include_dir,
        adapter_metadata_files=adapter_meta,
    )

    unused = find_unused_assets(
        docs_root,
        exclusion_mgr,
        config=config,
        repo_root=repo_root,
        adapter_metadata_files=adapter_meta,
    )
    if not unused:
        if not quiet:
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

    if not quiet:
        _shared.console.print(f"\n[yellow]Found {len(unused)} unused asset(s):[/]")
        for asset in unused:
            _shared.console.print(f"  [dim]{asset}[/]")

    if dry_run:
        if not quiet:
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

    for asset_path in unused:
        abs_path = docs_root / asset_path
        abs_path.unlink(missing_ok=True)

    if not quiet:
        _shared.console.print(f"\n[green]SUCCESS:[/] Deleted {len(unused)} unused asset(s).")
