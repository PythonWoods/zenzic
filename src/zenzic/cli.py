# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""CLI command definitions for zenzic."""

from __future__ import annotations

import difflib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from zenzic.core.adapters import list_adapter_engines
from zenzic.core.exclusion import LayeredExclusionManager
from zenzic.core.reporter import Finding, SentinelReporter
from zenzic.core.scanner import (
    PlaceholderFinding,
    _map_shield_to_finding,
    find_orphans,
    find_placeholders,
    find_repo_root,
    find_unused_assets,
    scan_docs_references,
)
from zenzic.core.scorer import ScoreReport, compute_score, load_snapshot, save_snapshot
from zenzic.core.validator import (
    LinkError,
    SnippetError,
    check_nav_contract,
    validate_links,
    validate_links_structured,
    validate_snippets,
)
from zenzic.models.config import ZenzicConfig
from zenzic.models.references import IntegrityReport
from zenzic.ui import INDIGO, SLATE, emoji


check_app = typer.Typer(
    name="check",
    help="[bold #4f46e5]Check[/] — Run documentation quality checks.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

clean_app = typer.Typer(
    name="clean",
    help="[bold #4f46e5]Clean[/] — Safely remove unused documentation files.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

plugins_app = typer.Typer(
    name="plugins",
    help="[bold #4f46e5]Plugins[/] — Inspect the Zenzic plugin registry.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console(highlight=False)

# ── CI-safe emoji degradation (delegated to zenzic.ui) ──────────────────────


_NO_CONFIG_HINT = Panel(
    "Using built-in defaults — no [bold]zenzic.toml[/] found.\n"
    "Run [bold cyan]zenzic init[/] to create a project configuration file.\n"
    "Customise docs directory, excluded paths, engine adapter, and lint rules.",
    title=f"[bold yellow]{emoji('info')} Zenzic Tip[/]",
    border_style="yellow",
    expand=False,
)


def _print_no_config_hint() -> None:
    """Print a one-time informational panel when running without zenzic.toml."""
    console.print(_NO_CONFIG_HINT)
    console.print()


def _apply_engine_override(config: ZenzicConfig, engine: str | None) -> ZenzicConfig:
    """Return *config* with ``build_context.engine`` replaced by *engine*.

    When *engine* is ``None`` or ``"auto"``, the original config is returned
    unchanged.  When *engine* is not a registered adapter, a Rich error is
    printed to stderr and the process exits with code 1.
    """
    if not engine or engine == "auto":
        return config
    known = list_adapter_engines()
    if engine not in known:
        engines_fmt = ", ".join(f"[bold]{e}[/]" for e in known) if known else "(none installed)"
        hint = ""
        suggestions = difflib.get_close_matches(engine, known, n=1, cutoff=0.5)
        if suggestions:
            hint = f"\n\n  Did you mean [bold cyan]{suggestions[0]}[/]?"
        console.print(
            f"[red]ERROR:[/] Unknown engine adapter [bold]{engine!r}[/].\n"
            f"Installed adapters: {engines_fmt}{hint}"
        )
        raise typer.Exit(1)
    new_context = config.build_context.model_copy(update={"engine": engine})
    return config.model_copy(update={"build_context": new_context})


def _render_link_error(err: LinkError, docs_root: Path) -> None:
    """Print a single LinkError with a Visual Snippet when source context is available."""
    try:
        rel = err.file_path.relative_to(docs_root)
        location = f"[dim]{rel}:{err.line_no}[/]"
    except ValueError:
        location = f"[dim]{err.file_path.name}:{err.line_no}[/]"

    # Strip the redundant "file:lineno: " prefix the message already carries
    # so we don't repeat it after the location badge.
    raw_msg = err.message
    prefix = f"{err.file_path.relative_to(docs_root).as_posix() if err.file_path != docs_root else ''}:{err.line_no}: "
    body = raw_msg[len(prefix) :] if raw_msg.startswith(prefix) else raw_msg

    type_badge = f"[[bold red]{err.error_type}[/]]" if err.error_type != "LINK_ERROR" else ""
    header = f"  {type_badge} {location} — {body}"
    console.print(header)

    if err.source_line:
        console.print(f"    [dim]│[/] [italic]{err.source_line}[/]")


def _build_exclusion_manager(
    config: ZenzicConfig,
    repo_root: Path,
    docs_root: Path,
    *,
    exclude_dirs: list[str] | None = None,
    include_dirs: list[str] | None = None,
) -> LayeredExclusionManager:
    """Construct a :class:`LayeredExclusionManager` from config + CLI flags.

    This is the **single factory** for exclusion managers in the CLI layer.
    Every command must call this and pass the result down the pipeline.

    Includes F4-1 jailbreak protection: rejects ``docs_root`` paths that
    escape the repository root via path traversal (``../``).
    """
    _validate_docs_root(repo_root, docs_root)
    return LayeredExclusionManager(
        config,
        repo_root=repo_root,
        docs_root=docs_root,
        cli_exclude=exclude_dirs,
        cli_include=include_dirs,
    )


def _validate_docs_root(repo_root: Path, docs_root: Path) -> None:
    """F4-1: Reject docs_dir paths that escape the repository root.

    Raises :class:`typer.Exit` with code 3 (Blood Sentinel) if
    ``docs_root.resolve()`` is not under ``repo_root.resolve()``.
    This prevents path-traversal attacks via ``docs_dir = "../../etc"``.
    """
    resolved_repo = repo_root.resolve()
    resolved_docs = docs_root.resolve()
    try:
        resolved_docs.relative_to(resolved_repo)
    except ValueError:
        console.print(
            f"[bold red]BLOOD SENTINEL:[/] docs_dir resolves to "
            f"[bold]{resolved_docs}[/] which is outside the repository root "
            f"[bold]{resolved_repo}[/]. Path traversal blocked."
        )
        raise typer.Exit(3) from None


def _count_docs_assets(
    docs_root: Path,
    repo_root: Path,
    exclusion_mgr: LayeredExclusionManager,
    config: ZenzicConfig | None = None,
) -> tuple[int, int]:
    """Return ``(docs_count, assets_count)`` for the Sentinel telemetry line.

    When *config* is provided and the adapter exposes ``get_locale_source_roots()``,
    locale translation trees (e.g. Docusaurus ``i18n/``) are counted in
    ``docs_count`` as well.
    """
    from zenzic.core.discovery import walk_files
    from zenzic.models.config import SYSTEM_EXCLUDED_DIRS

    _INERT = {".css", ".js"}
    _CONFIG = {".yml", ".yaml", ".toml"}
    _DOC_EXT = {".md", ".mdx"}
    if not docs_root.is_dir():
        return 0, 0
    docs_count = sum(
        1
        for p in walk_files(docs_root, SYSTEM_EXCLUDED_DIRS, exclusion_mgr)
        if p.suffix.lower() in _DOC_EXT or p.suffix.lower() in _CONFIG
    )
    docs_count += sum(
        1 for p in repo_root.iterdir() if p.is_file() and p.suffix.lower() in {".yml", ".yaml"}
    )
    assets_count = sum(
        1
        for p in walk_files(docs_root, SYSTEM_EXCLUDED_DIRS, exclusion_mgr)
        if p.suffix.lower() not in _INERT
        and p.suffix.lower() not in _CONFIG
        and p.suffix.lower() not in _DOC_EXT
    )
    # Count locale source files (Docusaurus i18n only when config is available).
    if config is not None:
        from zenzic.core.adapters import get_adapter

        adapter = get_adapter(config.build_context, docs_root, repo_root)
        if hasattr(adapter, "get_locale_source_roots"):
            for locale_root, _ in adapter.get_locale_source_roots(repo_root):
                docs_count += sum(
                    1
                    for p in walk_files(locale_root, SYSTEM_EXCLUDED_DIRS, exclusion_mgr)
                    if p.suffix.lower() in _DOC_EXT
                )
    return docs_count, assets_count


@check_app.command(name="links")
def check_links(
    strict: bool = typer.Option(False, "--strict", "-s", help="Exit non-zero on any warning."),
    show_info: bool = typer.Option(
        False, "--show-info", help="Show info-level findings (e.g. circular links) in the report."
    ),
) -> None:
    """Check for broken internal links. Pass --strict to also validate external URLs."""
    from zenzic import __version__

    repo_root = find_repo_root()
    config, _ = ZenzicConfig.load(repo_root)
    docs_root = (repo_root / config.docs_dir).resolve()
    exclusion_mgr = _build_exclusion_manager(config, repo_root, docs_root)

    def _rel(path: Path) -> str:
        try:
            return str(path.relative_to(docs_root))
        except ValueError:
            return str(path)

    t0 = time.monotonic()
    link_errors = validate_links_structured(
        docs_root,
        exclusion_mgr,
        repo_root=repo_root,
        config=config,
        strict=strict,
    )
    elapsed = time.monotonic() - t0

    findings = [
        Finding(
            rel_path=_rel(err.file_path),
            line_no=err.line_no,
            code=err.error_type,
            severity=(
                "security_incident"
                if err.error_type == "PATH_TRAVERSAL_SUSPICIOUS"
                else "info"
                if err.error_type == "CIRCULAR_LINK"
                else "error"
            ),
            message=err.message,
            source_line=err.source_line,
            col_start=err.col_start,
            match_text=err.match_text,
        )
        for err in link_errors
    ]

    docs_count, assets_count = _count_docs_assets(docs_root, repo_root, exclusion_mgr)
    reporter = SentinelReporter(console, docs_root, docs_dir=str(config.docs_dir))
    errors, warnings = reporter.render(
        findings,
        version=__version__,
        elapsed=elapsed,
        docs_count=docs_count,
        assets_count=assets_count,
        engine=config.build_context.engine if hasattr(config, "build_context") else "auto",
        ok_message="No broken links found.",
        show_info=show_info,
    )
    incidents = sum(1 for f in findings if f.severity == "security_incident")
    if incidents:
        raise typer.Exit(3)
    if errors:
        raise typer.Exit(1)


@check_app.command(name="orphans")
def check_orphans(
    engine: str | None = typer.Option(
        None,
        "--engine",
        help="Override the build engine adapter (e.g. mkdocs, zensical). "
        "Auto-detected from zenzic.toml when omitted.",
        metavar="ENGINE",
    ),
    show_info: bool = typer.Option(
        False, "--show-info", help="Show info-level findings (e.g. circular links) in the report."
    ),
) -> None:
    """Detect .md files not listed in the nav."""
    from zenzic import __version__

    repo_root = find_repo_root()
    config, loaded_from_file = ZenzicConfig.load(repo_root)
    if not loaded_from_file:
        _print_no_config_hint()
    config = _apply_engine_override(config, engine)
    docs_root = (repo_root / config.docs_dir).resolve()
    exclusion_mgr = _build_exclusion_manager(config, repo_root, docs_root)

    t0 = time.monotonic()
    orphans = find_orphans(docs_root, exclusion_mgr, repo_root=repo_root, config=config)
    elapsed = time.monotonic() - t0

    findings = [
        Finding(
            rel_path=str(path),
            line_no=0,
            code="ORPHAN",
            severity="warning",
            message="Physical file not listed in navigation.",
        )
        for path in orphans
    ]

    docs_count, assets_count = _count_docs_assets(docs_root, repo_root, exclusion_mgr)
    reporter = SentinelReporter(console, docs_root, docs_dir=str(config.docs_dir))
    errors, warnings = reporter.render(
        findings,
        version=__version__,
        elapsed=elapsed,
        docs_count=docs_count,
        assets_count=assets_count,
        engine=config.build_context.engine if hasattr(config, "build_context") else "auto",
        strict=True,
        ok_message="No orphan pages found.",
        show_info=show_info,
    )
    if errors or warnings:
        raise typer.Exit(1)


@check_app.command(name="snippets")
def check_snippets(
    show_info: bool = typer.Option(
        False, "--show-info", help="Show info-level findings (e.g. circular links) in the report."
    ),
) -> None:
    """Validate Python code blocks in documentation Markdown files."""
    from zenzic import __version__

    repo_root = find_repo_root()
    config, loaded_from_file = ZenzicConfig.load(repo_root)
    if not loaded_from_file:
        _print_no_config_hint()
    docs_root = (repo_root / config.docs_dir).resolve()
    exclusion_mgr = _build_exclusion_manager(config, repo_root, docs_root)

    def _rel(path: Path) -> str:
        try:
            return str(path.relative_to(docs_root))
        except ValueError:
            return str(path)

    t0 = time.monotonic()
    snippet_errors = validate_snippets(docs_root, exclusion_mgr, config=config)
    elapsed = time.monotonic() - t0

    findings: list[Finding] = []
    for s_err in snippet_errors:
        src = ""
        if s_err.line_no > 0 and s_err.file_path.is_file():
            try:
                lines = s_err.file_path.read_text(encoding="utf-8").splitlines()
                if 0 < s_err.line_no <= len(lines):
                    src = lines[s_err.line_no - 1].strip()
            except OSError:
                pass
        findings.append(
            Finding(
                rel_path=_rel(s_err.file_path),
                line_no=s_err.line_no,
                code="SNIPPET",
                severity="error",
                message=s_err.message,
                source_line=src,
            )
        )

    docs_count, assets_count = _count_docs_assets(docs_root, repo_root, exclusion_mgr)
    reporter = SentinelReporter(console, docs_root, docs_dir=str(config.docs_dir))
    errors, warnings = reporter.render(
        findings,
        version=__version__,
        elapsed=elapsed,
        docs_count=docs_count,
        assets_count=assets_count,
        engine=config.build_context.engine if hasattr(config, "build_context") else "auto",
        ok_message="All code snippets are syntactically valid.",
        show_info=show_info,
    )
    if errors:
        raise typer.Exit(1)


@check_app.command(name="references")
def check_references(
    strict: bool = typer.Option(
        False,
        "--strict",
        "-s",
        help="Treat Dead Definitions and duplicate defs as errors (not warnings).",
    ),
    links: bool = typer.Option(
        False,
        "--links",
        "-l",
        help="Also validate external HTTP/HTTPS reference URLs via async HEAD requests.",
    ),
    show_info: bool = typer.Option(
        False, "--show-info", help="Show info-level findings (e.g. circular links) in the report."
    ),
) -> None:
    """Run the Two-Pass Reference Pipeline: harvest definitions, check integrity, run Shield.

    Pass 1 — Harvest: extract [id]: url definitions, detect secrets (Shield).
    Pass 2 — Cross-Check: resolve [text][id] links against the ReferenceMap.
    Pass 3 — Report: compute Reference Integrity score, flag Dead Definitions and Dangling References.

    With --links: validate all external URLs via deduplicated async HEAD requests
    (one ping per unique URL across the entire docs tree).

    Exit codes:
      0 — all references resolve; no secrets found.
      1 — Dangling References or (with --strict) warnings found.
      2 — SECURITY CRITICAL: a secret was detected in a reference URL.
    """
    from zenzic import __version__

    repo_root = find_repo_root()
    config, loaded_from_file = ZenzicConfig.load(repo_root)
    if not loaded_from_file:
        _print_no_config_hint()
    docs_root = (repo_root / config.docs_dir).resolve()
    exclusion_mgr = _build_exclusion_manager(config, repo_root, docs_root)

    def _rel(path: Path) -> str:
        try:
            return str(path.relative_to(docs_root))
        except ValueError:
            return str(path)

    t0 = time.monotonic()
    reports, ext_link_errors = scan_docs_references(
        docs_root,
        exclusion_mgr,
        config=config,
        validate_links=links,
    )
    elapsed = time.monotonic() - t0

    # ── Build unified findings list ────────────────────────────────────────────
    findings: list[Finding] = []
    for report in reports:
        rel = _rel(report.file_path)
        _lines: list[str] = []
        if report.file_path.is_file():
            try:
                _lines = report.file_path.read_text(encoding="utf-8").splitlines()
            except OSError:
                pass
        for ref_f in report.findings:
            src = ""
            if _lines and 0 < ref_f.line_no <= len(_lines):
                src = _lines[ref_f.line_no - 1].strip()
            findings.append(
                Finding(
                    rel_path=rel,
                    line_no=ref_f.line_no,
                    code=ref_f.issue,
                    severity="warning" if ref_f.is_warning else "error",
                    message=ref_f.detail,
                    source_line=src,
                )
            )
        for rule_f in report.rule_findings:
            findings.append(
                Finding(
                    rel_path=rel,
                    line_no=rule_f.line_no,
                    code=rule_f.rule_id,
                    severity=rule_f.severity,
                    message=rule_f.message,
                    source_line=rule_f.matched_line or "",
                    col_start=rule_f.col_start,
                    match_text=rule_f.match_text or "",
                )
            )
        for sf in report.security_findings:
            findings.append(_map_shield_to_finding(sf, docs_root))

    for err_str in ext_link_errors:
        findings.append(
            Finding(
                rel_path="(external-urls)",
                line_no=0,
                code="LINK_URL",
                severity="error",
                message=err_str,
            )
        )

    docs_count, assets_count = _count_docs_assets(docs_root, repo_root, exclusion_mgr)
    reporter = SentinelReporter(console, docs_root, docs_dir=str(config.docs_dir))
    errors, warnings = reporter.render(
        findings,
        version=__version__,
        elapsed=elapsed,
        docs_count=docs_count,
        assets_count=assets_count,
        engine=config.build_context.engine if hasattr(config, "build_context") else "auto",
        strict=strict,
        ok_message="All references resolved.",
        show_info=show_info,
    )

    breaches = sum(1 for f in findings if f.severity == "security_breach")
    if breaches:
        raise typer.Exit(2)
    if errors or (strict and warnings):
        raise typer.Exit(1)


@check_app.command(name="assets")
def check_assets(
    show_info: bool = typer.Option(
        False, "--show-info", help="Show info-level findings (e.g. circular links) in the report."
    ),
) -> None:
    """Detect unused images and assets in the documentation."""
    from zenzic import __version__

    repo_root = find_repo_root()
    config, loaded_from_file = ZenzicConfig.load(repo_root)
    if not loaded_from_file:
        _print_no_config_hint()
    docs_root = (repo_root / config.docs_dir).resolve()
    exclusion_mgr = _build_exclusion_manager(config, repo_root, docs_root)

    t0 = time.monotonic()
    unused = find_unused_assets(docs_root, exclusion_mgr, config=config)
    elapsed = time.monotonic() - t0

    findings = [
        Finding(
            rel_path=str(path),
            line_no=0,
            code="ASSET",
            severity="warning",
            message="File not referenced in any documentation page.",
        )
        for path in unused
    ]

    docs_count, assets_count = _count_docs_assets(docs_root, repo_root, exclusion_mgr)
    reporter = SentinelReporter(console, docs_root, docs_dir=str(config.docs_dir))
    errors, warnings = reporter.render(
        findings,
        version=__version__,
        elapsed=elapsed,
        docs_count=docs_count,
        assets_count=assets_count,
        engine=config.build_context.engine if hasattr(config, "build_context") else "auto",
        strict=True,
        ok_message="No unused assets found.",
        show_info=show_info,
    )
    if errors or warnings:
        raise typer.Exit(1)


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
    exclusion_mgr = _build_exclusion_manager(config, repo_root, docs_root)

    unused = find_unused_assets(docs_root, exclusion_mgr, config=config)
    if not unused:
        console.print("\n[green]OK:[/] no unused assets to clean.")
        return

    console.print(f"\n[yellow]Found {len(unused)} unused asset(s):[/]")
    for path in unused:
        console.print(f"  [dim]{path}[/]")

    if dry_run:
        console.print("\n[blue]DRY RUN:[/] No files were deleted.")
        return

    if not yes:
        console.print()
        if not typer.confirm(
            f"Are you sure you want to permanently delete these {len(unused)} file(s)?",
            default=False,
        ):
            console.print("Cancelled.")
            raise typer.Exit(1)

    # Delete the files using absolute paths
    for path in unused:
        abs_path = docs_root / path
        abs_path.unlink(missing_ok=True)

    console.print(f"\n[green]SUCCESS:[/] Deleted {len(unused)} unused asset(s).")


@check_app.command(name="placeholders")
def check_placeholders(
    show_info: bool = typer.Option(
        False, "--show-info", help="Show info-level findings (e.g. circular links) in the report."
    ),
) -> None:
    """Detect pages with < 50 words or containing TODOs/stubs."""
    from zenzic import __version__

    repo_root = find_repo_root()
    config, loaded_from_file = ZenzicConfig.load(repo_root)
    if not loaded_from_file:
        _print_no_config_hint()
    docs_root = (repo_root / config.docs_dir).resolve()
    exclusion_mgr = _build_exclusion_manager(config, repo_root, docs_root)

    t0 = time.monotonic()
    raw_findings = find_placeholders(docs_root, exclusion_mgr, config=config)
    elapsed = time.monotonic() - t0

    findings: list[Finding] = []
    for pf in raw_findings:
        src = ""
        if pf.line_no > 0:
            abs_path = docs_root / pf.file_path
            if abs_path.is_file():
                try:
                    lines = abs_path.read_text(encoding="utf-8").splitlines()
                    if 0 < pf.line_no <= len(lines):
                        src = lines[pf.line_no - 1].strip()
                except OSError:
                    pass
        findings.append(
            Finding(
                rel_path=str(pf.file_path),
                line_no=pf.line_no,
                code=pf.issue,
                severity="warning",
                message=pf.detail,
                source_line=src,
                col_start=pf.col_start,
                match_text=pf.match_text,
            )
        )

    docs_count, assets_count = _count_docs_assets(docs_root, repo_root, exclusion_mgr)
    reporter = SentinelReporter(console, docs_root, docs_dir=str(config.docs_dir))
    errors, warnings = reporter.render(
        findings,
        version=__version__,
        elapsed=elapsed,
        docs_count=docs_count,
        assets_count=assets_count,
        engine=config.build_context.engine if hasattr(config, "build_context") else "auto",
        strict=True,
        ok_message="No placeholder stubs found.",
        show_info=show_info,
    )
    if errors or warnings:
        raise typer.Exit(1)


@dataclass
class _AllCheckResults:
    link_errors: list[LinkError]
    orphans: list[Path]
    snippet_errors: list[SnippetError]
    placeholders: list[PlaceholderFinding]
    unused_assets: list[Path]
    nav_contract_errors: list[str]
    reference_reports: list[IntegrityReport]
    security_events: int

    @property
    def failed(self) -> bool:
        ref_errors = any(r.has_errors for r in self.reference_reports)
        return bool(
            self.link_errors
            or self.orphans
            or self.snippet_errors
            or self.placeholders
            or self.unused_assets
            or self.nav_contract_errors
            or ref_errors
            or self.security_events
        )


def _collect_all_results(
    repo_root: Path,
    docs_root: Path,
    config: ZenzicConfig,
    exclusion_mgr: LayeredExclusionManager,
    strict: bool,
) -> _AllCheckResults:
    """Run all seven checks and return results as a typed container."""
    from zenzic.core.adapters import get_adapter

    # Resolve locale source roots from the adapter (Docusaurus i18n support).
    adapter = get_adapter(config.build_context, docs_root, repo_root)
    locale_roots: list[tuple[Path, str]] | None = None
    if hasattr(adapter, "get_locale_source_roots"):
        _roots = adapter.get_locale_source_roots(repo_root)
        locale_roots = _roots if _roots else None

    ref_reports, _ = scan_docs_references(
        docs_root,
        exclusion_mgr,
        config=config,
        validate_links=False,
        locale_roots=locale_roots,
    )
    security_events = sum(len(r.security_findings) for r in ref_reports)
    return _AllCheckResults(
        link_errors=validate_links_structured(
            docs_root,
            exclusion_mgr,
            repo_root=repo_root,
            config=config,
            strict=strict,
        ),
        orphans=find_orphans(docs_root, exclusion_mgr, repo_root=repo_root, config=config),
        snippet_errors=validate_snippets(docs_root, exclusion_mgr, config=config),
        placeholders=find_placeholders(
            docs_root, exclusion_mgr, config=config, repo_root=repo_root
        ),
        unused_assets=find_unused_assets(
            docs_root, exclusion_mgr, config=config, repo_root=repo_root
        ),
        nav_contract_errors=check_nav_contract(repo_root, exclusion_mgr),
        reference_reports=ref_reports,
        security_events=security_events,
    )


def _to_findings(results: _AllCheckResults, docs_root: Path) -> list[Finding]:
    """Convert all result types into a flat list of :class:`Finding`."""
    findings: list[Finding] = []

    def _rel(path: Path) -> str:
        try:
            return str(path.relative_to(docs_root))
        except ValueError:
            return str(path)

    for err in results.link_errors:
        findings.append(
            Finding(
                rel_path=_rel(err.file_path),
                line_no=err.line_no,
                code=err.error_type,
                severity=(
                    "security_incident"
                    if err.error_type == "PATH_TRAVERSAL_SUSPICIOUS"
                    else "info"
                    if err.error_type == "CIRCULAR_LINK"
                    else "error"
                ),
                message=err.message,
                source_line=err.source_line,
                col_start=err.col_start,
                match_text=err.match_text,
            )
        )

    for path in results.orphans:
        findings.append(
            Finding(
                rel_path=str(path),
                line_no=0,
                code="ORPHAN",
                severity="warning",
                message="Physical file not listed in navigation.",
            )
        )

    for s_err in results.snippet_errors:
        src = ""
        if s_err.line_no > 0 and s_err.file_path.is_file():
            try:
                lines = s_err.file_path.read_text(encoding="utf-8").splitlines()
                if 0 < s_err.line_no <= len(lines):
                    src = lines[s_err.line_no - 1].strip()
            except OSError:
                pass
        findings.append(
            Finding(
                rel_path=_rel(s_err.file_path),
                line_no=s_err.line_no,
                code="SNIPPET",
                severity="error",
                message=s_err.message,
                source_line=src,
            )
        )

    for pf in results.placeholders:
        src = ""
        if pf.line_no > 0:
            abs_path = docs_root / pf.file_path
            if abs_path.is_file():
                try:
                    lines = abs_path.read_text(encoding="utf-8").splitlines()
                    if 0 < pf.line_no <= len(lines):
                        src = lines[pf.line_no - 1].strip()
                except OSError:
                    pass
        findings.append(
            Finding(
                rel_path=str(pf.file_path),
                line_no=pf.line_no,
                code=pf.issue,
                severity="warning",
                message=pf.detail,
                source_line=src,
                col_start=pf.col_start,
                match_text=pf.match_text,
            )
        )

    for path in results.unused_assets:
        findings.append(
            Finding(
                rel_path=str(path),
                line_no=0,
                code="ASSET",
                severity="warning",
                message="File not referenced in any documentation page.",
            )
        )

    for msg in results.nav_contract_errors:
        findings.append(
            Finding(
                rel_path="(nav)",
                line_no=0,
                code="NAV",
                severity="error",
                message=msg,
            )
        )

    for report in results.reference_reports:
        rel = _rel(report.file_path)
        # Pre-load source lines for snippet context
        _lines: list[str] = []
        if report.file_path.is_file():
            try:
                _lines = report.file_path.read_text(encoding="utf-8").splitlines()
            except OSError:
                pass
        for ref_f in report.findings:
            src = ""
            if _lines and 0 < ref_f.line_no <= len(_lines):
                src = _lines[ref_f.line_no - 1].strip()
            findings.append(
                Finding(
                    rel_path=rel,
                    line_no=ref_f.line_no,
                    code=ref_f.issue,
                    severity="warning" if ref_f.is_warning else "error",
                    message=ref_f.detail,
                    source_line=src,
                )
            )
        for rule_f in report.rule_findings:
            findings.append(
                Finding(
                    rel_path=rel,
                    line_no=rule_f.line_no,
                    code=rule_f.rule_id,
                    severity=rule_f.severity,
                    message=rule_f.message,
                    source_line=rule_f.matched_line,
                    col_start=rule_f.col_start,
                    match_text=rule_f.match_text,
                )
            )
        # Convert Shield security findings into breach-severity Finding objects.
        # _map_shield_to_finding() is the sole authorised bridge between the Shield
        # and the reporter (see Obligation 4 / Mutation Gate in CONTRIBUTING.md).
        for sf in report.security_findings:
            findings.append(_map_shield_to_finding(sf, docs_root))

    return findings


# ── Target helpers (file or directory) ───────────────────────────────────────


def _resolve_target(repo_root: Path, config: ZenzicConfig, raw: str) -> Path:
    """Resolve *raw* to an existing file or directory.

    Search order: absolute as-is → relative to *repo_root* → relative to
    *repo_root/docs_dir*.  Files must have the ``.md`` extension.
    Exits with code 1 if nothing is found or the extension is wrong.
    """
    p = Path(raw)
    candidates: list[Path] = (
        [p] if p.is_absolute() else [repo_root / p, repo_root / config.docs_dir / p]
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
        if candidate.is_file():
            if candidate.suffix.lower() != ".md":
                console.print(
                    f"[red]ERROR:[/] [bold]{raw}[/] is not a Markdown file "
                    f"(expected .md, got '{candidate.suffix}')."
                )
                raise typer.Exit(1)
            return candidate.resolve()
    console.print(
        f"[red]ERROR:[/] Target not found: [bold]{raw}[/]\n"
        f"  Tried: {candidates[0]}" + (f", {candidates[1]}" if len(candidates) > 1 else "")
    )
    raise typer.Exit(1)


def _apply_target(
    repo_root: Path,
    config: ZenzicConfig,
    raw_path: str,
) -> tuple[ZenzicConfig, Path | None, Path, str]:
    """Resolve *raw_path* and return ``(patched_config, single_file, docs_root, hint)``.

    *single_file* is ``None`` in directory mode; the absolute ``.md`` path in
    file mode.  *hint* is a short display string for the Sentinel banner.

    **Directory mode** — ``config.docs_dir`` is patched to *target*; all
    checks scan that tree.  No post-hoc finding filter is applied.

    **File mode** — ``config.docs_dir`` is patched to *target.parent* when
    the file lives outside the configured docs dir.  The caller applies a
    post-hoc filter to the findings list using *single_file*.
    """
    target = _resolve_target(repo_root, config, raw_path)

    # ── display hint ─────────────────────────────────────────────────────────
    try:
        rel = target.relative_to(repo_root)
        hint = f"./{rel}" + ("/" if target.is_dir() else "")
    except ValueError:
        hint = str(target) + ("/" if target.is_dir() else "")

    # ── directory mode ────────────────────────────────────────────────────────
    if target.is_dir():
        try:
            new_docs_dir = target.relative_to(repo_root)
        except ValueError:
            new_docs_dir = target
        return config.model_copy(update={"docs_dir": new_docs_dir}), None, target, hint

    # ── file mode ─────────────────────────────────────────────────────────────
    default_docs_root = (repo_root / config.docs_dir).resolve()
    try:
        target.relative_to(default_docs_root)
        return config, target, default_docs_root, hint
    except ValueError:
        new_docs_dir = target.parent.relative_to(repo_root)
        patched = config.model_copy(update={"docs_dir": new_docs_dir})
        return patched, target, target.parent.resolve(), hint


@check_app.command(name="all")
def check_all(
    strict: bool | None = typer.Option(
        None, "--strict", "-s", help="Treat warnings as errors (exit non-zero on any warning)."
    ),
    output_format: str = typer.Option("text", "--format", help="Output format: text or json."),
    exit_zero: bool | None = typer.Option(
        None, "--exit-zero", help="Always exit 0; report issues without failing."
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
            "Limit audit to a single Markdown file or an entire directory. "
            "Accepts paths relative to the repo root or to the docs directory. "
            "File examples: README.md, docs/index.md. "
            "Directory examples: content/, docs/guide/. "
            "When a directory is given, docs_dir is patched to that path and all "
            "Markdown files inside it are audited."
        ),
        show_default=False,
    ),
    show_info: bool = typer.Option(
        False, "--show-info", help="Show info-level findings (e.g. circular links) in the report."
    ),
) -> None:
    """Run all checks: links, orphans, snippets, placeholders, assets, references.

    Optionally pass PATH to scope the audit to a single Markdown file or a custom
    directory (e.g. ``README.md``, ``content/``).  Zenzic auto-selects the
    VanillaAdapter when the target lives outside the configured docs directory.
    """
    repo_root = find_repo_root()
    config, loaded_from_file = ZenzicConfig.load(repo_root)
    if not loaded_from_file and not quiet:
        _print_no_config_hint()
    config = _apply_engine_override(config, engine)

    # ── Target mode (single file OR custom directory) ──────────────────────────
    _single_file: Path | None = None
    _target_hint: str | None = None
    if path is not None:
        config, _single_file, _, _target_hint = _apply_target(repo_root, config, path)

    docs_root = (repo_root / config.docs_dir).resolve()
    exclusion_mgr = _build_exclusion_manager(
        config,
        repo_root,
        docs_root,
        exclude_dirs=exclude_dir,
        include_dirs=include_dir,
    )

    effective_strict = strict if strict is not None else config.strict
    effective_exit_zero = exit_zero if exit_zero is not None else config.exit_zero

    t0 = time.monotonic()
    results = _collect_all_results(
        repo_root,
        docs_root,
        config,
        exclusion_mgr,
        strict=effective_strict,
    )
    elapsed = time.monotonic() - t0

    # ── JSON format ───────────────────────────────────────────────────────────
    if output_format == "json":
        ref_errors = []
        for r in results.reference_reports:
            for f in r.findings:
                if not f.is_warning:
                    try:
                        rel = r.file_path.relative_to(repo_root / config.docs_dir)
                    except ValueError:
                        rel = r.file_path
                    ref_errors.append(f"{rel}:{f.line_no} [{f.issue}] — {f.detail}")
        report = {
            "links": [str(e) for e in results.link_errors],
            "orphans": [str(p) for p in results.orphans],
            "snippets": [
                {"file": str(e.file_path), "line": e.line_no, "message": e.message}
                for e in results.snippet_errors
            ],
            "placeholders": [
                {"file": str(p.file_path), "line": p.line_no, "issue": p.issue, "detail": p.detail}
                for p in results.placeholders
            ],
            "unused_assets": [str(p) for p in results.unused_assets],
            "nav_contract": results.nav_contract_errors,
            "references": ref_errors,
        }
        print(json.dumps(report, indent=2))
        if results.failed and not effective_exit_zero:
            raise typer.Exit(1)
        return

    # ── Sentinel Report (text) ────────────────────────────────────────────────
    from zenzic import __version__

    all_findings = _to_findings(results, docs_root)

    # In single-file mode filter findings to the requested file only.
    if _single_file is not None:
        _sf_rel = str(_single_file.relative_to(docs_root))
        all_findings = [f for f in all_findings if f.rel_path == _sf_rel]

    reporter = SentinelReporter(console, docs_root, docs_dir=str(config.docs_dir))

    if quiet:
        errors, warnings = reporter.render_quiet(all_findings)
    else:
        docs_count, assets_count = _count_docs_assets(docs_root, repo_root, exclusion_mgr, config)
        # File-target mode: banner shows exactly 1 file.
        if _single_file is not None:
            docs_count, assets_count = 1, 0
        errors, warnings = reporter.render(
            all_findings,
            version=__version__,
            elapsed=elapsed,
            docs_count=docs_count,
            assets_count=assets_count,
            engine=config.build_context.engine if hasattr(config, "build_context") else "auto",
            target=_target_hint,
            strict=effective_strict,
            show_info=show_info,
        )

    # Security incidents (system-path traversal) cause Exit 3 — highest priority.
    # Exit 3 is NEVER suppressed by --exit-zero (documented contract).
    incidents = sum(1 for f in all_findings if f.severity == "security_incident")
    if incidents:
        raise typer.Exit(3)
    # Breach findings cause Exit 2; NEVER suppressed by --exit-zero.
    # This check runs after rendering so the report is always printed first.
    breaches = sum(1 for f in all_findings if f.severity == "security_breach")
    if breaches:
        raise typer.Exit(2)

    # In strict mode, warnings are promoted to failures.
    # Use reporter-derived counts (from filtered all_findings) so that target-mode
    # does not fail on findings outside the requested scope.
    has_failures = (errors > 0) or (effective_strict and warnings > 0)

    if has_failures:
        if not effective_exit_zero:
            raise typer.Exit(1)


@plugins_app.command(name="list")
def plugins_list() -> None:
    """List all rules registered in the ``zenzic.rules`` entry-point group.

    Shows Core rules (bundled with Zenzic) and any third-party plugin rules
    discovered from installed packages.  Each row includes:

    * **Source** — entry-point name (e.g. ``broken-links``).
    * **Rule ID** — stable identifier emitted in findings (e.g. ``Z001``).
    * **Origin** — distribution that registered the rule.
    * **Class** — fully qualified Python class name.
    """
    from zenzic.core.rules import list_plugin_rules

    rules = list_plugin_rules()
    if not rules:
        console.print("[yellow]No rules found in the 'zenzic.rules' entry-point group.[/]")
        console.print(
            "[dim]Install a plugin package or check that Zenzic is installed correctly.[/]"
        )
        return

    console.print(f"\n[bold]Installed plugin rules[/] ({len(rules)} found)\n")
    for info in rules:
        origin_badge = (
            "[dim cyan](core)[/]" if info.origin == "zenzic" else f"[dim green]({info.origin})[/]"
        )
        console.print(
            f"  [bold cyan]{info.source}[/]  "
            f"[bold]{info.rule_id}[/]  "
            f"{origin_badge}  "
            f"[dim]{info.class_name}[/]"
        )
    console.print()


def _run_all_checks(
    repo_root: Path,
    docs_root: Path,
    config: ZenzicConfig,
    exclusion_mgr: LayeredExclusionManager,
    strict: bool,
) -> ScoreReport:
    """Run all five checks and return a ScoreReport. Used by score and diff."""
    link_errors = validate_links(
        docs_root,
        exclusion_mgr,
        repo_root=repo_root,
        config=config,
        strict=strict,
    )
    orphans = find_orphans(docs_root, exclusion_mgr, repo_root=repo_root, config=config)
    snippet_errors = validate_snippets(docs_root, exclusion_mgr, config=config)
    placeholders = find_placeholders(docs_root, exclusion_mgr, config=config)
    unused_assets = find_unused_assets(docs_root, exclusion_mgr, config=config)

    return compute_score(
        link_errors=len(link_errors),
        orphans=len(orphans),
        snippet_errors=len(snippet_errors),
        placeholders=len(placeholders),
        unused_assets=len(unused_assets),
    )


def score(
    strict: bool | None = typer.Option(
        None,
        "--strict",
        "-s",
        help="Also validate external HTTP/HTTPS links (slower; requires network).",
    ),
    output_format: str = typer.Option("text", "--format", help="Output format: text or json."),
    save: bool = typer.Option(False, "--save", help="Save score snapshot to .zenzic-score.json."),
    fail_under: int = typer.Option(
        0, "--fail-under", help="Exit non-zero if score is below this threshold (0 = disabled)."
    ),
) -> None:
    """Compute a 0–100 documentation quality score across all checks."""
    repo_root = find_repo_root()
    config, _ = ZenzicConfig.load(repo_root)
    docs_root = (repo_root / config.docs_dir).resolve()
    exclusion_mgr = _build_exclusion_manager(config, repo_root, docs_root)
    effective_strict = strict if strict is not None else config.strict
    report = _run_all_checks(repo_root, docs_root, config, exclusion_mgr, strict=effective_strict)

    # CLI flag takes precedence; fall back to zenzic.toml; 0 means disabled.
    effective_threshold = fail_under if fail_under > 0 else config.fail_under

    if save:
        report.threshold = effective_threshold
        snapshot_path = save_snapshot(repo_root, report)
        console.print(f"[dim]Snapshot saved to {snapshot_path}[/]")

    if output_format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        # ── Sentinel Score Display ────────────────────────────────────────
        if report.score >= 80:
            score_style, score_icon = f"bold {INDIGO}", emoji("check")
        elif report.score >= 50:
            score_style, score_icon = "bold yellow", emoji("warn")
        else:
            score_style, score_icon = "bold red", emoji("cross")

        score_text = Text()
        score_text.append(f" {score_icon} ", style="bold")
        score_text.append(f" {report.score}", style=score_style)
        score_text.append("/100 ", style="dim")

        console.print()
        console.print(
            Panel(
                score_text,
                title="[bold]Zenzic Quality Score[/]",
                title_align="left",
                border_style=INDIGO,
                expand=False,
                padding=(0, 2),
            )
        )
        console.print()

        table = Table(
            box=box.ROUNDED,
            title="[bold]Quality Breakdown[/]",
            title_style=SLATE,
            border_style=SLATE,
            show_lines=False,
            pad_edge=True,
            padding=(0, 1),
        )
        table.add_column(emoji("dot"), justify="center", width=4, no_wrap=True)
        table.add_column("Category", min_width=14, style="bold")
        table.add_column("Issues", justify="right")
        table.add_column("Weight", justify="right", style="dim")
        table.add_column("Score", justify="right", style="dim")

        for cat in report.categories:
            if cat.issues == 0:
                status_icon = f"[green]{emoji('check')}[/]"
                issue_display = f"[green]{cat.issues}[/]"
            else:
                status_icon = f"[red]{emoji('cross')}[/]"
                issue_display = f"[red]{cat.issues}[/]"
            table.add_row(
                status_icon,
                cat.name,
                issue_display,
                f"{cat.weight:.0%}",
                f"{cat.contribution:.2f}",
            )

        console.print(table)

    if effective_threshold > 0 and report.score < effective_threshold:
        console.print(
            f"\n[red]FAILED:[/] score {report.score} is below threshold {effective_threshold}."
        )
        raise typer.Exit(1)


def diff(
    strict: bool | None = typer.Option(
        None,
        "--strict",
        "-s",
        help="Also validate external HTTP/HTTPS links (slower; requires network).",
    ),
    output_format: str = typer.Option("text", "--format", help="Output format: text or json."),
    threshold: int = typer.Option(
        0,
        "--threshold",
        help="Exit non-zero only if score dropped by more than this many points (0 = any drop).",
    ),
) -> None:
    """Compare current documentation score against the saved snapshot.

    Requires a previous snapshot created by ``zenzic score --save``.
    Exits non-zero if the score dropped by more than ``--threshold`` points.
    """
    repo_root = find_repo_root()
    config, _ = ZenzicConfig.load(repo_root)
    docs_root = (repo_root / config.docs_dir).resolve()
    exclusion_mgr = _build_exclusion_manager(config, repo_root, docs_root)
    effective_strict = strict if strict is not None else config.strict

    baseline = load_snapshot(repo_root)
    if baseline is None:
        console.print(
            "[yellow]WARNING:[/] no snapshot found. "
            "Run 'zenzic score --save' first to establish a baseline."
        )
        raise typer.Exit(1)

    current = _run_all_checks(repo_root, docs_root, config, exclusion_mgr, strict=effective_strict)
    delta = current.score - baseline.score

    if output_format == "json":
        print(
            json.dumps(
                {
                    "baseline": baseline.score,
                    "current": current.score,
                    "delta": delta,
                    "categories": [
                        {
                            "name": cat.name,
                            "baseline_issues": next(
                                (b.issues for b in baseline.categories if b.name == cat.name),
                                None,
                            ),
                            "current_issues": cat.issues,
                        }
                        for cat in current.categories
                    ],
                },
                indent=2,
            )
        )
    else:
        console.print(f"\nBaseline: [bold]{baseline.score}/100[/]")
        console.print(f"Current:  [bold]{current.score}/100[/]")
        delta_colour = "green" if delta >= 0 else "red"
        sign = "+" if delta >= 0 else ""
        console.print(f"Delta:    [{delta_colour}]{sign}{delta}[/]")
        console.print("")
        for cat in current.categories:
            base_cat = next((b for b in baseline.categories if b.name == cat.name), None)
            base_issues = base_cat.issues if base_cat else 0
            issue_delta = cat.issues - base_issues
            sign_i = "+" if issue_delta > 0 else ""
            colour = "red" if issue_delta > 0 else "green" if issue_delta < 0 else "dim"
            console.print(
                f"  {cat.name:<14} baseline {base_issues:>3}  current {cat.issues:>3}  "
                f"[{colour}]{sign_i}{issue_delta}[/]"
            )

    dropped = -delta  # positive means score went down
    if dropped > threshold:
        console.print(
            f"\n[red]REGRESSION:[/] score dropped by {dropped} point(s) (threshold: {threshold})."
        )
        raise typer.Exit(1)


def init(
    plugin: str | None = typer.Option(
        None,
        "--plugin",
        help="Generate a starter Python package for a Zenzic plugin rule.",
        metavar="NAME",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite an existing zenzic.toml without prompting.",
    ),
    pyproject: bool = typer.Option(
        False,
        "--pyproject",
        help="Write configuration into pyproject.toml [tool.zenzic] instead of zenzic.toml.",
    ),
) -> None:
    """Scaffold a Zenzic configuration in the current project.

    By default creates ``zenzic.toml``.  If ``pyproject.toml`` exists in the
    project root Zenzic will ask whether to embed the configuration there
    as a ``[tool.zenzic]`` table instead.  Use ``--pyproject`` to skip the
    prompt and write directly into ``pyproject.toml``.

    Performs engine auto-detection: if ``mkdocs.yml`` is present the generated
    file pre-sets ``engine = "mkdocs"``; if ``zensical.toml`` is present it
    pre-sets ``engine = "zensical"``.  Otherwise the ``[build_context]`` block
    is omitted and the vanilla (engine-agnostic) defaults apply.
    """
    repo_root = find_repo_root(fallback_to_cwd=True)

    if plugin is not None:
        _scaffold_plugin(repo_root, plugin, force)
        return

    # ── Decide target: zenzic.toml vs pyproject.toml ──────────────────────
    use_pyproject = pyproject
    pyproject_path = repo_root / "pyproject.toml"

    if not use_pyproject and pyproject_path.is_file():
        # Interactive prompt — ask the user
        use_pyproject = typer.confirm(
            "Found pyproject.toml. Embed Zenzic config there as [tool.zenzic]?",
            default=False,
        )

    if use_pyproject:
        _init_pyproject(repo_root, pyproject_path, force)
    else:
        _init_standalone(repo_root, force)


def _detect_init_engine(repo_root: Path) -> str | None:
    """Auto-detect the documentation engine from config files at *repo_root*."""
    if (repo_root / "mkdocs.yml").is_file():
        return "mkdocs"
    if (repo_root / "zensical.toml").is_file():
        return "zensical"
    return None


def _engine_feedback(detected_engine: str | None) -> str:
    """Return a Rich-formatted engine status line for init output."""
    if detected_engine:
        source = "mkdocs.yml" if detected_engine == "mkdocs" else "zensical.toml"
        return f"  Engine pre-set to [bold cyan]{detected_engine}[/] (detected from {source}).\n"
    return "  No engine config file found — using vanilla (engine-agnostic) defaults.\n"


def _init_standalone(repo_root: Path, force: bool) -> None:
    """Create a standalone ``zenzic.toml`` configuration file."""
    config_path = repo_root / "zenzic.toml"

    if config_path.is_file() and not force:
        console.print(
            f"[yellow]WARNING:[/] [bold]zenzic.toml[/] already exists at "
            f"[dim]{config_path}[/]\n"
            "Use [bold cyan]--force[/] to overwrite."
        )
        raise typer.Exit(1)

    detected_engine = _detect_init_engine(repo_root)

    build_context_block = ""
    if detected_engine:
        build_context_block = f'\n[build_context]\nengine = "{detected_engine}"\n'

    toml_content = (
        "# zenzic.toml — project configuration for Zenzic\n"
        "# See https://zenzic.pythonwoods.dev/configuration/ for full reference.\n"
        "\n"
        '# docs_dir = "docs"   # default: docs\n'
        "\n"
        "# Directories to skip during checks (relative to docs_dir).\n"
        "# excluded_check_dirs = []\n"
        "\n"
        "# Minimum quality score required to pass (0 = disabled).\n"
        "# fail_under = 0\n" + build_context_block + "\n"
        "# Zenzic Shield — built-in credential scanner (always active, no config required).\n"
        "# Detected pattern families: openai-api-key, github-token, aws-access-key,\n"
        "#   stripe-live-key, slack-token, google-api-key, private-key,\n"
        "#   hex-encoded-payload (3+ consecutive \\xNN sequences).\n"
        "# All lines including fenced code blocks are scanned. Exit code 2 on detection.\n"
        "\n"
        "# Declare project-specific lint rules (no Python required):\n"
        "# [[custom_rules]]\n"
        '# id       = "ZZ-NODRAFT"\n'
        '# pattern  = "(?i)\\\\bDRAFT\\\\b"\n'
        '# message  = "Remove DRAFT marker before publishing."\n'
        '# severity = "warning"\n'
    )

    config_path.write_text(toml_content, encoding="utf-8")

    console.print(
        f"\n[green]Created[/] [bold]{config_path.relative_to(repo_root)}[/]\n"
        + _engine_feedback(detected_engine)
        + "\nEdit the file to enable rules, adjust directories, or set a quality threshold.\n"
        "Run [bold cyan]zenzic check all[/] to validate your documentation."
    )


def _init_pyproject(repo_root: Path, pyproject_path: Path, force: bool) -> None:
    """Append a ``[tool.zenzic]`` section to an existing ``pyproject.toml``."""
    if not pyproject_path.is_file():
        console.print(
            "[red]ERROR:[/] No [bold]pyproject.toml[/] found at "
            f"[dim]{pyproject_path}[/]\n"
            "Use [bold cyan]zenzic init[/] without --pyproject to create a standalone zenzic.toml."
        )
        raise typer.Exit(1)

    existing = pyproject_path.read_text(encoding="utf-8")

    if "[tool.zenzic]" in existing and not force:
        console.print(
            "[yellow]WARNING:[/] [bold][tool.zenzic][/] already exists in "
            f"[dim]{pyproject_path}[/]\n"
            "Use [bold cyan]--force[/] to overwrite the section."
        )
        raise typer.Exit(1)

    detected_engine = _detect_init_engine(repo_root)

    engine_line = ""
    if detected_engine:
        engine_line = f'engine = "{detected_engine}"\n'

    section = (
        "\n[tool.zenzic]\n"
        "# See https://zenzic.pythonwoods.dev/configuration/ for full reference.\n"
        '# docs_dir = "docs"\n'
        "# excluded_check_dirs = []\n"
        "# fail_under = 0\n"
    )
    if engine_line:
        section += f"\n[tool.zenzic.build_context]\n{engine_line}"

    if force and "[tool.zenzic]" in existing:
        # Remove existing [tool.zenzic] block(s) before re-appending
        existing = re.sub(
            r"\n?\[tool\.zenzic[^\]]*\][^\[]*",
            "",
            existing,
        )

    pyproject_path.write_text(existing.rstrip("\n") + "\n" + section, encoding="utf-8")

    console.print(
        f"\n[green]Added[/] [bold][tool.zenzic][/] to [bold]{pyproject_path.relative_to(repo_root)}[/]\n"
        + _engine_feedback(detected_engine)
        + "\nEdit the section to enable rules, adjust directories, or set a quality threshold.\n"
        "Run [bold cyan]zenzic check all[/] to validate your documentation."
    )


def _scaffold_plugin(repo_root: Path, plugin_name: str, force: bool) -> None:
    """Create a ready-to-edit plugin package scaffold.

    Generates a Python package with a `zenzic.rules` entry-point and a
    module-level `BaseRule` implementation template.
    """
    raw = plugin_name.strip()
    if not raw:
        console.print("[red]ERROR:[/] --plugin requires a non-empty name.")
        raise typer.Exit(1)

    project_slug = re.sub(r"[^a-z0-9-]+", "-", raw.lower()).strip("-")
    project_slug = re.sub(r"-+", "-", project_slug)
    if not project_slug:
        console.print(
            "[red]ERROR:[/] Invalid plugin name. Use letters, numbers, and optional dashes."
        )
        raise typer.Exit(1)

    module_name = project_slug.replace("-", "_")
    class_name = "".join(part.capitalize() for part in project_slug.split("-")) + "Rule"
    rule_prefix = "".join(ch for ch in project_slug.upper() if ch.isalnum())[:8] or "PLUGIN"
    rule_id = f"{rule_prefix}-001"

    target = repo_root / project_slug
    if target.exists() and not force:
        console.print(
            f"[yellow]WARNING:[/] [bold]{project_slug}[/] already exists at "
            f"[dim]{target}[/]\nUse [bold cyan]--force[/] to overwrite scaffold files."
        )
        raise typer.Exit(1)

    src_pkg = target / "src" / module_name
    docs_dir = target / "docs"
    src_pkg.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    pyproject = f'''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{project_slug}"
version = "0.1.0"
description = "Custom Zenzic plugin rule package"
readme = "README.md"
requires-python = ">=3.11"
dependencies = ["zenzic>=0.5.0a3"]

[project.entry-points."zenzic.rules"]
{project_slug} = "{module_name}.rules:{class_name}"

[tool.hatch.build.targets.wheel]
packages = ["src/{module_name}"]
'''

    rules_py = f'''from __future__ import annotations

from pathlib import Path

from zenzic.rules import BaseRule, RuleFinding


class {class_name}(BaseRule):
    """Starter plugin rule generated by `zenzic init --plugin`."""

    @property
    def rule_id(self) -> str:
        return "{rule_id}"

    def check(self, file_path: Path, text: str) -> list[RuleFinding]:
        findings: list[RuleFinding] = []
        for lineno, line in enumerate(text.splitlines(), start=1):
            if "TODO" in line:
                findings.append(
                    RuleFinding(
                        file_path=file_path,
                        line_no=lineno,
                        rule_id=self.rule_id,
                        message="Remove TODO marker from published documentation.",
                        severity="warning",
                        matched_line=line,
                    )
                )
        return findings
'''

    readme = f'''# {project_slug}

Plugin scaffold generated by `zenzic init --plugin {project_slug}`.

## Quick start

```bash
uv sync
uv pip install -e .
zenzic plugins list
```

Enable this plugin in a target project's `zenzic.toml`:

```toml
plugins = ["{project_slug}"]
```
'''

    docs_index = (
        "# Plugin Scaffold Demo\n\n"
        "This scaffold includes a clean documentation page so `zenzic check all` passes out "
        "of the box. The content is intentionally longer than fifty words to satisfy the "
        "placeholder minimum-word rule, while remaining simple enough for quick editing "
        "during local plugin development and CI verification workflows.\n"
    )

    (target / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    (target / "README.md").write_text(readme, encoding="utf-8")
    (target / "zenzic.toml").write_text(
        '# zenzic.toml generated by plugin scaffold\n# docs_dir defaults to "docs"\n',
        encoding="utf-8",
    )
    (src_pkg / "__init__.py").write_text(
        f'"""{project_slug} plugin package."""\n',
        encoding="utf-8",
    )
    (src_pkg / "rules.py").write_text(rules_py, encoding="utf-8")
    (docs_dir / "index.md").write_text(docs_index, encoding="utf-8")

    console.print(
        f"\n[green]Created plugin scaffold[/] [bold]{project_slug}[/]\n"
        f"  Path: [dim]{target.relative_to(repo_root)}[/]\n"
        f"  Entry-point: [bold]{project_slug}[/] -> [dim]{module_name}.rules:{class_name}[/]\n"
        "\nNext steps:\n"
        f"  1. [bold]cd {project_slug}[/]\n"
        "  2. [bold]uv pip install -e .[/]\n"
        "  3. [bold]zenzic plugins list[/]"
    )
