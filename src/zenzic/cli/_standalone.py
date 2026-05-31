# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Standalone commands: score, diff, init — and their private helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path


if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # PEP 680 backport
import typer
from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from zenzic.cli.templates import GLOBAL_TOML_TEMPLATE, LOCAL_TOML_TEMPLATE
from zenzic.core import regex as re
from zenzic.core.exceptions import ConfigurationError
from zenzic.core.exclusion import LayeredExclusionManager
from zenzic.core.scanner import (
    find_orphans,
    find_placeholders,
    find_repo_root,
    find_unused_assets,
    scan_docs_references,
)
from zenzic.core.scorer import (
    CategoryScore,
    ScoreReport,
    compute_score,
    load_snapshot,
    save_snapshot,
)
from zenzic.core.ui import ZenzicPalette, emoji
from zenzic.core.validator import (
    check_nav_contract,
    validate_links_structured,
    validate_snippets,
)
from zenzic.models.config import ZenzicConfig

from . import _shared


# ── Module-level compiled patterns ───────────────────────────────────────────
# Slugification helpers (plugin name → project slug).
_SLUG_NONWORD_RE = re.compile(r"[^a-z0-9-]+")
_SLUG_MULTI_DASH_RE = re.compile(r"-+")

# ── Score helpers ─────────────────────────────────────────────────────────────


def _run_all_checks(
    repo_root: Path,
    docs_root: Path,
    config: ZenzicConfig,
    exclusion_mgr: LayeredExclusionManager,
    strict: bool,
) -> ScoreReport:
    """Run all checks and return a ScoreReport. Used by score and diff.

    Builds a ``findings_counts`` dict (Zxxx → count) from all check results
    and passes it to the Zenzic Penalty Scorer.
    """
    from zenzic.core.adapters import get_adapter

    adapter = get_adapter(config.build_context, docs_root, repo_root)
    _locale_roots = adapter.get_locale_source_roots(repo_root)
    locale_roots: list[tuple[Path, str]] | None = _locale_roots if _locale_roots else None
    _content_roots = adapter.get_extra_content_roots(repo_root)
    content_roots: list[Path] | None = _content_roots if _content_roots else None

    link_errors = validate_links_structured(
        docs_root,
        exclusion_mgr,
        repo_root=repo_root,
        config=config,
        strict=strict,
        locale_roots=locale_roots,
        check_external=True,
    )
    orphans = find_orphans(
        docs_root,
        exclusion_mgr,
        config=config,
        has_engine_config=adapter.has_engine_config(),
        nav_paths=adapter.get_nav_paths(),
        is_locale_dir=adapter.is_locale_dir,
        ignored_patterns=adapter.get_ignored_patterns(),
        adapter=adapter,
    )
    snippet_errors = validate_snippets(docs_root, exclusion_mgr, config=config)
    placeholders = find_placeholders(
        docs_root,
        exclusion_mgr,
        config=config,
        locale_roots=locale_roots,
        content_roots=content_roots,
    )
    unused_assets = find_unused_assets(
        docs_root,
        exclusion_mgr,
        config=config,
        locale_roots=locale_roots,
        content_roots=content_roots,
        adapter_metadata_files=adapter.get_metadata_files(),
    )

    # Collect rule findings (Z107, Z505, Z601) and security violations (Z201–Z203)
    # via the Two-Pass Reference Engine.
    ref_reports, _ = scan_docs_references(
        docs_root,
        exclusion_mgr,
        config=config,
        validate_links=False,
        locale_roots=locale_roots,
        content_roots=content_roots,
    )
    nav_errors = check_nav_contract(repo_root, exclusion_mgr)

    # ── Build findings_counts dict (Zenzic Penalty Scorer) ───────────────────────
    findings_counts: dict[str, int] = {}

    # Link errors — split by Zxxx code derived from error_type
    for err in link_errors:
        code = err.code
        findings_counts[code] = findings_counts.get(code, 0) + 1

    # Core check aggregates
    findings_counts["Z402"] = findings_counts.get("Z402", 0) + len(orphans)
    findings_counts["Z503"] = findings_counts.get("Z503", 0) + len(snippet_errors)
    findings_counts["Z405"] = findings_counts.get("Z405", 0) + len(unused_assets)
    findings_counts["Z406"] = findings_counts.get("Z406", 0) + len(nav_errors)

    # Placeholder findings — Z501 (pattern) vs Z502 (short-content) split (CEO-171)
    for pf in placeholders:
        pcode = "Z502" if pf.issue == "Z502" else "Z501"
        findings_counts[pcode] = findings_counts.get(pcode, 0) + 1

    # Rule-engine findings: Z107, Z505, Z601 (rule_id already a Zxxx code).
    # ADR-084: apply directory_policies filter (zero-debt exemptions) so that
    # `zenzic score` honours the same exemptions as `zenzic check`.
    # IMPORTANT: use r.file_path (IntegrityReport — locale-remapped virtual path),
    # NOT rule_f.file_path (RuleFinding — raw absolute path on disk).
    from fnmatch import fnmatch as _fnmatch

    from zenzic.core.codes import NON_SUPPRESSIBLE_CODES

    _dir_policies = (
        config.governance.directory_policies
        if hasattr(config.governance, "directory_policies")
        else {}
    )
    for r in ref_reports:
        # Derive the display-relative path once per report (mirrors _check.py logic).
        try:
            _rel = str(r.file_path.relative_to(docs_root))
        except ValueError:
            try:
                _rel = str(r.file_path.relative_to(repo_root))
            except ValueError:
                _rel = str(r.file_path)
        for rule_f in r.rule_findings:
            code = rule_f.rule_id
            if code in NON_SUPPRESSIBLE_CODES:
                findings_counts[code] = findings_counts.get(code, 0) + 1
                continue
            if _dir_policies and any(
                _fnmatch(_rel, pat) and code in codes for pat, codes in _dir_policies.items()
            ):
                continue  # policy exemption — zero debt cost
            findings_counts[code] = findings_counts.get(code, 0) + 1

    # Security violations (Z2xx) — any breach triggers score override
    security_violations = sum(len(r.security_findings) for r in ref_reports)
    if security_violations > 0:
        findings_counts["Z201"] = findings_counts.get("Z201", 0) + security_violations

    # Suppression Debt: count all active suppressions (inline + per-file config).
    # Each suppression is a technical debt entry that reduces the final score.
    from zenzic.cli._governance import collect_inline_suppression_stats, count_per_file_ignores

    inline_suppressions, _ = collect_inline_suppression_stats(docs_root, config, exclusion_mgr)
    per_file_suppressions = count_per_file_ignores(config)
    total_suppressions = inline_suppressions + per_file_suppressions
    suppression_cap = (
        config.governance.suppression_cap if hasattr(config.governance, "suppression_cap") else 30
    )

    return compute_score(
        findings_counts, suppression_count=total_suppressions, suppression_cap=suppression_cap
    )


