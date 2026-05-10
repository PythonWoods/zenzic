# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Check sub-commands: links, orphans, snippets, references, assets, placeholders, all."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path

import typer

from zenzic.core.discovery import iter_markdown_sources
from zenzic.core.exclusion import LayeredExclusionManager
from zenzic.core.reporter import Finding, SentinelReporter
from zenzic.core.rules import count_inline_suppressions
from zenzic.core.scanner import (
    I18nParityIssue,
    PlaceholderFinding,
    _map_shield_to_finding,
    find_i18n_parity,
    find_missing_directory_indices,
    find_orphans,
    find_placeholders,
    find_repo_root,
    find_unused_assets,
    scan_docs_references,
)
from zenzic.core.ui import SentinelPalette
from zenzic.core.validator import (
    LinkError,
    SnippetError,
    check_nav_contract,
    validate_links_structured,
    validate_snippets,
)
from zenzic.models.config import ZenzicConfig
from zenzic.models.references import IntegrityReport

from . import _shared


check_app = typer.Typer(
    name="check",
    help=f"[bold {SentinelPalette.BRAND}]Check[/] — Run documentation quality checks.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


# ── Check commands ────────────────────────────────────────────────────────────


@check_app.command(name="links")
def check_links(
    strict: bool = typer.Option(False, "--strict", "-s", help="Exit non-zero on any warning."),
    output_format: str = typer.Option(
        "text", "--format", "-f", help="Output format: text, json, or sarif."
    ),
    show_info: bool = typer.Option(
        False, "--show-info", help="Show info-level findings (e.g. circular links) in the report."
    ),
    offline: bool = typer.Option(
        False, "--offline", help="Force flat URL resolution for offline builds."
    ),
    no_external: bool = typer.Option(
        False,
        "--no-external",
        help=(
            "Skip HTTP validation of external URLs (Pass 3). "
            "For air-gapped / offline environments. "
            "Shield (Z201) always active regardless of this flag."
        ),
    ),
    exclude_url: list[str] = typer.Option(
        [],
        "--exclude-url",
        help=(
            "Bypass external URL validation for URLs matching this prefix (repeatable). "
            "Merged with excluded_external_urls from zenzic.toml at runtime."
        ),
        metavar="PREFIX",
    ),
    path: str | None = typer.Argument(
        None,
        help="Limit to a directory or file. Accepts paths relative to repo root or docs dir.",
        show_default=False,
    ),
) -> None:
    """Check for broken internal links. Pass --strict to also validate external URLs."""
    from zenzic import __version__

    _search_from: Path | None = None
    if path is not None:
        _pre = Path(path).resolve()
        _search_from = _pre.parent if _pre.is_file() else _pre
    repo_root = find_repo_root(search_from=_search_from)
    config, _ = ZenzicConfig.load(repo_root)
    if offline:
        config.build_context.offline_mode = True
    if exclude_url:
        config = config.model_copy(
            update={"excluded_external_urls": config.excluded_external_urls + list(exclude_url)}
        )
    if path is not None:
        config, _, docs_root, _ = _apply_target(repo_root, config, path)
        try:
            docs_root.relative_to(repo_root)
        except ValueError:
            repo_root = docs_root
    else:
        docs_root = (repo_root / config.docs_dir).resolve()
    exclusion_mgr = _shared._build_exclusion_manager(config, repo_root, docs_root)

    def _rel(path: Path) -> str:
        try:
            return str(path.relative_to(docs_root))
        except ValueError:
            return str(path)

    t0 = time.monotonic()
    from zenzic.core.adapters import get_adapter

    adapter = get_adapter(config.build_context, docs_root, repo_root)
    locale_roots: list[tuple[Path, str]] | None = None
    if hasattr(adapter, "get_locale_source_roots"):
        _roots = adapter.get_locale_source_roots(repo_root)
        locale_roots = _roots if _roots else None

    link_errors = validate_links_structured(
        docs_root,
        exclusion_mgr,
        repo_root=repo_root,
        config=config,
        strict=strict,
        locale_roots=locale_roots,
        check_external=not no_external,
    )
    elapsed = time.monotonic() - t0

    findings = [
        Finding(
            rel_path=_rel(err.file_path),
            line_no=err.line_no,
            code=err.code,
            severity=(
                "security_incident"
                if err.code == "Z203"
                else "info"
                if err.code == "Z106"
                else "error"
            ),
            message=err.message,
            source_line=err.source_line,
            col_start=err.col_start,
            match_text=err.match_text,
        )
        for err in link_errors
    ]

    if output_format == "json":
        _shared._output_json_findings(findings, elapsed)
        incidents = sum(1 for f in findings if f.severity == "security_incident")
        if incidents:
            raise typer.Exit(3)
        errors_count = sum(1 for f in findings if f.severity == "error")
        if errors_count:
            raise typer.Exit(1)
        return
    elif output_format == "sarif":
        _shared._output_sarif_findings(findings, __version__)
        incidents = sum(1 for f in findings if f.severity == "security_incident")
        if incidents:
            raise typer.Exit(3)
        errors_count = sum(1 for f in findings if f.severity == "error")
        if errors_count:
            raise typer.Exit(1)
        return

    docs_count, assets_count = _shared._count_docs_assets(docs_root, repo_root, exclusion_mgr)
    _shared._ui.print_header(__version__)
    if path is not None:
        try:
            _hint = str(docs_root.relative_to(Path.cwd()))
        except ValueError:
            _hint = str(docs_root)
        _shared.console.print(f"[dim]  Scanning: {_hint}[/]\n")
    reporter = SentinelReporter(_shared.console, docs_root, docs_dir=str(config.docs_dir))
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
    if no_external and output_format == "text":
        _shared.console.print(
            "[dim] 💡 External link validation skipped (--no-external). "
            "Shield (Z201) remains active.[/dim]\n"
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
    output_format: str = typer.Option(
        "text", "--format", "-f", help="Output format: text, json, or sarif."
    ),
    show_info: bool = typer.Option(
        False, "--show-info", help="Show info-level findings (e.g. circular links) in the report."
    ),
    offline: bool = typer.Option(
        False, "--offline", help="Force flat URL resolution for offline builds."
    ),
    path: str | None = typer.Argument(
        None,
        help="Limit to a directory or file. Accepts paths relative to repo root or docs dir.",
        show_default=False,
    ),
) -> None:
    """Detect .md files not listed in the nav."""
    from zenzic import __version__

    _search_from: Path | None = None
    if path is not None:
        _pre = Path(path).resolve()
        _search_from = _pre.parent if _pre.is_file() else _pre
    repo_root = find_repo_root(search_from=_search_from)
    config, loaded_from_file = ZenzicConfig.load(repo_root)
    if not loaded_from_file:
        _shared._print_no_config_hint(output_format)
    config = _shared._apply_engine_override(config, engine)
    if offline:
        config.build_context.offline_mode = True
    if path is not None:
        config, _, docs_root, _ = _apply_target(repo_root, config, path)
        try:
            docs_root.relative_to(repo_root)
        except ValueError:
            repo_root = docs_root
    else:
        docs_root = (repo_root / config.docs_dir).resolve()
    exclusion_mgr = _shared._build_exclusion_manager(config, repo_root, docs_root)

    t0 = time.monotonic()
    orphans = find_orphans(docs_root, exclusion_mgr, repo_root=repo_root, config=config)
    elapsed = time.monotonic() - t0

    findings = [
        Finding(
            rel_path=str(path),
            line_no=0,
            code="Z402",
            severity="warning",
            message="Physical file not listed in navigation.",
        )
        for path in orphans
    ]

    if output_format == "json":
        _shared._output_json_findings(findings, elapsed)
        errors_count = sum(1 for f in findings if f.severity == "error")
        if errors_count:
            raise typer.Exit(1)
        return
    elif output_format == "sarif":
        _shared._output_sarif_findings(findings, __version__)
        errors_count = sum(1 for f in findings if f.severity == "error")
        if errors_count:
            raise typer.Exit(1)
        return

    docs_count, assets_count = _shared._count_docs_assets(docs_root, repo_root, exclusion_mgr)
    _shared._ui.print_header(__version__)
    if path is not None:
        try:
            _hint = str(docs_root.relative_to(Path.cwd()))
        except ValueError:
            _hint = str(docs_root)
        _shared.console.print(f"[dim]  Scanning: {_hint}[/]\n")
    reporter = SentinelReporter(_shared.console, docs_root, docs_dir=str(config.docs_dir))
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
    output_format: str = typer.Option(
        "text", "--format", "-f", help="Output format: text, json, or sarif."
    ),
    show_info: bool = typer.Option(
        False, "--show-info", help="Show info-level findings (e.g. circular links) in the report."
    ),
    path: str | None = typer.Argument(
        None,
        help="Limit to a directory or file. Accepts paths relative to repo root or docs dir.",
        show_default=False,
    ),
) -> None:
    """Validate Python code blocks in documentation Markdown files."""
    from zenzic import __version__

    _search_from: Path | None = None
    if path is not None:
        _pre = Path(path).resolve()
        _search_from = _pre.parent if _pre.is_file() else _pre
    repo_root = find_repo_root(search_from=_search_from)
    config, loaded_from_file = ZenzicConfig.load(repo_root)
    if not loaded_from_file:
        _shared._print_no_config_hint(output_format)
    if path is not None:
        config, _, docs_root, _ = _apply_target(repo_root, config, path)
        try:
            docs_root.relative_to(repo_root)
        except ValueError:
            repo_root = docs_root
    else:
        docs_root = (repo_root / config.docs_dir).resolve()
    exclusion_mgr = _shared._build_exclusion_manager(config, repo_root, docs_root)

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
                code="Z503",
                severity="error",
                message=s_err.message,
                source_line=src,
            )
        )

    if output_format == "json":
        _shared._output_json_findings(findings, elapsed)
        errors_count = sum(1 for f in findings if f.severity == "error")
        if errors_count:
            raise typer.Exit(1)
        return
    elif output_format == "sarif":
        _shared._output_sarif_findings(findings, __version__)
        errors_count = sum(1 for f in findings if f.severity == "error")
        if errors_count:
            raise typer.Exit(1)
        return

    docs_count, assets_count = _shared._count_docs_assets(docs_root, repo_root, exclusion_mgr)
    _shared._ui.print_header(__version__)
    if path is not None:
        try:
            _hint = str(docs_root.relative_to(Path.cwd()))
        except ValueError:
            _hint = str(docs_root)
        _shared.console.print(f"[dim]  Scanning: {_hint}[/]\n")
    reporter = SentinelReporter(_shared.console, docs_root, docs_dir=str(config.docs_dir))
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
    output_format: str = typer.Option(
        "text", "--format", "-f", help="Output format: text, json, or sarif."
    ),
    show_info: bool = typer.Option(
        False, "--show-info", help="Show info-level findings (e.g. circular links) in the report."
    ),
    path: str | None = typer.Argument(
        None,
        help="Limit to a directory or file. Accepts paths relative to repo root or docs dir.",
        show_default=False,
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

    _search_from: Path | None = None
    if path is not None:
        _pre = Path(path).resolve()
        _search_from = _pre.parent if _pre.is_file() else _pre
    repo_root = find_repo_root(search_from=_search_from)
    config, loaded_from_file = ZenzicConfig.load(repo_root)
    if not loaded_from_file:
        _shared._print_no_config_hint(output_format)
    if path is not None:
        config, _, docs_root, _ = _apply_target(repo_root, config, path)
        try:
            docs_root.relative_to(repo_root)
        except ValueError:
            repo_root = docs_root
    else:
        docs_root = (repo_root / config.docs_dir).resolve()
    exclusion_mgr = _shared._build_exclusion_manager(config, repo_root, docs_root)

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
                code="Z101",
                severity="error",
                message=err_str,
            )
        )

    if output_format == "json":
        _shared._output_json_findings(findings, elapsed)
        breaches = sum(1 for f in findings if f.severity == "security_breach")
        if breaches:
            raise typer.Exit(2)
        errors_count = sum(1 for f in findings if f.severity == "error")
        warnings_count = sum(1 for f in findings if f.severity == "warning")
        if errors_count or (strict and warnings_count):
            raise typer.Exit(1)
        return
    elif output_format == "sarif":
        _shared._output_sarif_findings(findings, __version__)
        breaches = sum(1 for f in findings if f.severity == "security_breach")
        if breaches:
            raise typer.Exit(2)
        errors_count = sum(1 for f in findings if f.severity == "error")
        warnings_count = sum(1 for f in findings if f.severity == "warning")
        if errors_count or (strict and warnings_count):
            raise typer.Exit(1)
        return

    docs_count, assets_count = _shared._count_docs_assets(docs_root, repo_root, exclusion_mgr)
    _shared._ui.print_header(__version__)
    if path is not None:
        try:
            _hint = str(docs_root.relative_to(Path.cwd()))
        except ValueError:
            _hint = str(docs_root)
        _shared.console.print(f"[dim]  Scanning: {_hint}[/]\n")
    reporter = SentinelReporter(_shared.console, docs_root, docs_dir=str(config.docs_dir))
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
    output_format: str = typer.Option(
        "text", "--format", "-f", help="Output format: text, json, or sarif."
    ),
    show_info: bool = typer.Option(
        False, "--show-info", help="Show info-level findings (e.g. circular links) in the report."
    ),
    path: str | None = typer.Argument(
        None,
        help="Limit to a directory or file. Accepts paths relative to repo root or docs dir.",
        show_default=False,
    ),
) -> None:
    """Detect unused images and assets in the documentation."""
    from zenzic import __version__

    _search_from: Path | None = None
    if path is not None:
        _pre = Path(path).resolve()
        _search_from = _pre.parent if _pre.is_file() else _pre
    repo_root = find_repo_root(search_from=_search_from)
    config, loaded_from_file = ZenzicConfig.load(repo_root)
    if not loaded_from_file:
        _shared._print_no_config_hint(output_format)
    if path is not None:
        config, _, docs_root, _ = _apply_target(repo_root, config, path)
        try:
            docs_root.relative_to(repo_root)
        except ValueError:
            repo_root = docs_root
    else:
        docs_root = (repo_root / config.docs_dir).resolve()
    from zenzic.core.adapters import get_adapter

    adapter = get_adapter(config.build_context, docs_root, repo_root)
    adapter_meta = adapter.get_metadata_files()
    exclusion_mgr = _shared._build_exclusion_manager(
        config, repo_root, docs_root, adapter_metadata_files=adapter_meta
    )

    t0 = time.monotonic()
    unused = find_unused_assets(
        docs_root, exclusion_mgr, config=config, adapter_metadata_files=adapter_meta
    )
    elapsed = time.monotonic() - t0

    findings = [
        Finding(
            rel_path=str(path),
            line_no=0,
            code="Z405",
            severity="warning",
            message="File not referenced in any documentation page.",
        )
        for path in unused
    ]

    if output_format == "json":
        _shared._output_json_findings(findings, elapsed)
        errors_count = sum(1 for f in findings if f.severity == "error")
        if errors_count:
            raise typer.Exit(1)
        return
    elif output_format == "sarif":
        _shared._output_sarif_findings(findings, __version__)
        errors_count = sum(1 for f in findings if f.severity == "error")
        if errors_count:
            raise typer.Exit(1)
        return

    docs_count, assets_count = _shared._count_docs_assets(docs_root, repo_root, exclusion_mgr)
    _shared._ui.print_header(__version__)
    if path is not None:
        try:
            _hint = str(docs_root.relative_to(Path.cwd()))
        except ValueError:
            _hint = str(docs_root)
        _shared.console.print(f"[dim]  Scanning: {_hint}[/]\n")
    reporter = SentinelReporter(_shared.console, docs_root, docs_dir=str(config.docs_dir))
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


