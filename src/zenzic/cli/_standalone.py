# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Standalone commands: score, diff, init — and their private helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path

import typer
from rich import box
from rich.table import Table
from rich.text import Text

from zenzic.core.exclusion import LayeredExclusionManager
from zenzic.core.scanner import (
    find_orphans,
    find_placeholders,
    find_repo_root,
    find_unused_assets,
)
from zenzic.core.scorer import ScoreReport, compute_score, load_snapshot, save_snapshot
from zenzic.core.ui import ObsidianPalette, emoji
from zenzic.core.validator import validate_links, validate_snippets
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


# ── score command ─────────────────────────────────────────────────────────────


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
        from zenzic import __version__

        if report.score >= 80:
            score_style = ObsidianPalette.STYLE_OK
        elif report.score >= 50:
            score_style = "bold yellow"
        else:
            score_style = ObsidianPalette.STYLE_ERR

        score_summary = Text.from_markup(
            f"{emoji('sparkles')} "
            f"[bold {ObsidianPalette.SUCCESS}]Quality Score:[/bold {ObsidianPalette.SUCCESS}]"
            f" [{score_style}]{report.score}/100[/{score_style}]\n"
        )

        table = Table(
            box=box.ROUNDED,
            title="[bold]Quality Breakdown[/]",
            title_style=ObsidianPalette.DIM,
            border_style=ObsidianPalette.DIM,
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

        _shared.console.print()
        _shared._ui.print_header(__version__)
        _shared.console.print()
        _shared.console.print(score_summary)
        _shared.console.print(table)

    if effective_threshold > 0 and report.score < effective_threshold:
        _shared.console.print(
            f"\n[red]FAILED:[/] score {report.score} is below threshold {effective_threshold}."
        )
        raise typer.Exit(1)


# ── diff command ──────────────────────────────────────────────────────────────


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
    exclusion_mgr = _shared._build_exclusion_manager(config, repo_root, docs_root)
    effective_strict = strict if strict is not None else config.strict

    baseline = load_snapshot(repo_root)
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
            border_style=ObsidianPalette.DIM,
            show_header=True,
            header_style=ObsidianPalette.STYLE_BRAND,
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
) -> None:
    """Scaffold a Zenzic configuration in the current project.

    By default creates ``zenzic.toml``.  If ``pyproject.toml`` exists in the
    project root Zenzic will ask whether to embed the configuration there
    as a ``[tool.zenzic]`` table instead.  Use ``--pyproject`` to skip the
    prompt and write directly into ``pyproject.toml``.

    Performs engine auto-detection: if ``mkdocs.yml`` is present the generated
    file pre-sets ``engine = "mkdocs"``; if ``zensical.toml`` is present it
    pre-sets ``engine = "zensical"``.  Otherwise the ``[build_context]`` block
    is omitted and the standalone (engine-agnostic) defaults apply.
    """
    from zenzic import __version__

    _shared._ui.print_header(__version__)
    _shared.console.print()
    repo_root = find_repo_root(fallback_to_cwd=True)

    if plugin is not None:
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
    return "  No engine config file found — using standalone (engine-agnostic) defaults.\n"


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
        "#   hex-encoded-payload (3+ consecutive \\xNN sequences), gitlab-pat.\n"
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

    _shared.console.print(
        f"\n[green]Created[/] [bold]{config_path.relative_to(repo_root)}[/]\n"
        + _engine_feedback(detected_engine)
        + "\nEdit the file to enable rules, adjust directories, or set a quality threshold.\n"
        "Run [bold cyan]zenzic check all[/] to validate your documentation."
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
        existing = re.sub(
            r"\n?\[tool\.zenzic[^\]]*\][^\[]*",
            "",
            existing,
        )

    pyproject_path.write_text(existing.rstrip("\n") + "\n" + section, encoding="utf-8")

    _shared.console.print(
        f"\n[green]Added[/] [bold][tool.zenzic][/] to [bold]{pyproject_path.relative_to(repo_root)}[/]\n"
        + _engine_feedback(detected_engine)
        + "\nEdit the section to enable rules, adjust directories, or set a quality threshold.\n"
        "Run [bold cyan]zenzic check all[/] to validate your documentation."
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