# ── badge stamp helpers ────────────────────────────────────────────────────────

_SCORE_BADGE_LABEL = (
    "%F0%9F%9B%A1%EF%B8%8F_zenzic--score"  # 🛡️ zenzic-score (-- = literal dash in Shields.io)
)
_AUDIT_BADGE_LABEL = "%F0%9F%9B%A1%EF%B8%8F_zenzic--audit"  # 🛡️ zenzic-audit
_SCORE_STAMP_MARKER = "<!-- zenzic:score-badge -->"
_AUDIT_STAMP_MARKER = "<!-- zenzic:audit-badge -->"
_SHIELDS_URL_RE = re.compile(r"https://img\.shields\.io/badge/[^\s\"'<>)]*")


def _badge_url(score: int, fail_under: int, security_override: bool) -> str:
    message = f"{score}_%2F_100"
    _threshold = fail_under if fail_under > 0 else 80
    if security_override or score < _threshold:
        color = "ef4444"
    elif score < 100:
        color = "f59e0b"
    else:
        color = "4f46e5"
    return f"https://img.shields.io/badge/{_SCORE_BADGE_LABEL}-{message}-{color}?style=flat-square"


def _audit_badge_url(is_passing: bool) -> str:
    """Generate deterministic audit badge URL for pass/fail state."""
    message = "passing" if is_passing else "failing"
    color = "22c55e" if is_passing else "ef4444"
    return f"https://img.shields.io/badge/{_AUDIT_BADGE_LABEL}-{message}-{color}?style=flat-square"


def _stamp_file(path: Path, marker: str, badge_url: str) -> bool:
    """Update the badge URL on the line after a marker.

    Returns True if the file was modified.
    Raises ValueError if the marker is found but the next line is not a Shields.io badge.
    """
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    modified = False
    i = 0
    while i < len(lines):
        if lines[i].strip() == marker:
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                if "img.shields.io/badge/" not in lines[j]:
                    raise ValueError(
                        f"{path}:{j + 1}: marker '{marker}' found at line {i + 1} "
                        "but next line is not a Shields.io badge"
                    )
                new_line = _SHIELDS_URL_RE.sub(badge_url, lines[j])
                if new_line != lines[j]:
                    lines[j] = new_line
                    modified = True
        i += 1
    if modified:
        path.write_text("".join(lines), encoding="utf-8")
    return modified


def _check_stamp_file(path: Path, marker: str, expected_url: str) -> bool:
    """Return True if the badge after marker matches expected_url.

    Returns True (pass) when the file does not exist, has no marker, or the
    marker has no following badge line — badge is considered 'not configured'.
    Returns False (stale) only when a badge line is present but the URL differs.
    """
    if not path.exists():
        return True
    content = path.read_text(encoding="utf-8")
    if marker not in content:
        return True
    lines = content.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        if lines[i].strip() == marker:
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and "img.shields.io/badge/" in lines[j]:
                m = _SHIELDS_URL_RE.search(lines[j])
                return bool(m and m.group() == expected_url)
        i += 1
    return True


# ── score command ─────────────────────────────────────────────────────────────