@check_app.command(name="placeholders")
def check_placeholders(
    show_info: bool = typer.Option(
        False, "--show-info", help="Show info-level findings (e.g. circular links) in the report."
    ),
    path: str | None = typer.Argument(
        None,
        help="Limit to a directory or file. Accepts paths relative to repo root or docs dir.",
        show_default=False,
    ),
) -> None:
    """Detect pages with < 50 words or containing TODOs/stubs."""
    from zenzic import __version__

    _search_from: Path | None = None
    if path is not None:
        _pre = Path(path).resolve()
        _search_from = _pre.parent if _pre.is_file() else _pre
    repo_root = find_repo_root(search_from=_search_from)
    config, loaded_from_file = ZenzicConfig.load(repo_root)
    if not loaded_from_file:
        _shared._print_no_config_hint()
    if path is not None:
        config, _, docs_root, _ = _apply_target(repo_root, config, path)
        try:
            docs_root.relative_to(repo_root)
        except ValueError:
            repo_root = docs_root
    else:
        docs_root = (repo_root / config.docs_dir).resolve()
    exclusion_mgr = _shared._build_exclusion_manager(config, repo_root, docs_root)

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

    docs_count, assets_count = _shared._count_docs_assets(docs_root, repo_root, exclusion_mgr)
    _shared._ui.print_header(__version__)
    if path is not None:
        try:
            _hint = str(docs_root.relative_to(Path.cwd()))
        except ValueError:
            _hint = str(docs_root)
        _shared.console.print(f"[dim]  Scanning: {_hint}[/]\n")
    reporter = SentinelReporter(_shared.console, docs_root, docs_dir=str(config.docs_dir))
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


