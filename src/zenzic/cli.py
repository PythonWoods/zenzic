# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""CLI command definitions for zenzic."""

from __future__ import annotations

import errno
import functools
import http.server
import json
import shutil
import socket
from dataclasses import dataclass
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from zenzic.core.adapters import list_adapter_engines
from zenzic.core.scanner import (
    PlaceholderFinding,
    find_orphans,
    find_placeholders,
    find_repo_root,
    find_unused_assets,
    scan_docs_references_with_links,
)
from zenzic.core.scorer import ScoreReport, compute_score, load_snapshot, save_snapshot
from zenzic.core.validator import (
    SnippetError,
    check_nav_contract,
    validate_links,
    validate_snippets,
)
from zenzic.models.config import ZenzicConfig


check_app = typer.Typer(
    name="check",
    help="Run documentation quality checks.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

clean_app = typer.Typer(
    name="clean",
    help="Safely remove unused documentation files.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console(highlight=False)

_NO_CONFIG_HINT = Panel(
    "Using built-in defaults — no [bold]zenzic.toml[/] found.\n"
    "Run [bold cyan]zenzic init[/] to create a project configuration file.\n"
    "Customise docs directory, excluded paths, engine adapter, and lint rules.",
    title="[bold yellow]💡 Zenzic Tip[/]",
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
        console.print(
            f"[red]ERROR:[/] Unknown engine adapter [bold]{engine!r}[/].\n"
            f"Installed adapters: {engines_fmt}\n"
            "Install a third-party adapter or choose from the list above."
        )
        raise typer.Exit(1)
    new_context = config.build_context.model_copy(update={"engine": engine})
    return config.model_copy(update={"build_context": new_context})


@check_app.command(name="links")
def check_links(
    strict: bool = typer.Option(False, "--strict", "-s", help="Exit non-zero on any warning."),
) -> None:
    """Check for broken internal links. Pass --strict to also validate external URLs."""
    repo_root = find_repo_root()
    errors = validate_links(repo_root, strict=strict)
    if errors:
        console.print(f"\n[red]BROKEN LINKS ({len(errors)}):[/]")
        for err in errors:
            console.print(f"  [yellow]{err}[/]")
        raise typer.Exit(1)
    console.print("\n[green]OK:[/] no broken links found.")


@check_app.command(name="orphans")
def check_orphans(
    engine: str | None = typer.Option(
        None,
        "--engine",
        help="Override the build engine adapter (e.g. mkdocs, zensical). "
        "Auto-detected from zenzic.toml when omitted.",
        metavar="ENGINE",
    ),
) -> None:
    """Detect .md files not listed in the nav."""
    repo_root = find_repo_root()
    config, loaded_from_file = ZenzicConfig.load(repo_root)
    if not loaded_from_file:
        _print_no_config_hint()
    config = _apply_engine_override(config, engine)
    orphans = find_orphans(repo_root, config)
    if orphans:
        console.print(f"\n[red]ORPHANS ({len(orphans)}):[/] physical files not in nav:")
        for path in orphans:
            console.print(f"  [yellow]{path}[/]")
        raise typer.Exit(1)
    console.print("\n[green]OK:[/] no orphan pages found.")


@check_app.command(name="snippets")
def check_snippets() -> None:
    """Validate Python code blocks in documentation Markdown files."""
    repo_root = find_repo_root()
    config, loaded_from_file = ZenzicConfig.load(repo_root)
    if not loaded_from_file:
        _print_no_config_hint()
    errors = validate_snippets(repo_root, config)
    if errors:
        console.print(f"\n[red]INVALID SNIPPETS ({len(errors)}):[/]")
        for err in errors:
            console.print(f"  [yellow]{err.file_path}:{err.line_no}[/] - {err.message}")
        raise typer.Exit(1)
    console.print("\n[green]OK:[/] all Python snippets are syntactically valid.")


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
    repo_root = find_repo_root()
    config, loaded_from_file = ZenzicConfig.load(repo_root)
    if not loaded_from_file:
        _print_no_config_hint()
    reports, link_errors = scan_docs_references_with_links(
        repo_root, validate_links=links, config=config
    )

    docs_root = repo_root / config.docs_dir

    # ── Check for secrets first (Exit Code 2) ─────────────────────────────────
    security_hits = [(r.file_path, sf) for r in reports for sf in r.security_findings]
    if security_hits:
        console.print("\n[bold red]╔══════════════════════════════════════╗[/]")
        console.print("[bold red]║        SECURITY CRITICAL             ║[/]")
        console.print("[bold red]║  Secret(s) detected in documentation ║[/]")
        console.print("[bold red]╚══════════════════════════════════════╝[/]\n")
        for _fp, sf in security_hits:
            try:
                display_path = sf.file_path.relative_to(docs_root)
            except ValueError:
                display_path = sf.file_path
            console.print(
                f"  [bold red][SHIELD][/] {display_path}:{sf.line_no} "
                f"— [red]{sf.secret_type}[/] detected in URL"
            )
            console.print(f"    [dim]{sf.url[:80]}[/]")
        console.print("\n[bold red]Build aborted.[/] Rotate the exposed credential immediately.")
        raise typer.Exit(2)

    # ── Collect reference findings ─────────────────────────────────────────────
    all_errors: list[str] = []
    all_warnings: list[str] = []
    total_score = 0.0
    file_count = len(reports)

    for report in reports:
        try:
            rel = report.file_path.relative_to(docs_root)
        except ValueError:
            rel = report.file_path
        for finding in report.findings:
            msg = f"  [yellow]{rel}:{finding.line_no}[/] [{finding.issue}] — {finding.detail}"
            if finding.is_warning:
                all_warnings.append(msg)
            else:
                all_errors.append(msg)

        for rf in report.rule_findings:
            severity_color = "red" if rf.is_error else "yellow"
            header = (
                f"[{severity_color}][{rf.rule_id}][/] [dim]{rel}:{rf.line_no}[/] — {rf.message}"
            )
            if rf.matched_line:
                snippet = rf.matched_line.rstrip()
                msg = f"{header}\n  [dim]│[/] [italic]{snippet}[/]"
            else:
                msg = header
            if rf.is_error:
                all_errors.append(msg)
            else:
                all_warnings.append(msg)

        if file_count:
            total_score += report.score

    avg_score = total_score / file_count if file_count else 100.0

    # ── Output ─────────────────────────────────────────────────────────────────
    if all_errors:
        console.print(f"\n[red]REFERENCE ERRORS ({len(all_errors)}):[/]")
        for msg in all_errors:
            console.print(msg)

    if all_warnings:
        label = "[red]REFERENCE WARNINGS[/]" if strict else "[yellow]REFERENCE WARNINGS[/]"
        console.print(f"\n{label} ({len(all_warnings)}):")
        for msg in all_warnings:
            console.print(msg)

    if link_errors:
        console.print(f"\n[red]BROKEN REFERENCE URLS ({len(link_errors)}):[/]")
        for err in link_errors:
            console.print(f"  [yellow]{err}[/]")

    console.print(
        f"\n[dim]Reference Integrity:[/] [bold]{avg_score:.1f}%[/] across {file_count} file(s)."
    )
    if links:
        console.print("[dim]External URL validation: enabled.[/]")

    failed = bool(all_errors) or bool(link_errors) or (strict and bool(all_warnings))
    if failed:
        raise typer.Exit(1)

    console.print("\n[green]OK:[/] all references resolved.")


@check_app.command(name="assets")
def check_assets() -> None:
    """Detect unused images and assets in the documentation."""
    repo_root = find_repo_root()
    config, loaded_from_file = ZenzicConfig.load(repo_root)
    if not loaded_from_file:
        _print_no_config_hint()
    unused = find_unused_assets(repo_root, config)
    if unused:
        console.print(
            f"\n[red]UNUSED ASSETS ({len(unused)}):[/] physical files not linked anywhere:"
        )
        for path in unused:
            console.print(f"  [yellow]{path}[/]")
        raise typer.Exit(1)
    console.print("\n[green]OK:[/] no unused assets found.")


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

    unused = find_unused_assets(repo_root, config)
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
def check_placeholders() -> None:
    """Detect pages with < 50 words or containing TODOs/stubs."""
    repo_root = find_repo_root()
    config, loaded_from_file = ZenzicConfig.load(repo_root)
    if not loaded_from_file:
        _print_no_config_hint()
    findings = find_placeholders(repo_root, config)
    if findings:
        console.print(f"\n[red]PLACEHOLDERS/STUBS ({len(findings)}):[/]")
        for f in findings:
            console.print(f"  [yellow]{f.file_path}:{f.line_no}[/] [{f.issue}] - {f.detail}")
        raise typer.Exit(1)
    console.print("\n[green]OK:[/] no placeholder stubs found.")


@dataclass
class _AllCheckResults:
    link_errors: list[str]
    orphans: list[Path]
    snippet_errors: list[SnippetError]
    placeholders: list[PlaceholderFinding]
    unused_assets: list[Path]
    nav_contract_errors: list[str]
    reference_errors: list[str]
    security_events: int

    @property
    def failed(self) -> bool:
        return bool(
            self.link_errors
            or self.orphans
            or self.snippet_errors
            or self.placeholders
            or self.unused_assets
            or self.nav_contract_errors
            or self.reference_errors
            or self.security_events
        )


def _collect_all_results(
    repo_root: Path,
    config: ZenzicConfig,
    strict: bool,
) -> _AllCheckResults:
    """Run all seven checks and return results as a typed container."""
    ref_reports, _ = scan_docs_references_with_links(repo_root, validate_links=False, config=config)
    docs_root = repo_root / config.docs_dir
    reference_errors: list[str] = []
    security_events = 0
    for report in ref_reports:
        for _sf in report.security_findings:
            security_events += 1
        for finding in report.findings:
            if not finding.is_warning:
                try:
                    rel = report.file_path.relative_to(docs_root)
                except ValueError:
                    rel = report.file_path
                reference_errors.append(
                    f"{rel}:{finding.line_no} [{finding.issue}] — {finding.detail}"
                )
    return _AllCheckResults(
        link_errors=validate_links(repo_root, strict=strict),
        orphans=find_orphans(repo_root, config),
        snippet_errors=validate_snippets(repo_root, config),
        placeholders=find_placeholders(repo_root, config),
        unused_assets=find_unused_assets(repo_root, config),
        nav_contract_errors=check_nav_contract(repo_root),
        reference_errors=reference_errors,
        security_events=security_events,
    )


@check_app.command(name="all")
def check_all(
    strict: bool | None = typer.Option(
        None, "--strict", "-s", help="Treat warnings as errors and validate external URLs."
    ),
    output_format: str = typer.Option("text", "--format", help="Output format: text or json."),
    exit_zero: bool | None = typer.Option(
        None, "--exit-zero", help="Always exit 0; report issues without failing."
    ),
    engine: str | None = typer.Option(
        None,
        "--engine",
        help="Override the build engine adapter (e.g. mkdocs, zensical). "
        "Auto-detected from zenzic.toml when omitted.",
        metavar="ENGINE",
    ),
) -> None:
    """Run all checks: links, orphans, snippets, placeholders, assets, references."""
    repo_root = find_repo_root()
    config, loaded_from_file = ZenzicConfig.load(repo_root)
    if not loaded_from_file:
        _print_no_config_hint()
    config = _apply_engine_override(config, engine)
    effective_strict = strict if strict is not None else config.strict
    effective_exit_zero = exit_zero if exit_zero is not None else config.exit_zero
    results = _collect_all_results(repo_root, config, strict=effective_strict)

    if output_format == "json":
        report = {
            "links": results.link_errors,
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
            "references": results.reference_errors,
        }
        print(json.dumps(report, indent=2))
        if results.failed and not effective_exit_zero:
            raise typer.Exit(1)
        return

    # 1. Links
    console.print("Running link check...")
    if results.link_errors:
        console.print(f"[red]BROKEN LINKS ({len(results.link_errors)}):[/]")
        for err in results.link_errors:
            console.print(f"  [yellow]{err}[/]")
    else:
        console.print("[green]OK:[/] links.")

    # 2. Orphans
    console.print("\nRunning orphan check...")
    if results.orphans:
        console.print(f"[red]ORPHANS ({len(results.orphans)}):[/]")
        for path in results.orphans:
            console.print(f"  [yellow]{path}[/]")
    else:
        console.print("[green]OK:[/] orphans.")

    # 3. Snippets
    console.print("\nRunning snippet check...")
    if results.snippet_errors:
        console.print(f"[red]INVALID SNIPPETS ({len(results.snippet_errors)}):[/]")
        for s_err in results.snippet_errors:
            console.print(f"  [yellow]{s_err.file_path}:{s_err.line_no}[/] - {s_err.message}")
    else:
        console.print("[green]OK:[/] snippets.")

    # 4. Placeholders
    console.print("\nRunning placeholder check...")
    if results.placeholders:
        console.print(f"[red]PLACEHOLDERS/STUBS ({len(results.placeholders)}):[/]")
        for f in results.placeholders:
            console.print(f"  [yellow]{f.file_path}:{f.line_no}[/] [{f.issue}] - {f.detail}")
    else:
        console.print("[green]OK:[/] placeholders.")

    # 5. Unused Assets
    console.print("\nRunning unused assets check...")
    if results.unused_assets:
        console.print(f"[red]UNUSED ASSETS ({len(results.unused_assets)}):[/]")
        for path in results.unused_assets:
            console.print(f"  [yellow]{path}[/]")
    else:
        console.print("[green]OK:[/] assets.")

    # 6. Nav-contract
    console.print("\nRunning nav-contract check...")
    if results.nav_contract_errors:
        console.print(f"[red]NAV CONTRACT VIOLATIONS ({len(results.nav_contract_errors)}):[/]")
        for err in results.nav_contract_errors:
            console.print(f"  [yellow]{err}[/]")
    else:
        console.print("[green]OK:[/] nav contract.")

    # 7. References (dangling links + Shield)
    console.print("\nRunning reference check...")
    if results.security_events:
        console.print(
            f"[bold red]SECURITY CRITICAL:[/] {results.security_events} credential(s) detected. "
            "Exit code 2 — rotate immediately."
        )
        raise typer.Exit(2)
    if results.reference_errors:
        console.print(f"[red]DANGLING REFERENCES ({len(results.reference_errors)}):[/]")
        for err in results.reference_errors:
            console.print(f"  [yellow]{err}[/]")
    else:
        console.print("[green]OK:[/] references.")

    if results.failed:
        console.print("\n[red]FAILED:[/] One or more checks failed.")
        if not effective_exit_zero:
            raise typer.Exit(1)
    else:
        console.print("\n[green]SUCCESS:[/] All checks passed.")


def _detect_engine(repo_root: Path, override: str | None) -> str | None:
    """Resolve which documentation engine binary to use for ``zenzic serve``.

    Resolution order (first match wins):

    1. Explicit ``--engine`` flag → validate binary on PATH and ``mkdocs.yml``
       presence, return it or exit.
    2. ``mkdocs.yml`` present → prefer ``"zensical"`` (reads ``mkdocs.yml``
       natively), fall back to ``"mkdocs"``.
    3. No config file found → return ``None`` (caller falls back to static
       serving of ``site/``).

    Returning ``None`` rather than raising ensures ``serve`` works without any
    documentation engine installed — satisfying the engine-agnostic constraint.

    Args:
        repo_root: Repository root directory.
        override: Value of the ``--engine`` CLI flag (``None`` if not passed).

    Returns:
        Engine binary name (``"zensical"`` or ``"mkdocs"``), or ``None`` only
        when ``mkdocs.yml`` is absent (pure static-fallback scenario).

    Raises:
        typer.Exit: When ``--engine`` binary is absent from ``$PATH`` or
            ``mkdocs.yml`` is missing; or when ``mkdocs.yml`` is present but
            neither engine binary is installed.
    """
    # Both engines accept mkdocs.yml; zensical reads it natively.
    _ENGINE_CONFIGS: dict[str, tuple[str, ...]] = {
        "zensical": ("mkdocs.yml",),
        "mkdocs": ("mkdocs.yml",),
    }
    if override is not None:
        if shutil.which(override) is None:
            console.print(
                f"[red]ERROR:[/] engine '[bold]{override}[/]' not found on PATH. Is it installed?"
            )
            raise typer.Exit(1)
        accepted = _ENGINE_CONFIGS.get(override, ())
        if accepted and not any((repo_root / cfg).exists() for cfg in accepted):
            names = " or ".join(f"[bold]{c}[/]" for c in accepted)
            console.print(
                f"[red]ERROR:[/] --engine [bold]{override}[/] requires "
                f"{names} in the repository root, but the file was not found."
            )
            raise typer.Exit(1)
        return override

    if (repo_root / "mkdocs.yml").exists():
        if shutil.which("zensical"):
            return "zensical"
        if shutil.which("mkdocs"):
            return "mkdocs"
        console.print(
            "[red]ERROR:[/] Found [bold]mkdocs.yml[/] but neither "
            "[bold]zensical[/] nor [bold]mkdocs[/] is installed.\n"
            "Install a documentation engine: [bold]uv add --dev zensical[/] "
            "or [bold]uv add --dev mkdocs[/]"
        )
        raise typer.Exit(1)

    return None  # No config file found — serve() falls back to static serving of site/


def _find_free_port(start: int, limit: int = 10) -> int:
    """Return the first available TCP port in ``[start, start+limit)``.

    Probes by attempting a temporary bind on ``127.0.0.1`` so the result
    is reliable before we hand it to either an engine subprocess or the
    built-in static server.

    Raises:
        OSError: with ``errno.EADDRINUSE`` when no free port exists in the
            scanned range.
    """
    for candidate in range(start, start + limit):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", candidate))
                return candidate
            except OSError as exc:
                if exc.errno != errno.EADDRINUSE:
                    raise
    raise OSError(errno.EADDRINUSE, f"No free port in {start}–{start + limit - 1}")


def serve(
    engine_override: str | None = typer.Option(
        None,
        "--engine",
        help="Force a specific engine: 'mkdocs' or 'zensical'. Auto-detected when omitted.",
        metavar="ENGINE",
    ),
    no_preflight: bool = typer.Option(
        False,
        "--no-preflight",
        help="Skip the pre-flight quality check and start the server immediately.",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Starting port. Zenzic scans up to 10 consecutive ports if the requested one is busy.",
        min=1024,
        max=65535,
    ),
) -> None:
    """Run pre-flight checks, then start the documentation development server.

    Engine auto-detection (overridable with ``--engine``):

    * ``mkdocs.yml`` present + ``zensical`` installed → ``zensical serve``
    * ``mkdocs.yml`` present + only ``mkdocs`` avail  → ``mkdocs serve``

    Quality issues found during the pre-flight are printed as warnings but
    never block startup — fix them live while the server is running.
    """
    repo_root = find_repo_root()
    engine = _detect_engine(repo_root, engine_override)

    # ── Pre-flight check ──────────────────────────────────────────────────────
    if not no_preflight:
        console.print("[dim]Zenzic pre-flight check…[/]")
        config, _ = ZenzicConfig.load(repo_root)
        issue_count = 0

        for orphan in find_orphans(repo_root, config):
            console.print(f"  [yellow]⚠  [orphan][/] {orphan}")
            issue_count += 1
        for err in validate_snippets(repo_root, config):
            console.print(
                f"  [yellow]⚠  [snippet][/] {err.file_path}:{err.line_no} — {err.message}"
            )
            issue_count += 1
        for finding in find_placeholders(repo_root, config):
            console.print(
                f"  [yellow]⚠  [placeholder][/] {finding.file_path}:{finding.line_no}"
                f" [{finding.issue}]"
            )
            issue_count += 1
        for asset in find_unused_assets(repo_root, config):
            console.print(f"  [yellow]⚠  [asset][/] {asset}")
            issue_count += 1

        if issue_count:
            console.print(
                f"\n[yellow]{issue_count} issue(s) detected.[/] "
                "Fix them while the server is running — "
                "run [bold]zenzic check all[/] to recheck.\n"
            )
        else:
            console.print("[green]OK[/] — all checks passed.\n")

    # ── Resolve a free port (applies to both engine and static fallback) ──────
    _PORT_SCAN_LIMIT = 10
    try:
        free_port = _find_free_port(port, _PORT_SCAN_LIMIT)
    except OSError:
        console.print(
            f"[red]ERROR:[/] All ports {port}–{port + _PORT_SCAN_LIMIT - 1} "
            "are in use. Free a port and try again."
        )
        raise typer.Exit(1) from None
    if free_port != port:
        console.print(f"[yellow]Port {port} already in use — using {free_port}[/]")

    # ── Launch the dev server ─────────────────────────────────────────────────
    if engine:
        import subprocess  # deferred — only needed when an engine subprocess is launched

        console.print(f"[bold blue]Zenzic:[/] Starting [bold]{engine} serve[/]…")
        subprocess.run(
            [engine, "serve", "--dev-addr", f"127.0.0.1:{free_port}"],
            cwd=repo_root,
        )
    else:
        site_dir = repo_root / "site"
        if not site_dir.is_dir():
            console.print(
                "[red]ERROR:[/] No documentation engine found on PATH and no pre-built "
                "[bold]site/[/] directory exists.\n"
                "Install [bold]mkdocs[/] or [bold]zensical[/], or run a build first."
            )
            raise typer.Exit(1)
        console.print(
            "[bold blue]Zenzic:[/] No engine found — serving pre-built "
            f"[bold]{site_dir.relative_to(repo_root)}[/] as static files "
            "(no hot-reload).\n"
            "Install [bold]mkdocs[/] or [bold]zensical[/] for a live-reload server."
        )
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(site_dir))
        try:
            with http.server.HTTPServer(("", free_port), handler) as httpd:
                console.print(
                    f"Serving on [link=http://localhost:{free_port}]http://localhost:{free_port}[/link]"
                    " — Ctrl+C to stop."
                )
                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    pass
        except OSError as exc:
            if exc.errno == errno.EADDRINUSE:
                # TOCTOU: port was taken between probe and bind
                console.print(f"[red]ERROR:[/] Port {free_port} became unavailable. Try again.")
                raise typer.Exit(1) from None
            raise


def _run_all_checks(
    repo_root: Path,
    config: ZenzicConfig,
    strict: bool,
) -> ScoreReport:
    """Run all five checks and return a ScoreReport. Used by score and diff."""
    link_errors = validate_links(repo_root, strict=strict)
    orphans = find_orphans(repo_root, config)
    snippet_errors = validate_snippets(repo_root, config)
    placeholders = find_placeholders(repo_root, config)
    unused_assets = find_unused_assets(repo_root, config)

    return compute_score(
        link_errors=len(link_errors),
        orphans=len(orphans),
        snippet_errors=len(snippet_errors),
        placeholders=len(placeholders),
        unused_assets=len(unused_assets),
    )


def score(
    strict: bool | None = typer.Option(
        None, "--strict", "-s", help="Run link check in strict mode."
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
    effective_strict = strict if strict is not None else config.strict
    report = _run_all_checks(repo_root, config, strict=effective_strict)

    # CLI flag takes precedence; fall back to zenzic.toml; 0 means disabled.
    effective_threshold = fail_under if fail_under > 0 else config.fail_under

    if save:
        report.threshold = effective_threshold
        snapshot_path = save_snapshot(repo_root, report)
        console.print(f"[dim]Snapshot saved to {snapshot_path}[/]")

    if output_format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        console.print(f"\nSCORE: [bold]{report.score}/100[/]")
        console.print("")
        for cat in report.categories:
            bar = "[green]PASS[/]" if cat.issues == 0 else "[red]FAIL[/]"
            console.print(
                f"  {bar}  {cat.name:<14} {cat.issues:>3} issue(s)  "
                f"[dim]weight {cat.weight:.0%}  contribution {cat.contribution:.2f}[/]"
            )

    if effective_threshold > 0 and report.score < effective_threshold:
        console.print(
            f"\n[red]FAILED:[/] score {report.score} is below threshold {effective_threshold}."
        )
        raise typer.Exit(1)


def diff(
    strict: bool | None = typer.Option(
        None, "--strict", "-s", help="Run link check in strict mode."
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
    effective_strict = strict if strict is not None else config.strict

    baseline = load_snapshot(repo_root)
    if baseline is None:
        console.print(
            "[yellow]WARNING:[/] no snapshot found. "
            "Run 'zenzic score --save' first to establish a baseline."
        )
        raise typer.Exit(1)

    current = _run_all_checks(repo_root, config, strict=effective_strict)
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
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite an existing zenzic.toml without prompting.",
    ),
) -> None:
    """Scaffold a zenzic.toml configuration file in the current project.

    Performs engine auto-detection: if ``mkdocs.yml`` is present the generated
    file pre-sets ``engine = "mkdocs"``; if ``zensical.toml`` is present it
    pre-sets ``engine = "zensical"``.  Otherwise the ``[build_context]`` block
    is omitted and the vanilla (engine-agnostic) defaults apply.
    """
    repo_root = find_repo_root()
    config_path = repo_root / "zenzic.toml"

    if config_path.is_file() and not force:
        console.print(
            f"[yellow]WARNING:[/] [bold]zenzic.toml[/] already exists at "
            f"[dim]{config_path}[/]\n"
            "Use [bold cyan]--force[/] to overwrite."
        )
        raise typer.Exit(1)

    # Engine auto-detection — mirrors the logic used by _detect_engine() for serve.
    detected_engine: str | None = None
    if (repo_root / "mkdocs.yml").is_file():
        detected_engine = "mkdocs"
    elif (repo_root / "zensical.toml").is_file():
        detected_engine = "zensical"

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
        "# Declare project-specific lint rules (no Python required):\n"
        "# [[custom_rules]]\n"
        '# id       = "ZZ-NODRAFT"\n'
        '# pattern  = "(?i)\\\\bDRAFT\\\\b"\n'
        '# message  = "Remove DRAFT marker before publishing."\n'
        '# severity = "warning"\n'
    )

    config_path.write_text(toml_content, encoding="utf-8")

    engine_line = (
        f"  Engine pre-set to [bold cyan]{detected_engine}[/] (detected from "
        + ("mkdocs.yml" if detected_engine == "mkdocs" else "zensical.toml")
        + ").\n"
        if detected_engine
        else "  No engine config file found — using vanilla (engine-agnostic) defaults.\n"
    )
    console.print(
        f"\n[green]Created[/] [bold]{config_path.relative_to(repo_root)}[/]\n"
        + engine_line
        + "\nEdit the file to enable rules, adjust directories, or set a quality threshold.\n"
        "Run [bold cyan]zenzic check all[/] to validate your documentation."
    )