def score(
    path: str | None = typer.Argument(
        None,
        help="Repository root or docs directory to score (default: configured docs directory).",
        show_default=False,
    ),
    strict: bool | None = typer.Option(
        None,
        "--strict",
        "-s",
        help="Treat warnings as errors. The score gate is controlled exclusively by --fail-under.",
    ),
    output_format: str = typer.Option(
        "text", "--format", "-f", help="Output format: text or json."
    ),
    save: bool = typer.Option(False, "--save", help="Save score snapshot to .zenzic-score.json."),
    fail_under: int = typer.Option(
        0, "--fail-under", help="Exit non-zero if score is below this threshold (0 = disabled)."
    ),
    stamp: bool = typer.Option(
        False,
        "--stamp",
        help="Update the score badge inline in files listed in badge_stamp_files.",
    ),
    check_stamp: bool = typer.Option(
        False,
        "--check-stamp",
        help=(
            "Verify that badge_stamp_files contain the current score URL. "
            "Exit 1 if any badge is stale. Mutually exclusive with --stamp."
        ),
    ),
    no_header: bool = typer.Option(
        False,
        "--no-header",
        help="Suppress the Zenzic banner. Use in CI pipelines where check all already printed it.",
    ),
) -> None:
    """Compute a 0–100 documentation quality score across all checks."""
    # CEO-056 "Universal Path Awareness": derive repo_root from the explicit
    # target path so that `zenzic score ../project-B` loads project-B's config.
    _search_from: Path | None = None
    if path is not None:
        _pre = Path(path).resolve()
        _search_from = _pre.parent if _pre.is_file() else _pre
    try:
        repo_root = find_repo_root(search_from=_search_from)
        config, _ = ZenzicConfig.load(repo_root)
    except (RuntimeError, ConfigurationError) as exc:
        typer.echo(f"ERROR: {exc}", err=True)
        raise typer.Exit(1) from exc
    docs_root = (repo_root / config.docs_dir).resolve()
    # CEO-043: sovereign sandbox — if docs_root escapes repo_root, adopt it as root.
    try:
        docs_root.relative_to(repo_root)
    except ValueError:
        repo_root = docs_root

    if stamp and check_stamp:
        _shared.stderr_console.print(
            "[red]ERROR:[/] --stamp and --check-stamp are mutually exclusive."
        )
        raise typer.Exit(1)

    if output_format != "json" and not no_header and not check_stamp:
        from zenzic import __version__

        _shared._ui.print_header(__version__)
        if path is not None:
            try:
                _hint = str(docs_root.relative_to(Path.cwd()))
            except ValueError:
                _hint = str(docs_root)
            _shared.console.print(f"[{ZenzicPalette.DIM}]  Scoring: {_hint}[/]")
        _shared.console.print()

    exclusion_mgr = _shared._build_exclusion_manager(config, repo_root, docs_root)
    report = _run_all_checks(repo_root, docs_root, config, exclusion_mgr, strict=config.strict)

    effective_threshold = fail_under if fail_under > 0 else config.fail_under

    if save:
        report.threshold = effective_threshold
        snapshot_path = save_snapshot(repo_root, report)
        _shared.console.print(f"[{ZenzicPalette.DIM}]Snapshot saved to {snapshot_path}[/]")

    if output_format == "json" and not check_stamp:
        print(json.dumps(report.to_dict(), indent=2))
    elif not check_stamp:
        if report.score >= 80:
            score_style = ZenzicPalette.STYLE_OK
        elif report.score >= 50:
            score_style = "bold yellow"
        else:
            score_style = ZenzicPalette.STYLE_ERR

        score_summary = Text.from_markup(
            f"{emoji('sparkles')} "
            f"[bold {ZenzicPalette.SUCCESS}]Quality Score:[/bold {ZenzicPalette.SUCCESS}]"
            f" [{score_style}]{report.score}/100[/{score_style}]\n"
        )

        table = Table(
            box=box.ROUNDED,
            title="[bold]Quality Breakdown[/]",
            title_style=ZenzicPalette.DIM,
            border_style=ZenzicPalette.DIM,
            show_lines=False,
            pad_edge=True,
            padding=(0, 1),
        )
        table.add_column(emoji("dot"), justify="center", width=4, no_wrap=True)
        table.add_column("Category", min_width=14, style="bold")
        table.add_column("Issues", justify="right")
        table.add_column("Weight", justify="right", style=ZenzicPalette.DIM)
        table.add_column("Raw Pts", justify="right", style=ZenzicPalette.DIM)
        table.add_column("Applied Pts", justify="right")

        for cat in report.categories:
            if cat.issues == 0:
                status_icon = f"[green]{emoji('check')}[/]"
                issue_display = f"[green]{cat.issues}[/]"
            else:
                status_icon = f"[red]{emoji('cross')}[/]"
                issue_display = f"[red]{cat.issues}[/]"
            raw_pts = round(cat.raw_penalty)
            raw_display = f"-{raw_pts}" if raw_pts > 0 else "0"
            applied_penalty = round(cat.weight * 100 - cat.contribution * 100)
            applied_display = f"-{applied_penalty}" if applied_penalty > 0 else "0"
            capped_suffix = " [yellow](CAPPED)[/yellow]" if cat.is_capped else ""
            table.add_row(
                status_icon,
                cat.name,
                issue_display,
                f"{cat.weight:.0%}",
                raw_display,
                f"{applied_display}{capped_suffix}",
            )

        subtotal = sum(round(c.contribution * 100) for c in report.categories)
        table.add_section()
        table.add_row(
            "",
            "[dim]Σ Subtotal[/dim]",
            "",
            "",
            "",
            f"[bold]{subtotal}[/bold]",
        )

        _shared.console.print(score_summary)
        _shared.console.print(table)

        gravity_loss = subtotal - (report.score + report.suppression_debt_pts)
        if gravity_loss > 0:
            _shared.console.print(
                f"  [yellow]![/] [bold]Gravity Cap Enforcement (Brand = 0):[/]"
                f" [red]-{gravity_loss} pts[/]"
            )
        debt_pts = report.suppression_debt_pts
        debt_style = "red" if debt_pts > 0 else "dim"
        debt_sign = "-" if debt_pts > 0 else ""
        _shared.console.print(
            f"  [yellow]![/] [bold]Technical Debt"
            f" ({report.suppression_count} suppressions):[/]"
            f" [{debt_style}]{debt_sign}{debt_pts} pts[/{debt_style}]"
        )
        _shared.console.print(
            f"  [dim]=[/dim] [bold]Final Quality Score[/bold]"
            f" [{score_style}]{report.score} / 100[/{score_style}]"
        )

        if report.score == 100:
            from rich.console import Group

            _shared.console.print()
            _shared.console.print(
                Group(
                    Text.from_markup(
                        f"[bold {ZenzicPalette.BRAND}]{emoji('check')} Analysis complete[/]"
                    ),
                    Text(),
                    Text.from_markup(
                        f"[{ZenzicPalette.SUCCESS}]{emoji('check')} Every check passed \u2014 "
                        f"documentation integrity verified.[/{ZenzicPalette.SUCCESS}]"
                    ),
                )
            )

    if stamp:
        _eff = fail_under if fail_under > 0 else config.fail_under
        score_url = _badge_url(report.score, _eff, report.security_override)
        audit_ok = (
            not report.security_override
            and report.score >= _eff
            and report.suppression_count <= report.suppression_cap
        )
        audit_url = _audit_badge_url(audit_ok)
        found_any = False
        for rel in config.project_metadata.badge_stamp_files:
            p = Path(rel)
            if not p.exists():
                continue
            content = p.read_text(encoding="utf-8")
            has_score_marker = _SCORE_STAMP_MARKER in content
            has_audit_marker = _AUDIT_STAMP_MARKER in content
            if not has_score_marker and not has_audit_marker:
                continue
            found_any = True
            changed_score = False
            changed_audit = False
            if has_score_marker:
                changed_score = _stamp_file(p, _SCORE_STAMP_MARKER, score_url)
            if has_audit_marker:
                changed_audit = _stamp_file(p, _AUDIT_STAMP_MARKER, audit_url)
            if changed_score or changed_audit:
                _shared.console.print(f"[dim]Badge stamped → {p}[/]")
        if not found_any:
            _shared.stderr_console.print(
                "[red]--stamp: no recognized stamp markers found in any configured file "
                f"({_SCORE_STAMP_MARKER!r}, {_AUDIT_STAMP_MARKER!r})[/]",
            )
            raise typer.Exit(1)

    if check_stamp:
        _eff = fail_under if fail_under > 0 else config.fail_under
        score_url = _badge_url(report.score, _eff, report.security_override)
        audit_ok = (
            not report.security_override
            and report.score >= _eff
            and report.suppression_count <= report.suppression_cap
        )
        audit_url = _audit_badge_url(audit_ok)
        outdated: list[tuple[Path, str]] = []
        for rel in config.project_metadata.badge_stamp_files:
            p = Path(rel)
            if not _check_stamp_file(p, _SCORE_STAMP_MARKER, score_url):
                outdated.append((p, "score"))
            if not _check_stamp_file(p, _AUDIT_STAMP_MARKER, audit_url):
                outdated.append((p, "audit"))
        if outdated:
            for p, badge_type in outdated:
                _shared.console.print(
                    f"[red][FAILED][/red] Badge ({badge_type}) in [bold]{p}[/] is stale. "
                    "Run 'zenzic score --stamp' locally and commit the result."
                )
            raise typer.Exit(1)
        _shared.console.print(f"[{ZenzicPalette.SUCCESS}][SUCCESS] All badges are current.[/]")

    if effective_threshold > 0 and report.score < effective_threshold:
        _shared.console.print(
            f"\n[red]FAILED:[/] score {report.score} is below threshold {effective_threshold}."
        )
        raise typer.Exit(1)

    if report.suppression_count > report.suppression_cap:
        _shared.console.print(
            f"\n[red]FAILED:[/] suppression cap exceeded "
            f"({report.suppression_count}/{report.suppression_cap}). "
            f"Update governance.suppression_cap in .zenzic.toml if intentional."
        )
        raise typer.Exit(1)

    if not check_stamp:
        _shared.print_footer_hint("score", output_format=output_format)


