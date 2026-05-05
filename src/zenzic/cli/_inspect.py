# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Inspect sub-commands: introspect the Zenzic scanner arsenal and plugin registry."""

from __future__ import annotations

import typer
from rich import box
from rich.table import Table
from rich.text import Text

from zenzic.core.codes import CORE_SCANNERS
from zenzic.core.scanner import find_repo_root
from zenzic.core.ui import SentinelPalette
from zenzic.models.config import ZenzicConfig

from . import _shared


inspect_app = typer.Typer(
    name="inspect",
    help=f"[bold {SentinelPalette.BRAND}]Inspect[/] — Introspect the Zenzic scanner arsenal and plugin registry.",
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
        title=f"[bold {SentinelPalette.BRAND}]Core Scanners[/]  [dim](built-in)[/dim]",
        title_justify="left",
        box=box.ROUNDED,
        border_style=SentinelPalette.DIM,
        header_style=SentinelPalette.STYLE_BRAND,
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
            f"  [{SentinelPalette.DIM}]\u26a0  Exit 2 and Exit 3 are non-suppressible \u2014 "
            f"--exit-zero has no effect on Shield or Blood Sentinel.[/{SentinelPalette.DIM}]"
        )
    )
    _shared.console.print()

    # ── Section B: Extensible Rules ───────────────────────────────────────
    rules = list_plugin_rules()

    rules_table = Table(
        title=(
            f"[bold {SentinelPalette.BRAND}]Extensible Rules[/]  "
            f"[dim](plugin system \u2014 zenzic.rules entry-point group)[/dim]"
        ),
        title_justify="left",
        box=box.ROUNDED,
        border_style=SentinelPalette.DIM,
        header_style=SentinelPalette.STYLE_BRAND,
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
                f"[{SentinelPalette.DIM}]No third-party plugins installed. "
                f"Register rules via the zenzic.rules entry-point group.[/{SentinelPalette.DIM}]"
            ),
        )

    _shared.console.print(rules_table)
    _shared.console.print()

    rule_count = len(rules)
    _shared.console.print(
        Text.from_markup(
            f"  [{SentinelPalette.DIM}]{len(CORE_SCANNERS)} built-in scanners \u00b7 "
            f"{rule_count} extensible rule{'s' if rule_count != 1 else ''} registered"
            f"[/{SentinelPalette.DIM}]"
        )
    )
    _shared.console.print()

    # ── Section C: Engine-specific Link Bypasses ──────────────────────────
    bypass_table = Table(
        title=(
            f"[bold {SentinelPalette.BRAND}]Engine-specific Link Bypasses[/]  "
            f"[dim](Rule R21 \u2014 Protocol Sovereignty)[/dim]"
        ),
        title_justify="left",
        box=box.ROUNDED,
        border_style=SentinelPalette.DIM,
        header_style=SentinelPalette.STYLE_BRAND,
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
                f"[bold]pathname:[/bold]  [{SentinelPalette.DIM}](static-asset routing escape hatch)[/{SentinelPalette.DIM}]"
            ),
        ),
        (
            "mkdocs",
            "MkDocsAdapter",
            Text.from_markup(f"[{SentinelPalette.DIM}](none)[/{SentinelPalette.DIM}]"),
        ),
        (
            "zensical",
            "ZensicalAdapter",
            Text.from_markup(f"[{SentinelPalette.DIM}](none)[/{SentinelPalette.DIM}]"),
        ),
        (
            "standalone",
            "StandaloneAdapter",
            Text.from_markup(f"[{SentinelPalette.DIM}](none)[/{SentinelPalette.DIM}]"),
        ),
    ]
    for _engine, _adapter, _bypasses in _BYPASS_ROWS:
        bypass_table.add_row(_engine, _adapter, _bypasses)

    _shared.console.print(bypass_table)
    _shared.console.print()
    _shared.console.print(
        Text.from_markup(
            f"  [{SentinelPalette.DIM}]R21: engine-specific behaviour is declared in the adapter "
            f"via get_link_scheme_bypasses() \u2014 validator.py never hardcodes engine names."
            f"[/{SentinelPalette.DIM}]"
        )
    )


# Canonical command
inspect_app.command(
    name="capabilities",
    help="Show all built-in scanners, plugin rules, and engine-specific link bypasses.",
)(_inspect_capabilities)