# ── All-checks aggregate ──────────────────────────────────────────────────────


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
    directory_index_issues: list[Path]
    config_asset_issues: list[tuple[str, str]] = field(default_factory=list)
    i18n_parity_issues: list[I18nParityIssue] = field(default_factory=list)
    i18n_strict: bool = True

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
            or self.i18n_parity_issues
        )


@dataclass(frozen=True)
class _SuppressionAudit:
    inline_count: int
    per_file_count: int
    cap: int
    inline_hotspots: dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return self.inline_count + self.per_file_count

    @property
    def excess(self) -> int:
        return max(0, self.total - self.cap)

    @property
    def extended_debt(self) -> bool:
        return self.cap > 30

    def top_offenders(self, *, limit: int = 5) -> list[tuple[str, int]]:
        rows = sorted(
            ((path, count) for path, count in self.inline_hotspots.items() if count > 0),
            key=lambda item: item[1],
            reverse=True,
        )
        if self.per_file_count > 0:
            rows.append(("zenzic.toml [per-file]", self.per_file_count))
        rows.sort(key=lambda item: item[1], reverse=True)
        return rows[:limit]


def _collect_inline_suppression_stats(
    docs_root: Path,
    config: ZenzicConfig,
    exclusion_mgr: LayeredExclusionManager,
) -> tuple[int, dict[str, int]]:
    """Count inline suppression directives and hotspot distribution."""
    total = 0
    hotspots: dict[str, int] = {}
    for md_file in iter_markdown_sources(docs_root, config, exclusion_mgr):
        try:
            text = md_file.read_text(encoding="utf-8")
        except OSError:
            continue
        count = count_inline_suppressions(text)
        if count <= 0:
            continue
        total += count
        try:
            rel = str(md_file.relative_to(docs_root))
        except ValueError:
            rel = str(md_file)
        hotspots[rel] = count
    return total, hotspots