# ── diff command ──────────────────────────────────────────────────────────────


def diff(
    path: str | None = typer.Argument(
        None,
        help="Repository root or docs directory to compare (default: configured docs directory).",
        show_default=False,
    ),
    strict: bool | None = typer.Option(
        None,
        "--strict",
        "-s",
        help="Treat warnings as errors. The score gate is controlled exclusively by --fail-under.",
    ),
    output_format: str = typer.Option(
        "text", "--format", "-f", help="Output format: text or json."
    ),
    threshold: int = typer.Option(
        0,
        "--threshold",
        help="Exit non-zero only if score dropped by more than this many points (0 = any drop).",
    ),
    base: str | None = typer.Option(
        None,
        "--base",
        help="Path to a JSON report file to use as baseline instead of the saved snapshot.",
        show_default=False,
    ),
) -> None:
    """Compare current documentation score against the saved snapshot.

    Requires a previous snapshot created by ``zenzic score --save``,
    or an explicit JSON report passed via ``--base <file>``.
    Exits non-zero if the score dropped by more than ``--threshold`` points.
    """
    # CEO-056 "Universal Path Awareness": derive repo_root from the explicit
    # target path so that `zenzic diff ../project-B` loads project-B's config
    # and compares against project-B's snapshot (total sovereignty).
    _search_from: Path | None = None
    if path is not None:
        _pre = Path(path).resolve()
        _search_from = _pre.parent if _pre.is_file() else _pre
    try:
        repo_root = find_repo_root(search_from=_search_from)
        config, _ = ZenzicConfig.load(repo_root)
    except (RuntimeError, ConfigurationError) as exc:
        typer.echo(f"ERROR: {exc}", err=True)
        raise typer.Exit(1) from exc
    docs_root = (repo_root / config.docs_dir).resolve()
    # CEO-043: sovereign sandbox
    try:
        docs_root.relative_to(repo_root)
    except ValueError:
        repo_root = docs_root
    exclusion_mgr = _shared._build_exclusion_manager(config, repo_root, docs_root)

    baseline: ScoreReport | None = None
    try:
        if base is not None:
            # Load baseline from an explicit JSON report file (--base <file>).
            try:
                base_path = Path(base).resolve()
                raw = json.loads(base_path.read_text(encoding="utf-8"))
                baseline_categories = [CategoryScore(**c) for c in raw.get("categories", [])]
                baseline = ScoreReport(
                    score=int(raw.get("score", 0)),
                    threshold=int(raw.get("threshold", 0)),
                    categories=baseline_categories,
                )
            except (OSError, json.JSONDecodeError, TypeError, KeyError) as exc:
                typer.echo(f"ERROR: Cannot read baseline file '{base}': {exc}", err=True)
                raise typer.Exit(1) from exc
        else:
            baseline = load_snapshot(repo_root)
    except ConfigurationError as exc:
        _shared.get_ui().print_exception_alert(str(exc))
        raise typer.Exit(1) from exc
    if baseline is None:
        _shared.console.print(
            "[yellow]WARNING:[/] no snapshot found. "
            "Run 'zenzic score --save' first, or pass a JSON report with --base."
        )
        raise typer.Exit(1)

    current = _run_all_checks(repo_root, docs_root, config, exclusion_mgr, strict=config.strict)
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
        from zenzic import __version__

        delta_colour = "green" if delta >= 0 else "red"
        sign = "+" if delta >= 0 else ""
        diff_table = Table(
            box=box.ROUNDED,
            border_style=ZenzicPalette.DIM,
            show_header=True,
            header_style=ZenzicPalette.STYLE_BRAND,
            pad_edge=True,
            padding=(0, 1),
        )
        diff_table.add_column("Category", style="bold", min_width=14)
        diff_table.add_column("Baseline", justify="right")
        diff_table.add_column("Current", justify="right")
        diff_table.add_column("Delta", justify="right")
        for cat in current.categories:
            base_cat = next((b for b in baseline.categories if b.name == cat.name), None)
            base_issues = base_cat.issues if base_cat else 0
            issue_delta = cat.issues - base_issues
            sign_i = "+" if issue_delta > 0 else ""
            colour = "red" if issue_delta > 0 else "green" if issue_delta < 0 else "dim"
            diff_table.add_row(
                cat.name,
                str(base_issues),
                str(cat.issues),
                f"[{colour}]{sign_i}{issue_delta}[/]",
            )
        body = Text.from_markup(
            f"  Baseline: [bold]{baseline.score}/100[/]   "
            f"Current: [bold {delta_colour}]{current.score}/100[/]   "
            f"Delta: [{delta_colour}]{sign}{delta}[/]\n"
        )
        _shared.console.print()
        _shared._ui.print_header(__version__)
        if path is not None:
            try:
                _hint = str(docs_root.relative_to(Path.cwd()))
            except ValueError:
                _hint = str(docs_root)
            _shared.console.print(f"[{ZenzicPalette.DIM}]  Comparing: {_hint}[/]")
        _shared.console.print()
        _shared.console.print(body)
        _shared.console.print(diff_table)
        _shared.console.print()

    dropped = -delta
    if dropped > threshold:
        _shared.console.print(
            f"[red]REGRESSION:[/] score dropped by {dropped} point(s) (threshold: {threshold})."
        )
        raise typer.Exit(1)

    _shared.print_footer_hint("diff", output_format=output_format)


