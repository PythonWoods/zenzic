# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Standalone commands: score, diff, init — and their private helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path

import typer
from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from zenzic.core.codes import normalize as _normalize_code
from zenzic.core.exceptions import ConfigurationError
from zenzic.core.exclusion import LayeredExclusionManager
from zenzic.core.scanner import (
    find_orphans,
    find_placeholders,
    find_repo_root,
    find_unused_assets,
    scan_docs_references,
)
from zenzic.core.scorer import ScoreReport, compute_score, load_snapshot, save_snapshot
from zenzic.core.ui import SentinelPalette, emoji
from zenzic.core.validator import check_nav_contract, validate_links, validate_snippets
from zenzic.models.config import ZenzicConfig

from . import _shared


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
    and passes it to the Quartz Penalty Scorer (CEO-163).
    """
    from zenzic.core.adapters import get_adapter

    adapter = get_adapter(config.build_context, docs_root, repo_root)
    locale_roots: list[tuple[Path, str]] | None = None
    if hasattr(adapter, "get_locale_source_roots"):
        _roots = adapter.get_locale_source_roots(repo_root)
        locale_roots = _roots if _roots else None

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

    # Collect rule findings (Z107, Z505, Z905) and security violations (Z201–Z203)
    # via the Two-Pass Reference Engine.
    ref_reports, _ = scan_docs_references(
        docs_root,
        exclusion_mgr,
        config=config,
        validate_links=False,
        locale_roots=locale_roots,
    )
    nav_errors = check_nav_contract(repo_root, exclusion_mgr)

    # ── Build findings_counts dict (Quartz Penalty Scorer, CEO-163) ───────────────
    findings_counts: dict[str, int] = {}

    # Link errors — split by Zxxx code derived from error_type
    for err in link_errors:
        code = _normalize_code(err.error_type)  # type: ignore[attr-defined]
        findings_counts[code] = findings_counts.get(code, 0) + 1

    # Core check aggregates
    findings_counts["Z402"] = findings_counts.get("Z402", 0) + len(orphans)
    findings_counts["Z503"] = findings_counts.get("Z503", 0) + len(snippet_errors)
    findings_counts["Z903"] = findings_counts.get("Z903", 0) + len(unused_assets)
    findings_counts["Z904"] = findings_counts.get("Z904", 0) + len(nav_errors)

    # Placeholder findings — Z501 (pattern) vs Z502 (short-content) split (CEO-171)
    for pf in placeholders:
        pcode = "Z502" if pf.issue == "short-content" else "Z501"
        findings_counts[pcode] = findings_counts.get(pcode, 0) + 1

    # Rule-engine findings: Z107, Z505, Z905 (rule_id already a Zxxx code)
    for r in ref_reports:
        for rule_f in r.rule_findings:
            findings_counts[rule_f.rule_id] = findings_counts.get(rule_f.rule_id, 0) + 1

    # Security violations (Z2xx) — any breach triggers score override
    security_violations = sum(len(r.security_findings) for r in ref_reports)
    if security_violations > 0:
        findings_counts["Z201"] = findings_counts.get("Z201", 0) + security_violations

    return compute_score(findings_counts)


# ── score command ─────────────────────────────────────────────────────────────


def score(
    path: str | None = typer.Argument(
        None,
        help="Project root or docs directory to score (default: configured docs_dir).",
        show_default=False,
    ),
    strict: bool | None = typer.Option(
        None,
        "--strict",
        "-s",
        help="Also validate external HTTP/HTTPS links (slower; requires network).",
    ),
    output_format: str = typer.Option(
        "text", "--format", "-f", help="Output format: text or json."
    ),
    save: bool = typer.Option(False, "--save", help="Save score snapshot to .zenzic-score.json."),
    fail_under: int = typer.Option(
        0, "--fail-under", help="Exit non-zero if score is below this threshold (0 = disabled)."
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

    if output_format != "json":
        from zenzic import __version__

        _shared._ui.print_header(__version__)
        if path is not None:
            try:
                _hint = str(docs_root.relative_to(Path.cwd()))
            except ValueError:
                _hint = str(docs_root)
            _shared.console.print(f"[dim]  Scoring: {_hint}[/]")
        _shared.console.print()

    exclusion_mgr = _shared._build_exclusion_manager(config, repo_root, docs_root)
    effective_strict = strict if strict is not None else config.strict
    report = _run_all_checks(repo_root, docs_root, config, exclusion_mgr, strict=effective_strict)

    effective_threshold = fail_under if fail_under > 0 else config.fail_under

    if save:
        report.threshold = effective_threshold
        snapshot_path = save_snapshot(repo_root, report)
        _shared.console.print(f"[dim]Snapshot saved to {snapshot_path}[/]")

    if output_format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        if report.score >= 80:
            score_style = SentinelPalette.STYLE_OK
        elif report.score >= 50:
            score_style = "bold yellow"
        else:
            score_style = SentinelPalette.STYLE_ERR

        score_summary = Text.from_markup(
            f"{emoji('sparkles')} "
            f"[bold {SentinelPalette.SUCCESS}]Quality Score:[/bold {SentinelPalette.SUCCESS}]"
            f" [{score_style}]{report.score}/100[/{score_style}]\n"
        )

        table = Table(
            box=box.ROUNDED,
            title="[bold]Quality Breakdown[/]",
            title_style=SentinelPalette.DIM,
            border_style=SentinelPalette.DIM,
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

        _shared.console.print(score_summary)
        _shared.console.print(table)

        if report.score == 100:
            from rich.console import Group

            _shared.console.print()
            _shared.console.print(
                Group(
                    Text.from_markup(
                        f"[bold {SentinelPalette.BRAND}]{emoji('shield')} SENTINEL SEAL[/]"
                    ),
                    Text(),
                    Text.from_markup(
                        f"[{SentinelPalette.SUCCESS}]{emoji('check')} Every check passed \u2014 "
                        f"documentation integrity verified.[/{SentinelPalette.SUCCESS}]"
                    ),
                )
            )

    if effective_threshold > 0 and report.score < effective_threshold:
        _shared.console.print(
            f"\n[red]FAILED:[/] score {report.score} is below threshold {effective_threshold}."
        )
        raise typer.Exit(1)


# ── diff command ──────────────────────────────────────────────────────────────


def diff(
    path: str | None = typer.Argument(
        None,
        help="Project root or docs directory to compare (default: configured docs_dir).",
        show_default=False,
    ),
    strict: bool | None = typer.Option(
        None,
        "--strict",
        "-s",
        help="Also validate external HTTP/HTTPS links (slower; requires network).",
    ),
    output_format: str = typer.Option(
        "text", "--format", "-f", help="Output format: text or json."
    ),
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
    effective_strict = strict if strict is not None else config.strict

    try:
        baseline = load_snapshot(repo_root)
    except ConfigurationError as exc:
        _shared.get_ui().print_exception_alert(str(exc))
        raise typer.Exit(1) from exc
    if baseline is None:
        _shared.console.print(
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
        from zenzic import __version__

        delta_colour = "green" if delta >= 0 else "red"
        sign = "+" if delta >= 0 else ""
        diff_table = Table(
            box=box.ROUNDED,
            border_style=SentinelPalette.DIM,
            show_header=True,
            header_style=SentinelPalette.STYLE_BRAND,
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
            _shared.console.print(f"[dim]  Comparing: {_hint}[/]")
        _shared.console.print()
        _shared.console.print(body)
        _shared.console.print(diff_table)
        _shared.console.print()

    dropped = -delta
    if dropped > threshold:
        _shared.console.print(
            f"\n[red]REGRESSION:[/] score dropped by {dropped} point(s) (threshold: {threshold})."
        )
        raise typer.Exit(1)


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
        help="Overwrite an existing zenzic.toml without prompting.",
    ),
    pyproject: bool = typer.Option(
        False,
        "--pyproject",
        help="Write configuration into pyproject.toml [tool.zenzic] instead of zenzic.toml.",
    ),
    dev: bool = typer.Option(
        False,
        "--dev",
        help=(
            "Also scaffold .zenzic.dev.toml (D002 Environmental Privacy Gate). "
            "Auto-enabled in editable installs (CEO-275)."
        ),
    ),
    path: str | None = typer.Argument(
        None,
        help="Directory to initialize (default: current project root or CWD).",
        show_default=False,
    ),
) -> None:
    """Scaffold a Zenzic configuration in the current project.

    By default creates ``zenzic.toml``.  If ``pyproject.toml`` exists in the
    project root Zenzic will ask whether to embed the configuration there
    as a ``[tool.zenzic]`` table instead.  Use ``--pyproject`` to skip the
    prompt and write directly into ``pyproject.toml``.

    Pass PATH to initialize a remote directory (e.g. ``zenzic init ../new-project``).
    The directory is created if it does not exist.

    Performs engine auto-detection: if ``mkdocs.yml`` is present the generated
    file pre-sets ``engine = "mkdocs"``; if ``zensical.toml`` is present it
    pre-sets ``engine = "zensical"``.  Otherwise the ``[build_context]`` block
    is omitted and the standalone (engine-agnostic) defaults apply.

    Use ``--dev`` to also create ``.zenzic.dev.toml`` (D002 Environmental Privacy
    Gate).  In editable installs the dev scaffold is created automatically
    (CEO-275 Conditional Scaffolding).
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
        _shared.console.print(f"[dim]  Target: {_hint}[/]\n")
    else:
        repo_root = find_repo_root(fallback_to_cwd=True)

    if plugin is not None:
        conflicting = [flag for flag, val in [("--dev", dev), ("--pyproject", pyproject)] if val]
        if conflicting:
            typer.echo(
                f"ERROR: --plugin cannot be combined with {', '.join(conflicting)}. "
                "These flags target different init modes.",
                err=True,
            )
            raise typer.Exit(2)
        _scaffold_plugin(repo_root, plugin, force)
        return

    use_pyproject = pyproject
    pyproject_path = repo_root / "pyproject.toml"

    if not use_pyproject and pyproject_path.is_file():
        use_pyproject = typer.confirm(
            "Found pyproject.toml. Embed Zenzic config there as [tool.zenzic]?",
            default=False,
        )

    if use_pyproject:
        _init_pyproject(repo_root, pyproject_path, force)
    else:
        _init_standalone(repo_root, force)

    # CEO-275: Conditional Scaffolding — create .zenzic.dev.toml when:
    #   (a) --dev flag is explicitly passed, or
    #   (b) running in an editable (developer) install (auto-detection)
    if dev or _is_editable_install():
        _scaffold_dev_toml(repo_root)


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