def _count_per_file_ignores(config: ZenzicConfig) -> int:
    """Count configured per-file suppression entries (pattern+code pairs)."""
    total = 0
    for codes in config.governance.per_file_ignores.values():
        if not isinstance(codes, list):
            continue
        normalized_codes = {
            str(code).upper().strip()
            for code in codes
            if isinstance(code, str) and str(code).upper().startswith("Z")
        }
        total += len(normalized_codes)
    return total


def _apply_per_file_ignores(findings: list[Finding], config: ZenzicConfig) -> list[Finding]:
    """Filter findings using governance.per_file_ignores patterns."""
    from zenzic.core.codes import NON_SUPPRESSIBLE_CODES

    if not config.governance.per_file_ignores:
        return findings

    normalized_map: dict[str, set[str]] = {}
    for pattern, codes in config.governance.per_file_ignores.items():
        if not isinstance(pattern, str) or not isinstance(codes, list):
            continue
        normalized_codes = {
            str(code).upper().strip()
            for code in codes
            if isinstance(code, str) and str(code).upper().startswith("Z")
        }
        if normalized_codes:
            normalized_map[pattern] = normalized_codes

    if not normalized_map:
        return findings

    filtered: list[Finding] = []
    for finding in findings:
        code = finding.code.upper().strip()
        if code in NON_SUPPRESSIBLE_CODES:
            filtered.append(finding)
            continue
        if any(
            fnmatch(finding.rel_path, pattern) and code in codes
            for pattern, codes in normalized_map.items()
        ):
            continue
        filtered.append(finding)
    return filtered