# ── explain command ────────────────────────────────────────────────────────────


def explain(
    rule_id: str = typer.Argument(
        ...,
        help="Rule code to explain (e.g. Z101, Z601).",
        metavar="RULE_ID",
    ),
    path: str | None = typer.Option(
        None,
        "--path",
        help="Project root to resolve config genealogy (default: current working directory).",
        show_default=False,
    ),
) -> None:
    """Show rule metadata, scoring weight, and config genealogy for a rule code.

    Displays which config file (Default / Global TOML / Local TOML) controls
    the rule, and whether it is currently enabled or suppressed.
    """
    from rich.table import Table as RTable

    from zenzic import __version__
    from zenzic.core.codes import (
        CODE_DESCRIPTIONS,
        CODE_NAMES,
        CODE_SARIF_LEVELS,
        NON_SUPPRESSIBLE_CODES,
    )
    from zenzic.core.scorer import _CODE_CATEGORY, _CODE_PENALTY, _WEIGHTS

    rule_id = rule_id.upper()

    _shared._ui.print_header(__version__)
    _shared.console.print()

    # ── Rule metadata ─────────────────────────────────────────────────────────
    name = CODE_NAMES.get(rule_id, "UNKNOWN")
    description = CODE_DESCRIPTIONS.get(rule_id, "No description available.")
    severity = CODE_SARIF_LEVELS.get(rule_id, "unknown")
    bucket = _CODE_CATEGORY.get(rule_id, "—")
    penalty = _CODE_PENALTY.get(rule_id)
    weight = _WEIGHTS.get(bucket, 0.0)
    is_security = rule_id in NON_SUPPRESSIBLE_CODES

    meta_table = RTable.grid(padding=(0, 2))
    meta_table.add_column(style=ZenzicPalette.DIM, min_width=20)
    meta_table.add_column()
    meta_table.add_row("Rule", f"[bold cyan]{rule_id}[/] — {name}")
    meta_table.add_row("Description", description)
    meta_table.add_row("Severity", f"[{'red' if severity == 'error' else 'yellow'}]{severity}[/]")
    if is_security:
        meta_table.add_row(
            "Scoring Tier", "[bold red]SECURITY GATE[/] — score collapses to 0 on any occurrence"
        )
    elif bucket != "—":
        cap = weight * 100
        penalty_str = f"{penalty:.1f} pt/occurrence" if penalty else "not penalised"
        meta_table.add_row("Scoring Tier", f"{bucket} (weight {weight:.0%}, cap {cap:.0f} pts)")
        meta_table.add_row("Penalty", penalty_str)
    else:
        meta_table.add_row("Scoring Tier", f"[{ZenzicPalette.DIM}]not included in DQS[/]")

    _shared.console.print(meta_table)
    _shared.console.print()

    # ── Config genealogy ──────────────────────────────────────────────────────
    _search_from: Path | None = None
    if path is not None:
        _search_from = Path(path).resolve()

    genealogy_rows: list[tuple[str, str, str]] = []
    try:
        repo_root = find_repo_root(search_from=_search_from)
        config, _ = ZenzicConfig.load(repo_root)

        # Rule-specific config keys to inspect
        _RULE_CONFIG_MAP: dict[str, list[tuple[str, str]]] = {
            "Z601": [("governance.brand_obsolescence", "brand_obsolescence list")],
            "Z204": [("governance.forbidden_patterns", "forbidden_patterns list")],
            "Z501": [("placeholder_patterns", "placeholder_patterns list")],
            "Z502": [("short_content_threshold", "short_content_threshold")],
            "Z402": [("excluded_dirs", "excluded_dirs (removes pages from nav scope)")],
        }
        # Global: .zenzic.toml presence
        global_toml = repo_root / ".zenzic.toml"
        local_toml = repo_root / ".zenzic.local.toml"

        genealogy_rows.append(
            (
                "Default",
                "[green]Active[/]",
                "Built-in Zenzic defaults apply unless overridden.",
            )
        )
        genealogy_rows.append(
            (
                f"Global ({global_toml.name})",
                "[green]Loaded[/]"
                if global_toml.is_file()
                else f"[{ZenzicPalette.DIM}]Not found[/]",
                str(global_toml) if global_toml.is_file() else "Using pyproject.toml or defaults.",
            )
        )
        genealogy_rows.append(
            (
                "Local (.zenzic.local.toml)",
                "[green]Loaded[/]"
                if local_toml.is_file()
                else f"[{ZenzicPalette.DIM}]Not present[/]",
                str(local_toml)
                if local_toml.is_file()
                else "No local overlay — shared config applies.",
            )
        )

        # Rule-specific config notes
        if rule_id in _RULE_CONFIG_MAP:
            for key_path, label in _RULE_CONFIG_MAP[rule_id]:
                parts = key_path.split(".")
                val: object = config
                for part in parts:
                    val = getattr(val, part, None)
                    if val is None:
                        break
                if isinstance(val, list):
                    if val:
                        genealogy_rows.append(
                            (
                                f"  {label}",
                                f"[yellow]{len(val)} entries[/]",
                                ", ".join(f'"{v}"' for v in val[:3])
                                + (" …" if len(val) > 3 else ""),
                            )
                        )
                    else:
                        genealogy_rows.append(
                            (
                                f"  {label}",
                                f"[{ZenzicPalette.DIM}]empty[/]",
                                "Rule fires on default patterns.",
                            )
                        )

        # Per-file suppression status for this rule
        suppressed_patterns = [
            pat for pat, codes in config.governance.per_file_ignores.items() if rule_id in codes
        ]
        if suppressed_patterns:
            genealogy_rows.append(
                (
                    "  Per-file Ignores",
                    "[yellow]Suppressed[/]",
                    "Via governance.per_file_ignores for: "
                    + ", ".join(f'"{p}"' for p in suppressed_patterns[:3])
                    + (" …" if len(suppressed_patterns) > 3 else ""),
                )
            )
        else:
            genealogy_rows.append(
                (
                    "  Per-file Ignores",
                    "[green]Active[/]",
                    "Rule is not suppressed in any file glob.",
                )
            )

    except (RuntimeError, ConfigurationError):
        genealogy_rows.append(
            (
                "Config",
                f"[{ZenzicPalette.DIM}]not resolved[/]",
                "Run from a project root to see genealogy.",
            )
        )

    g_table = RTable(
        show_header=True, header_style="bold", box=None, pad_edge=False, padding=(0, 2)
    )
    g_table.add_column("Layer", style=ZenzicPalette.DIM, min_width=30)
    g_table.add_column("Status", min_width=14)
    g_table.add_column("Detail")
    for layer, status, detail in genealogy_rows:
        g_table.add_row(layer, status, detail)

    _shared.console.print("[bold]Config Genealogy[/]")
    _shared.console.print(g_table)
    _shared.console.print()
    _shared.print_footer_hint("explain")