@inspect_app.command(name="routes")
def inspect_routes(
    kind: str = typer.Option(
        "all",
        "--kind",
        help="Filter routes by kind: physical, virtual, or all.",
        show_default=True,
    ),
    as_json: bool = typer.Option(
        False,
        "--json",
        help="Output the route map as machine-readable JSON.",
    ),
) -> None:
    """Export the complete site map — URLs, source files, and digest fingerprints.

    Each route entry carries:

    * **url** — the canonical path,
    * **kind** — physical, tag, tag_index, pagination, author, or author_index,
    * **source_files** — repo-relative POSIX paths that activate the route, and
    * **digest** — SHA-256 of ``url + ':' + ','.join(sorted(source_files))``.
    """
    import hashlib
    import json as _json
    import sys
    from pathlib import Path

    from zenzic.core.adapters import get_adapter
    from zenzic.core.discovery import (
        iter_extra_content_markdown_sources,
        iter_markdown_sources,
    )
    from zenzic.models.vsm import build_vsm

    _VALID_KINDS = frozenset({"physical", "virtual", "all"})
    if kind not in _VALID_KINDS:
        # JSON Purity Invariant: errors always go to stderr, never stdout
        msg = "Error: --kind must be one of: physical, virtual, all\n"
        if as_json:
            sys.stderr.write(msg)
        else:
            _shared.console.print(
                "[bold red]Error:[/] --kind must be one of: physical, virtual, all"
            )
        raise typer.Exit(1)

    repo_root = find_repo_root()
    config, _ = ZenzicConfig.load(repo_root)
    docs_root = (repo_root / config.docs_dir).resolve()
    exclusion_mgr = _shared._build_exclusion_manager(config, repo_root, docs_root)
    adapter = get_adapter(config.build_context, docs_root, repo_root)

    # ── Pass 1: load docs markdown files ──────────────────────────────────────
    md_contents: dict[Path, str] = {}
    for md_file in iter_markdown_sources(docs_root, config, exclusion_mgr):
        try:
            md_contents[md_file.resolve()] = md_file.read_text(encoding="utf-8")
        except OSError:
            continue

    # ── Pass 1c: include extra content roots (blog/, etc.) ────────────────────
    extra_content_roots: list[tuple[Path, str]] = []
    if hasattr(adapter, "get_extra_content_roots"):
        for content_root in adapter.get_extra_content_roots(repo_root):
            extra_content_roots.append((content_root.path, content_root.url_prefix))
            for abs_path, _ in iter_extra_content_markdown_sources(
                content_root.path, content_root.url_prefix, config, exclusion_mgr
            ):
                try:
                    md_contents[abs_path.resolve()] = abs_path.read_text(encoding="utf-8")
                except OSError:
                    continue

    vsm = build_vsm(adapter, docs_root, md_contents, extra_content_roots=extra_content_roots)

    # ── Virtual route kind lookup (call once; idempotent with build_vsm's call) ─
    virtual_kind_map: dict[str, str] = {}
    if hasattr(adapter, "get_virtual_routes"):
        for vr in adapter.get_virtual_routes(md_contents):
            virtual_kind_map[vr.url] = vr.kind

    # ── Source file normalisation ──────────────────────────────────────────────
    # Extra-content-root files are already repo-relative (e.g. "blog/post.md").
    # Docs-root files are relative to docs/, so prepend docs_dir to make them
    # repo-relative (e.g. "intro.md" → "docs/intro.md").
    _extra_prefixes: frozenset[str] = frozenset(
        prefix.rstrip("/") for _, prefix in extra_content_roots if prefix
    )
    _docs_prefix = config.docs_dir.as_posix().rstrip("/")

    def _physical_source(route_source: str) -> str:
        for pfx in _extra_prefixes:
            if route_source == pfx or route_source.startswith(pfx + "/"):
                return route_source  # already repo-relative
        return _docs_prefix + "/" + route_source

    def _digest(url: str, source_files: list[str]) -> str:
        raw = url + ":" + ",".join(sorted(source_files))
        return hashlib.sha256(raw.encode()).hexdigest()

    # ── Build records ──────────────────────────────────────────────────────────
    records: list[dict[str, str | list[str]]] = []
    for url, route in sorted(vsm.items()):
        if not url:
            continue
        is_virtual = route.source == "<virtual>"
        if kind == "physical" and is_virtual:
            continue
        if kind == "virtual" and not is_virtual:
            continue
        if is_virtual:
            route_kind: str = virtual_kind_map.get(url, "tag")
            source_files: list[str] = sorted(route.proxy_sources)
        else:
            route_kind = "physical"
            source_files = [_physical_source(route.source)]

        records.append(
            {
                "url": url,
                "kind": route_kind,
                "source_files": source_files,
                "digest": _digest(url, source_files),
            }
        )

    # ── Output ─────────────────────────────────────────────────────────────────
    if as_json:
        # JSON Purity Invariant (Rule R20 Machine Silence):
        # stdout must contain EXCLUSIVELY valid JSON — no Rich markup, no ANSI
        # codes, no banners. Write directly to sys.stdout, bypassing the Rich
        # console entirely.
        sys.stdout.write(_json.dumps({"routes": records}, indent=2, ensure_ascii=False))
        sys.stdout.write("\n")
        sys.stdout.flush()
        return

    label = f"{len(records)} route{'s' if len(records) != 1 else ''}"
    table = Table(
        title=f"[bold]Site Map[/] · {label}",
        title_justify="left",
        box=box.ROUNDED,
        border_style=SentinelPalette.DIM,
        header_style=SentinelPalette.STYLE_BRAND,
        pad_edge=True,
        padding=(0, 1),
    )
    table.add_column("URL", style="bold cyan", no_wrap=True)
    table.add_column("Kind", min_width=10)
    table.add_column("Source Files")
    table.add_column("Digest", style="dim", min_width=12, no_wrap=True)

    for rec in records:
        table.add_row(
            str(rec["url"]),
            str(rec["kind"]),
            ", ".join(str(sf) for sf in rec["source_files"]),
            str(rec["digest"])[:12] + "…",
        )

    _shared.console.print()
    _shared.console.print(table)
    _shared.console.print()