def _collect_all_results(
    repo_root: Path,
    docs_root: Path,
    config: ZenzicConfig,
    exclusion_mgr: LayeredExclusionManager,
    strict: bool,
    check_external: bool = True,
) -> _AllCheckResults:
    """Run all seven checks and return results as a typed container."""
    from zenzic.core.adapters import get_adapter

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

    config_asset_issues: list[tuple[str, str]] = []
    _engine = config.build_context.engine
    if _engine == "docusaurus":
        from zenzic.core.adapters._docusaurus import (
            check_config_assets as _docusaurus_check_assets,
            find_docusaurus_config,
        )

        dc_config = find_docusaurus_config(repo_root)
        if dc_config is not None:
            config_asset_issues = _docusaurus_check_assets(dc_config, repo_root)
    elif _engine == "mkdocs":
        from zenzic.core.adapters._mkdocs import check_config_assets as _mkdocs_check_assets

        config_asset_issues = _mkdocs_check_assets(repo_root)
    elif _engine == "zensical":
        from zenzic.core.adapters._zensical import check_config_assets as _zensical_check_assets

        config_asset_issues = _zensical_check_assets(repo_root)

    return _AllCheckResults(
        link_errors=validate_links_structured(
            docs_root,
            exclusion_mgr,
            repo_root=repo_root,
            config=config,
            strict=strict,
            locale_roots=locale_roots,
            check_external=check_external,
        ),
        orphans=find_orphans(docs_root, exclusion_mgr, repo_root=repo_root, config=config),
        snippet_errors=validate_snippets(docs_root, exclusion_mgr, config=config),
        placeholders=find_placeholders(
            docs_root, exclusion_mgr, config=config, repo_root=repo_root
        ),
        unused_assets=find_unused_assets(
            docs_root,
            exclusion_mgr,
            config=config,
            repo_root=repo_root,
            adapter_metadata_files=adapter.get_metadata_files(),
        ),
        nav_contract_errors=check_nav_contract(repo_root, exclusion_mgr),
        reference_reports=ref_reports,
        security_events=security_events,
        directory_index_issues=find_missing_directory_indices(
            docs_root, exclusion_mgr, repo_root=repo_root, config=config
        ),
        config_asset_issues=config_asset_issues,
        i18n_parity_issues=find_i18n_parity(repo_root, config=config),
        i18n_strict=config.i18n.strict_parity,
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
                code=err.code,
                severity=(
                    "security_incident"
                    if err.code in ("Z203", "Z202")
                    else "info"
                    if err.code == "Z106"
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
                code="Z402",
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
                code="Z503",
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
                code="Z405",
                severity="warning",
                message="File not referenced in any documentation page.",
            )
        )

    for msg in results.nav_contract_errors:
        findings.append(
            Finding(
                rel_path="(nav)",
                line_no=0,
                code="Z406",
                severity="error",
                message=msg,
            )
        )

    _i18n_strict = results.i18n_strict
    for issue in results.i18n_parity_issues:
        findings.append(
            Finding(
                rel_path=_rel(issue.file_path),
                line_no=0,
                code="Z602",
                severity="error" if _i18n_strict else "warning",
                message=issue.message,
            )
        )

    for report in results.reference_reports:
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
                    source_line=rule_f.matched_line,
                    col_start=rule_f.col_start,
                    match_text=rule_f.match_text,
                )
            )
        for sf in report.security_findings:
            findings.append(_map_shield_to_finding(sf, docs_root))

    for dir_path in results.directory_index_issues:
        findings.append(
            Finding(
                rel_path=str(dir_path),
                line_no=0,
                code="Z401",
                severity="info",
                message=(
                    "Directory contains Markdown files but has no index page — "
                    "the directory URL may return a 404."
                ),
            )
        )

    for rel_path, message in results.config_asset_issues:
        findings.append(
            Finding(
                rel_path=rel_path,
                line_no=0,
                code="Z404",
                severity="warning",
                message=message,
            )
        )

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
                _shared.console.print(
                    f"[red]ERROR:[/] [bold]{raw}[/] is not a Markdown file "
                    f"(expected .md, got '{candidate.suffix}')."
                )
                raise typer.Exit(1)
            return candidate.resolve()
    _shared.console.print(
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
    """
    target = _resolve_target(repo_root, config, raw_path)

    try:
        rel = target.relative_to(repo_root)
        if rel == Path("."):
            # Target IS repo_root itself — use relpath from CWD for clean display.
            # This avoids the "././" balbettio caused by f"./{Path('.')}".
            hint = os.path.relpath(target) + ("/" if target.is_dir() else "")
        else:
            hint = f"./{rel}" + ("/" if target.is_dir() else "")
    except ValueError:
        # Target is outside repo_root (cross-repo scan) — use relpath from CWD.
        try:
            hint = os.path.relpath(target) + ("/" if target.is_dir() else "")
        except ValueError:
            hint = str(target) + ("/" if target.is_dir() else "")

    if target.is_dir():
        # CEO-052: if target IS the project root, preserve the configured docs_dir.
        # The explicit path was used to locate the correct project config —
        # not to redefine the documentation scope. Overriding docs_dir to "."
        # would scan the entire project root (including blog/, scripts/, etc.)
        # instead of respecting the configured docs_dir (e.g. "docs").
        if target == repo_root:
            docs_root = (repo_root / config.docs_dir).resolve()
            return config, None, docs_root, hint
        try:
            new_docs_dir = target.relative_to(repo_root)
        except ValueError:
            new_docs_dir = target
        return config.model_copy(update={"docs_dir": new_docs_dir}), None, target, hint

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
    output_format: str = typer.Option(
        "text", "--format", "-f", help="Output format: text, json, or sarif."
    ),
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
    offline: bool = typer.Option(
        False, "--offline", help="Force flat URL resolution for offline builds."
    ),
    no_external: bool = typer.Option(
        False,
        "--no-external",
        help=(
            "Skip HTTP validation of external URLs (Pass 3). "
            "For air-gapped / offline environments. "
            "Shield (Z201) always active regardless of this flag."
        ),
    ),
    exclude_url: list[str] = typer.Option(
        [],
        "--exclude-url",
        help=(
            "Bypass external URL validation for URLs matching this prefix (repeatable). "
            "Merged with excluded_external_urls from zenzic.toml at runtime."
        ),
        metavar="PREFIX",
    ),
) -> None:
    """Run all checks: links, orphans, snippets, placeholders, assets, references.

    Optionally pass PATH to scope the audit to a single Markdown file or a custom
    directory (e.g. ``README.md``, ``content/``).  Zenzic auto-selects the
    StandaloneAdapter when the target lives outside the configured docs directory.
    """
    # GAP-04: Conflict validation — --strict and --exit-zero are mutually exclusive.
    if strict and exit_zero:
        typer.echo(
            "ERROR: --strict and --exit-zero are mutually exclusive. "
            "--strict promotes warnings to errors; --exit-zero suppresses all exit codes.",
            err=True,
        )
        raise typer.Exit(2)
    # CEO-052 "The Sovereign Root Fix": when an explicit target PATH is given,
    # derive repo_root by searching upward FROM that path — not from CWD.
    # "The configuration follows the target, not the caller."
    _search_from: Path | None = None
    if path is not None:
        _pre = Path(path).resolve()
        _search_from = _pre.parent if _pre.is_file() else _pre
    try:
        repo_root = find_repo_root(search_from=_search_from)
        config, loaded_from_file = ZenzicConfig.load(repo_root)
    except RuntimeError as exc:
        typer.echo(f"ERROR: {exc}", err=True)
        raise typer.Exit(1) from exc
    if not loaded_from_file and not quiet:
        _shared._print_no_config_hint(output_format)
    config = _shared._apply_engine_override(config, engine)
    if offline:
        config.build_context.offline_mode = True
    if exclude_url:
        config = config.model_copy(
            update={"excluded_external_urls": config.excluded_external_urls + list(exclude_url)}
        )

    if not quiet and output_format == "text":
        from zenzic import __version__

        _shared._ui.print_header(__version__)

    _single_file: Path | None = None
    _target_hint: str | None = None
    if path is not None:
        config, _single_file, _, _target_hint = _apply_target(repo_root, config, path)

    docs_root = (repo_root / config.docs_dir).resolve()
    # CEO-043: explicit target may live outside the CWD repo root.
    # Adopt the target as the sovereign sandbox so Blood Sentinel guards
    # escapes FROM the target, not the location OF the target.
    try:
        docs_root.relative_to(repo_root)
    except ValueError:
        repo_root = docs_root
    exclusion_mgr = _shared._build_exclusion_manager(
        config,
        repo_root,
        docs_root,
        exclude_dirs=exclude_dir,
        include_dirs=include_dir,
    )

    effective_strict = strict if strict is not None else config.strict
    effective_exit_zero = exit_zero if exit_zero is not None else config.exit_zero

    t0 = time.monotonic()
    inline_suppressions, inline_hotspots = _collect_inline_suppression_stats(
        docs_root, config, exclusion_mgr
    )
    per_file_suppressions = _count_per_file_ignores(config)
    suppression_audit = _SuppressionAudit(
        inline_count=inline_suppressions,
        per_file_count=per_file_suppressions,
        cap=config.governance.suppression_cap,
        inline_hotspots=inline_hotspots,
    )

    if (
        config.governance.suppression_cap_fail_hard
        and suppression_audit.total > suppression_audit.cap
    ):
        if output_format == "json":
            print(
                json.dumps(
                    {
                        "error": "SUPPRESSION_CAP_EXCEEDED",
                        "message": (
                            f"Suppression cap exceeded: {suppression_audit.total}/{suppression_audit.cap}. "
                            "Reduce inline/per-file suppressions before release."
                        ),
                        "playbook": "https://zenzic.dev/developers/how-to/release-governance-protocol",
                    },
                    indent=2,
                )
            )
        elif output_format == "text":
            if not quiet:
                _shared.console.print()
            _shared.console.print(
                "[bold red]✘ GOVERNANCE_FAILURE: SUPPRESSION_CAP_EXCEEDED[/bold red]"
            )
            _shared.console.print(
                "The current repository exceeds the maximum allowed architectural debt."
            )
            _shared.console.print()
            _shared.console.print("[bold][STATISTICS][/bold]")
            _shared.console.print(
                f"  • Total Active Suppressions: [bold]{suppression_audit.total}[/bold]"
            )
            _shared.console.print(
                f"  • Configured Global CAP:     [bold]{suppression_audit.cap}[/bold]"
            )
            _shared.console.print(
                f"  • Excess Debt:               [bold red]+{suppression_audit.excess}[/bold red]"
            )
            _shared.console.print()
            _shared.console.print("[bold][BREAKDOWN][/bold]")
            _shared.console.print(
                f"  • Inline Ignores (zenzic-ignore):  [bold]{suppression_audit.inline_count}[/bold]"
            )
            _shared.console.print(
                f"  • Per-File Ignores (config):       [bold]{suppression_audit.per_file_count}[/bold]"
            )
            _shared.console.print()
            _shared.console.print("[bold][HOTSPOTS - Top Offenders][/bold]")
            for path, count in suppression_audit.top_offenders(limit=5):
                _shared.console.print(f"  [bold red]{count:>3}[/bold red]  {path}")
            _shared.console.print()
            _shared.console.print("[bold][REMEDIATION][/bold]")
            _shared.console.print(
                "  1. Review hotspots and resolve underlying issues to remove suppressions."
            )
            _shared.console.print(
                "  2. If debt is intentional, increase 'governance.suppression_cap' in zenzic.toml."
            )
            _shared.console.print(
                "  3. Consult the Playbook: [cyan]https://zenzic.dev/developers/how-to/release-governance-protocol[/cyan]"
            )
            _shared.console.print(
                "[bold red][DEBT_STATUS][/bold red] ✘ FAILED (Fail-Hard Policy Active)"
            )
        raise typer.Exit(1)

    results = _collect_all_results(
        repo_root,
        docs_root,
        config,
        exclusion_mgr,
        strict=effective_strict,
        check_external=not no_external,
    )
    elapsed = time.monotonic() - t0

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
    elif output_format == "sarif":
        from zenzic import __version__

        all_findings = _to_findings(results, docs_root)
        _shared._output_sarif_findings(all_findings, __version__)
        incidents = sum(1 for f in all_findings if f.severity == "security_incident")
        if incidents:
            raise typer.Exit(3)
        breaches = sum(1 for f in all_findings if f.severity == "security_breach")
        if breaches:
            raise typer.Exit(2)
        errors_count = sum(1 for f in all_findings if f.severity == "error")
        if errors_count and not effective_exit_zero:
            raise typer.Exit(1)
        return

    from zenzic import __version__

    all_findings = _to_findings(results, docs_root)
    all_findings = _apply_per_file_ignores(all_findings, config)

    if _single_file is not None:
        _sf_rel = str(_single_file.relative_to(docs_root))
        all_findings = [f for f in all_findings if f.rel_path == _sf_rel]

    reporter = SentinelReporter(_shared.console, docs_root, docs_dir=str(config.docs_dir))

    if quiet:
        errors, warnings = reporter.render_quiet(all_findings)
    else:
        docs_count, assets_count = _shared._count_docs_assets(
            docs_root, repo_root, exclusion_mgr, config
        )
        if _single_file is not None:
            docs_count, assets_count = 1, 0

        # Z906 guardrail: if the target contains zero Markdown sources, inform
        # the user with an amber warning and exit cleanly (not a system error).
        if docs_count == 0 and _single_file is None:
            _target_display = _target_hint or "./"
            _shared.console.print(
                f"[bold yellow]\u26a0 Z906 NO_FILES_FOUND[/bold yellow] — "
                f"No Markdown sources found in [cyan]{_target_display}[/cyan]. "
                "Audit skipped."
            )
            return

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

    if no_external and output_format == "text" and not quiet:
        _shared.console.print(
            "[dim] 💡 External link validation skipped (--no-external). "
            "Shield (Z201) remains active.[/dim]\n"
        )

    if output_format == "text":
        extended = " [yellow][EXTENDED DEBT][/yellow]" if suppression_audit.extended_debt else ""
        _shared.console.print(
            "[dim]Suppression Audit:[/] "
            f"[bold]{suppression_audit.total}/{suppression_audit.cap}[/bold] "
            f"(inline: {suppression_audit.inline_count}, per-file: {suppression_audit.per_file_count})"
            f"{extended}"
        )

    incidents = sum(1 for f in all_findings if f.severity == "security_incident")
    if incidents:
        raise typer.Exit(3)
    breaches = sum(1 for f in all_findings if f.severity == "security_breach")
    if breaches:
        raise typer.Exit(2)

    has_failures = (errors > 0) or (effective_strict and warnings > 0)

    if has_failures:
        if not effective_exit_zero:
            raise typer.Exit(1)