# ── init command ──────────────────────────────────────────────────────────────


def init(
    ctx: typer.Context,
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
        help=(
            "Overwrite an existing plugin scaffold when used with --plugin. "
            "Not supported for configuration initialization."
        ),
    ),
    pyproject: bool = typer.Option(
        False,
        "--pyproject",
        help="Write configuration into pyproject.toml [tool.zenzic] instead of .zenzic.toml.",
    ),
    local: bool = typer.Option(
        False,
        "--local",
        help="Scaffold only .zenzic.local.toml (machine-local overlay). Skips main config creation.",
    ),
    path: str | None = typer.Argument(
        None,
        help="Directory to initialize (default: current project root or current working directory).",
        show_default=False,
    ),
) -> None:
    """Scaffold a Zenzic configuration in the current project.

    By default creates ``.zenzic.toml``.  If ``pyproject.toml`` exists in the
    project root Zenzic will ask whether to embed the configuration there
    as a ``[tool.zenzic]`` table instead.  Use ``--pyproject`` to skip the
    prompt and write directly into ``pyproject.toml``.

    Pass PATH to initialize a remote directory (e.g. ``zenzic init ../new-project``).
    The directory is created if it does not exist.

    Performs engine auto-detection: if ``mkdocs.yml`` is present the generated
    file pre-sets ``engine = "mkdocs"``; if ``zensical.toml`` is present it
    pre-sets ``engine = "zensical"``.  Otherwise the ``[build_context]`` block
    is omitted and the standalone (engine-agnostic) defaults apply.

    Use ``--local`` to scaffold only ``.zenzic.local.toml`` (machine-local overlay)
    without touching the shared configuration.  Ideal for contributors who clone a
    repo that already has ``.zenzic.toml`` committed.
    """
    from zenzic import __version__

    _shared._ui.print_header(__version__)
    _shared.console.print()
    # CEO-060: when an explicit target is given, treat it as the repo root.
    if path is not None:
        repo_root = Path(path).resolve()
        repo_root.mkdir(parents=True, exist_ok=True)
        try:
            _hint = str(repo_root.relative_to(Path.cwd()))
        except ValueError:
            _hint = str(repo_root)
        _shared.console.print(f"[{ZenzicPalette.DIM}]  Target: {_hint}[/]")
    else:
        repo_root = find_repo_root(fallback_to_cwd=True)

    if plugin is not None:
        conflicting = [
            flag for flag, val in [("--local", local), ("--pyproject", pyproject)] if val
        ]
        if conflicting:
            typer.echo(
                f"ERROR: --plugin cannot be combined with {', '.join(conflicting)}. "
                "These flags target different init modes.",
                err=True,
            )
            raise typer.Exit(2)
        _scaffold_plugin(repo_root, plugin, force)
        return

    if local:
        if pyproject:
            typer.echo(
                "ERROR: --local cannot be combined with --pyproject. "
                "--local scaffolds only the machine-local overlay.",
                err=True,
            )
            raise typer.Exit(1)
        _scaffold_local_toml(repo_root, discovered_name=_discover_project_name(repo_root))
        _shared.print_footer_hint("init")
        return

    if force:
        _shared.console.print(
            "[red]✘ ERROR:[/] --force is not supported for configuration initialization. "
            "Manual editing is required to modify existing settings."
        )
        raise typer.Exit(1)

    config_path = repo_root / ".zenzic.toml"
    local_path = repo_root / ".zenzic.local.toml"
    # Atomic guard for the dual-file init contract: do not allow partial re-init.
    if config_path.exists():
        _raise_existing_configuration_error(config_path)
    if local_path.exists():
        _raise_existing_configuration_error(local_path)

    use_pyproject = pyproject
    pyproject_path = repo_root / "pyproject.toml"

    if not use_pyproject and pyproject_path.is_file():
        use_pyproject = typer.confirm(
            "Found pyproject.toml. Embed Zenzic config there as [tool.zenzic]?",
            default=False,
        )

    if use_pyproject:
        _init_pyproject(repo_root, pyproject_path)
    else:
        _init_standalone(repo_root)

    # Local Sovereignty: always scaffold machine-local overlay.
    _scaffold_local_toml(repo_root, discovered_name=_discover_project_name(repo_root))
    _shared.print_footer_hint("init")


