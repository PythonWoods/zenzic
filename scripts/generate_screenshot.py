# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Generate docs/assets/screenshot.svg via Rich SVG export.

Run via:
    nox -s screenshot
"""

from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from zenzic.core.scanner import find_orphans, find_placeholders, find_unused_assets
from zenzic.core.validator import validate_links, validate_snippets
from zenzic.models.config import ZenzicConfig


BROKEN_DOCS = Path(__file__).parent.parent / "examples" / "broken-docs"
OUT = Path(__file__).parent.parent / "docs" / "assets" / "screenshots" / "screenshot.svg"

console = Console(highlight=False, record=True, width=82)
config = ZenzicConfig.load(BROKEN_DOCS)
failed = False

console.print("[bold dim]$[/] [bold]zenzic check all --strict[/bold]")
console.print()

# Links
console.print("Running link check...")
link_errors = validate_links(BROKEN_DOCS, strict=True)
if link_errors:
    console.print(f"[red]BROKEN LINKS ({len(link_errors)}):[/]")
    for err in link_errors:
        console.print(f"  [yellow]{err}[/]")
    failed = True
else:
    console.print("[green]OK:[/] links.")

# Orphans
console.print("\nRunning orphan check...")
orphans = find_orphans(BROKEN_DOCS, config)
if orphans:
    console.print(f"[red]ORPHANS ({len(orphans)}):[/]")
    for path in orphans:
        console.print(f"  [yellow]{path}[/]")
    failed = True
else:
    console.print("[green]OK:[/] orphans.")

# Snippets
console.print("\nRunning snippet check...")
snippet_errors = validate_snippets(BROKEN_DOCS, config)
if snippet_errors:
    console.print(f"[red]INVALID SNIPPETS ({len(snippet_errors)}):[/]")
    for err in snippet_errors:
        console.print(f"  [yellow]{err.file_path}:{err.line_no}[/] - {err.message}")
    failed = True
else:
    console.print("[green]OK:[/] snippets.")

# Placeholders
console.print("\nRunning placeholder check...")
placeholders = find_placeholders(BROKEN_DOCS, config)
if placeholders:
    console.print(f"[red]PLACEHOLDERS ({len(placeholders)}):[/]")
    for finding in placeholders:
        console.print(
            f"  [yellow]{finding.file_path}:{finding.line_no}[/]"
            f" [{finding.issue}] - {finding.detail}"
        )
    failed = True
else:
    console.print("[green]OK:[/] placeholders.")

# Unused assets
console.print("\nRunning unused assets check...")
unused_assets = find_unused_assets(BROKEN_DOCS, config)
if unused_assets:
    console.print(f"[red]UNUSED ASSETS ({len(unused_assets)}):[/]")
    for path in unused_assets:
        console.print(f"  [yellow]{path}[/]")
    failed = True
else:
    console.print("[green]OK:[/] assets.")

if failed:
    console.print("\n[red]FAILED:[/] One or more checks failed.")
else:
    console.print("\n[green]SUCCESS:[/] All checks passed.")

OUT.parent.mkdir(parents=True, exist_ok=True)
console.save_svg(str(OUT), title="zenzic check all --strict")
print(f"Saved → {OUT.relative_to(Path(__file__).parent.parent)}")

# Clean up the mkdocs build artefact produced by validate_links.
site_dir = BROKEN_DOCS / "site"
if site_dir.exists():
    shutil.rmtree(site_dir)