def _scaffold_dev_toml(repo_root: Path) -> None:
    """Create a ``.zenzic.dev.toml`` template for the D002 Environmental Privacy Gate.

    Idempotent — skips creation silently if the file already exists.
    The generated file is annotated with the literal-string constraint
    (CEO-276 Literal Certainty Standard) and must be git-ignored.
    """
    from rich.panel import Panel

    dev_toml = repo_root / ".zenzic.dev.toml"
    if dev_toml.exists():
        _shared.console.print("[dim]  .zenzic.dev.toml already exists — skipped.[/]")
        return

    content = (
        "# .zenzic.dev.toml — Local Development Gate (git-ignored)\n"
        "# This file is local to your machine. DO NOT commit it to version control.\n"
        "# Use it to protect private context from being exported by 'zenzic brain map'.\n"
        "#\n"
        "# Documentation: https://zenzic.dev/docs/community/developers/how-to/configure-dev-perimeters\n"
        "\n"
        "[development_gate]\n"
        "# List of literal strings (case-insensitive) to be redacted from exports.\n"
        "# Regular expressions are NOT supported — patterns are matched verbatim.\n"
        '# forbidden_patterns = ["internal-project-name", "/home/user/private/path"]\n'
        "forbidden_patterns = []\n"
    )
    dev_toml.write_text(content, encoding="utf-8")

    _shared.console.print(
        Panel(
            "[green]✔[/] [bold].zenzic.dev.toml[/] created (D002 Privacy Gate).\n"
            "[yellow]⚠[/]  Add this file to [bold].gitignore[/] — it is local only.\n\n"
            "Edit [bold cyan]forbidden_patterns[/] with literal strings to protect "
            "from exports.",
            title="[bold]Dev Perimeter Gate[/]",
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


def _init_standalone(repo_root: Path, force: bool) -> None:
    """Create a standalone ``zenzic.toml`` configuration file."""
    config_path = repo_root / "zenzic.toml"

    if config_path.is_file() and not force:
        _shared.console.print(
            f"[yellow]WARNING:[/] [bold]zenzic.toml[/] already exists at "
            f"[dim]{config_path}[/]\n"
            "Use [bold cyan]--force[/] to overwrite."
        )
        raise typer.Exit(1)

    detected_engine = _detect_init_engine(repo_root)

    toml_content = (
        "# zenzic.toml — The Zenzic Safe Harbor Configuration\n"
        "# See https://zenzic.dev/docs/reference/configuration/ for full reference.\n"
        "\n"
        "# --- CORE SETTINGS ---\n"
        'docs_dir = "docs"\n'
        "fail_under = 100  # Strict gate: fail if quality score < 100%\n"
        "strict = true     # Promote all warnings to blocking errors\n"
        "\n"
        "# --- QUALITY THRESHOLDS ---\n"
        "# placeholder_max_words = 50       # Threshold for Z502 (Short Content)\n"
        "\n"
        "# --- EXCLUSIONS ---\n"
        "# respect_vcs_ignore = false  # uncomment to disable .gitignore integration\n"
        '# excluded_dirs = ["temp", "drafts", "node_modules"]\n'
        "# excluded_external_urls = []\n"
        "\n"
        "# --- PROJECT IDENTITY ---\n"
        "[project_metadata]\n"
        'release_name = "MyProject"\n'
        '# obsolete_names = ["OldBrand", "LegacyName"]\n'
        "\n"
        "# --- ENGINE CONTEXT ---\n"
        "[build_context]\n"
        f'engine = "{detected_engine}"   # Pre-aligned via Quartz Auto-Discovery\n'
        'base_url = "/"\n'
        'default_locale = "en"\n'
        "\n"
        "# --- CUSTOM RULES ---\n"
        "# [[custom_rules]]\n"
        '# id = "ZZ-001"\n'
        '# pattern = "TODO:"\n'
        '# message = "Incomplete content detected."\n'
        '# severity = "warning"\n'
    )

    config_path.write_text(toml_content, encoding="utf-8")

    _shared.console.print(
        Panel(
            f"[green]✔[/] [bold]Sentinel Seal:[/] zenzic.toml created.\n"
            f"[yellow]💡[/] [bold]Auto-discovery:[/] Engine pre-set to "
            f"[bold cyan]{detected_engine}[/].\n\n"
            "Edit the file, adjust directories, then run "
            "[bold cyan]zenzic check all[/].",
            title="[bold]Zenzic Init[/]",
            border_style="green",
        )
    )


def _init_pyproject(repo_root: Path, pyproject_path: Path, force: bool) -> None:
    """Append a ``[tool.zenzic]`` section to an existing ``pyproject.toml``."""
    if not pyproject_path.is_file():
        _shared.console.print(
            "[red]ERROR:[/] No [bold]pyproject.toml[/] found at "
            f"[dim]{pyproject_path}[/]\n"
            "Use [bold cyan]zenzic init[/] without --pyproject to create a standalone zenzic.toml."
        )
        raise typer.Exit(1)

    existing = pyproject_path.read_text(encoding="utf-8")

    if "[tool.zenzic]" in existing and not force:
        _shared.console.print(
            "[yellow]WARNING:[/] [bold][tool.zenzic][/] already exists in "
            f"[dim]{pyproject_path}[/]\n"
            "Use [bold cyan]--force[/] to overwrite the section."
        )
        raise typer.Exit(1)

    detected_engine = _detect_init_engine(repo_root)

    engine_section = (
        "\n[tool.zenzic.build_context]\n"
        f'engine = "{detected_engine}"   # Pre-aligned via Quartz Auto-Discovery\n'
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
    ) + engine_section

    if force and "[tool.zenzic]" in existing:
        existing = re.sub(
            r"\n?\[tool\.zenzic[^\]]*\][^\[]*",
            "",
            existing,
        )

    pyproject_path.write_text(existing.rstrip("\n") + "\n" + section, encoding="utf-8")

    _shared.console.print(
        Panel(
            f"[green]✔[/] [bold]Sentinel Seal:[/] [tool.zenzic] added to "
            f"{pyproject_path.relative_to(repo_root)}.\n"
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

    project_slug = re.sub(r"[^a-z0-9-]+", "-", raw.lower()).strip("-")
    project_slug = re.sub(r"-+", "-", project_slug)
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
zenzic inspect capabilities
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

    _shared.console.print(
        f"\n[green]Created plugin scaffold[/] [bold]{project_slug}[/]\n"
        f"  Path: [dim]{target.relative_to(repo_root)}[/]\n"
        f"  Entry-point: [bold]{project_slug}[/] -> [dim]{module_name}.rules:{class_name}[/]\n"
        "\nNext steps:\n"
        f"  1. [bold]cd {project_slug}[/]\n"
        "  2. [bold]uv pip install -e .[/]\n"
        "  3. [bold]zenzic inspect capabilities[/]"
    )