def _is_editable_install() -> bool:
    """Detect editable (development) install via PEP 610 direct_url.json.

    Mirrors the logic of ``_is_dev_mode()`` in ``main.py`` as a local helper
    to avoid circular imports between ``_standalone`` and ``main`` (CEO-275).
    Returns True only when Zenzic is installed with ``pip install -e .`` or
    ``uv sync`` in development mode.
    """
    import importlib.metadata
    import json

    try:
        dist = importlib.metadata.distribution("zenzic")
        direct_url_content = dist.read_text("direct_url.json")
        if not direct_url_content:
            return False
        data = json.loads(direct_url_content)
        return "dir_info" in data and data["dir_info"].get("editable", False)
    except Exception:
        return False


def _raise_existing_configuration_error(existing_path: Path) -> None:
    """Abort init when a pre-existing configuration asset is found."""
    _shared.console.print(
        "[red]✘ ERROR:[/] Configuration already exists at "
        f"[{ZenzicPalette.DIM}]{existing_path}[/]. "
        "Manual editing is required to modify existing settings."
    )
    raise typer.Exit(1)


def _scaffold_local_toml(repo_root: Path, *, discovered_name: str | None = None) -> None:
    """Create a didactic ``.zenzic.local.toml`` Local Sovereignty template.

    Idempotent for content creation, but always ensures Git protection:
    when the target is a Git repository, ``.zenzic.local.toml`` is enforced in
    ``.gitignore`` (created if missing) to prevent accidental commits.
    """
    from rich.panel import Panel

    local_toml = repo_root / ".zenzic.local.toml"
    created_now = False

    if not local_toml.exists():
        local_toml.write_text(LOCAL_TOML_TEMPLATE, encoding="utf-8")
        created_now = True

    # Ensure local overlay is ignored in Git repositories.
    is_git_repo = (repo_root / ".git").exists()
    gitignore = repo_root / ".gitignore"
    gitignore_line = ""
    if is_git_repo:
        existing = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
        if ".zenzic.local.toml" not in existing:
            separator = "" if (not existing or existing.endswith("\n")) else "\n"
            gitignore.write_text(existing + separator + ".zenzic.local.toml\n", encoding="utf-8")
            gitignore_line = (
                "[yellow]🛡️ Security Note:[/] Added [bold].zenzic.local.toml[/] "
                "to your [bold].gitignore[/] to preserve local sovereignty.\n"
            )
        else:
            gitignore_line = (
                f"[{ZenzicPalette.DIM}].gitignore already protects .zenzic.local.toml.[/]\n"
            )
    else:
        gitignore_line = (
            "[yellow]⚠[/] No Git repository detected. Keep .zenzic.local.toml private.\n"
        )

    _shared.console.print(
        Panel(
            (
                "[green]✔[/] [bold].zenzic.local.toml[/] created (Local Sovereignty overlay).\n"
                if created_now
                else f"[{ZenzicPalette.DIM}].zenzic.local.toml already exists — preserved.[/]\n"
            )
            + gitignore_line
            + "\nEdit local overrides safely: this file wins over shared config "
            "only on your machine.",
            title=f"[bold]{discovered_name or 'Zenzic'} Local Sandbox[/]",
            border_style="cyan",
        )
    )


def _detect_init_engine(repo_root: Path) -> str:
    """Auto-detect the documentation engine from config files at *repo_root*.

    Delegates to :func:`~zenzic.core.adapters._factory.discover_engine` so
    the detection priority is identical to the runtime engine resolution
    (CEO-221: single source of truth for engine detection).
    Always returns a concrete engine name — ``"standalone"`` when no engine
    config file is found.
    """
    from zenzic.core.adapters._factory import discover_engine

    return discover_engine(repo_root)


def _discover_project_name(repo_root: Path) -> str | None:
    """Discover project name from pyproject.toml or package.json when available."""
    pyproject = repo_root / "pyproject.toml"
    if pyproject.is_file():
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            project = data.get("project")
            if isinstance(project, dict):
                name = project.get("name")
                if isinstance(name, str) and name.strip():
                    return name.strip()
        except Exception:
            pass

    package_json = repo_root / "package.json"
    if package_json.is_file():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
            name = data.get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()
        except Exception:
            pass

    return None


def _build_governance_ready_toml(*, engine: str, discovered_name: str | None) -> str:
    """Build governance configuration template with didactic comments."""
    hint_name = discovered_name or "My Awesome App"
    return GLOBAL_TOML_TEMPLATE.format(engine=engine, hint_name=hint_name)


def _init_standalone(repo_root: Path) -> None:
    """Create a standalone ``.zenzic.toml`` configuration file."""
    config_path = repo_root / ".zenzic.toml"
    local_path = repo_root / ".zenzic.local.toml"

    if config_path.exists():
        _raise_existing_configuration_error(config_path)
    if local_path.exists():
        _raise_existing_configuration_error(local_path)

    detected_engine = _detect_init_engine(repo_root)
    discovered_name = _discover_project_name(repo_root)
    toml_content = _build_governance_ready_toml(
        engine=detected_engine,
        discovered_name=discovered_name,
    )

    config_path.write_text(toml_content, encoding="utf-8")

    _shared.console.print(
        Panel(
            f"[green]✔[/] [bold].zenzic.toml created.[/]\n"
            f"[yellow]💡[/] [bold]Auto-discovery:[/] Engine pre-set to "
            f"[bold cyan]{detected_engine}[/].\n\n"
            "Run [bold cyan]zenzic check all[/] to verify your documentation.",
            title="[bold]Zenzic Init[/]",
            border_style="green",
        )
    )


def _init_pyproject(repo_root: Path, pyproject_path: Path) -> None:
    """Append a ``[tool.zenzic]`` section to an existing ``pyproject.toml``."""
    if not pyproject_path.is_file():
        _shared.console.print(
            "[red]ERROR:[/] No [bold]pyproject.toml[/] found at "
            f"[{ZenzicPalette.DIM}]{pyproject_path}[/]\n"
            "Use [bold cyan]zenzic init[/] without --pyproject to create a standalone .zenzic.toml."
        )
        raise typer.Exit(1)

    existing = pyproject_path.read_text(encoding="utf-8")

    if "[tool.zenzic]" in existing:
        _raise_existing_configuration_error(pyproject_path)

    detected_engine = _detect_init_engine(repo_root)

    engine_section = (
        "\n[tool.zenzic.build_context]\n"
        f'engine = "{detected_engine}"   # Pre-aligned via engine auto-discovery\n'
        'base_url = "/"\n'
        'default_locale = "en"\n'
    )

    section = (
        "\n[tool.zenzic]\n"
        "# See https://zenzic.dev/docs/reference/configuration/ for full reference.\n"
        'docs_dir = "docs"\n'
        "fail_under = 100  # Strict gate: fail if quality score < 100%\n"
        "strict = true     # Promote all warnings to blocking errors\n"
        "# excluded_dirs = []\n"
        "\n"
        "[tool.zenzic.governance]\n"
        "suppression_cap = 30\n"
        "suppression_cap_fail_hard = true\n"
        "brand_obsolescence = []\n"
        "# [tool.zenzic.governance.per_file_ignores]\n"
        "# [tool.zenzic.governance.directory_policies]\n"
        "\n"
        "# Uncomment to enable i18n parity checks:\n"
        "# [tool.zenzic.i18n]\n"
        "# enabled = true\n"
        '# base_lang = "en"\n'
        '# base_source = "docs"\n'
        "# [tool.zenzic.i18n.targets]\n"
        '# it = "i18n/it/docusaurus-plugin-content-docs/current"\n'
        "\n"
        "# Uncomment to add project-specific lint rules:\n"
        "# [[tool.zenzic.custom_rules]]\n"
        '# id      = "ZZ-NOCLICKHERE"\n'
        '# pattern = "(?i)\\\\bclick here\\\\b"\n'
        '# message = "Avoid generic link text."\n'
    ) + engine_section

    pyproject_path.write_text(existing.rstrip("\n") + "\n" + section, encoding="utf-8")

    _shared.console.print(
        Panel(
            f"[green]✔[/] [bold][tool.zenzic] added to "
            f"{pyproject_path.relative_to(repo_root)}.[/]\n"
            f"[yellow]💡[/] [bold]Auto-discovery:[/] Engine pre-set to "
            f"[bold cyan]{detected_engine}[/].\n\n"
            "Edit the section, adjust directories, then run "
            "[bold cyan]zenzic check all[/].",
            title="[bold]Zenzic Init[/]",
            border_style="green",
        )
    )


def _scaffold_plugin(repo_root: Path, plugin_name: str, force: bool) -> None:
    """Create a ready-to-edit plugin package scaffold."""
    raw = plugin_name.strip()
    if not raw:
        _shared.console.print("[red]ERROR:[/] --plugin requires a non-empty name.")
        raise typer.Exit(1)

    project_slug = _SLUG_NONWORD_RE.sub("-", raw.lower()).strip("-")
    project_slug = _SLUG_MULTI_DASH_RE.sub("-", project_slug)
    if not project_slug:
        _shared.console.print(
            "[red]ERROR:[/] Invalid plugin name. Use letters, numbers, and optional dashes."
        )
        raise typer.Exit(1)

    module_name = project_slug.replace("-", "_")
    class_name = "".join(part.capitalize() for part in project_slug.split("-")) + "Rule"
    rule_prefix = "".join(ch for ch in project_slug.upper() if ch.isalnum())[:8] or "PLUGIN"
    rule_id = f"{rule_prefix}-001"

    target = repo_root / project_slug
    if target.exists() and not force:
        _shared.console.print(
            f"[yellow]WARNING:[/] [bold]{project_slug}[/] already exists at "
            f"[{ZenzicPalette.DIM}]{target}[/]\nUse [bold cyan]--force[/] to overwrite scaffold files."
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
dependencies = ["zenzic>=0.8.1"]

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
zenzic inspect capabilities
```

Enable this plugin in a target project's `.zenzic.toml`:

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
    (target / ".zenzic.toml").write_text(
        '# .zenzic.toml generated by plugin scaffold\n# docs_dir defaults to "docs"\n',
        encoding="utf-8",
    )
    (src_pkg / "__init__.py").write_text(
        f'"""{project_slug} plugin package."""\n',
        encoding="utf-8",
    )
    (src_pkg / "rules.py").write_text(rules_py, encoding="utf-8")
    (docs_dir / "index.md").write_text(docs_index, encoding="utf-8")

    _shared.console.print(
        f"\n[green]Created plugin scaffold[/] [bold]{project_slug}[/]\n"
        f"  Path: [{ZenzicPalette.DIM}]{target.relative_to(repo_root)}[/]\n"
        f"  Entry-point: [bold]{project_slug}[/] -> [{ZenzicPalette.DIM}]{module_name}.rules:{class_name}[/]\n"
        "\nNext steps:\n"
        f"  1. [bold]cd {project_slug}[/]\n"
        "  2. [bold]uv pip install -e .[/]\n"
        "  3. [bold]zenzic inspect capabilities[/]"
    )
