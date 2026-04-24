# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Shared CLI infrastructure: console singleton, _ui gateway, and cross-command utilities.

All Console and Panel configuration for the CLI lives here or in ``zenzic.ui``.
No other CLI module may instantiate Console or Panel directly.
"""

from __future__ import annotations

import difflib
import json
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from zenzic.core.adapters import list_adapter_engines
from zenzic.core.exclusion import LayeredExclusionManager
from zenzic.core.reporter import Finding
from zenzic.core.ui import ObsidianPalette, ObsidianUI, emoji
from zenzic.models.config import ZenzicConfig


# ── Console singleton & UI gateway ───────────────────────────────────────────

console = Console(
    highlight=False,
    no_color=os.environ.get("NO_COLOR") is not None,
    force_terminal=True
    if os.environ.get("FORCE_COLOR") and not os.environ.get("NO_COLOR")
    else None,
)

_ui = ObsidianUI(console)


def configure_console(*, no_color: bool = False, force_color: bool = False) -> None:
    """Reconfigure the module-level console for color control.

    Called by main.py callback when --no-color or --force-color flags are passed.
    CLI flags take priority over environment variables.  Also rebuilds ``_ui``
    so all subsequent command output uses the reconfigured console.
    """
    global console, _ui
    if no_color:
        console = Console(highlight=False, no_color=True)
    elif force_color:
        console = Console(highlight=False, force_terminal=True)
    # else: keep existing console — no_color=False + force_color=False means "auto",
    # which is already set correctly in the module-level Console (force_terminal=None).
    _ui = ObsidianUI(console)


def get_ui() -> ObsidianUI:
    """Return the current centralized :class:`~zenzic.ui.ObsidianUI` instance.

    Always performs a live lookup so callers outside this module always receive
    the instance that is current *after* any ``configure_console()`` call.
    """
    return _ui


def get_console() -> Console:
    """Return the current centralized :class:`rich.console.Console` instance."""
    return console


# ── Info hint panel ──────────────────────────────────────────────────────────

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


# ── Engine override ───────────────────────────────────────────────────────────


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


# ── JSON output ───────────────────────────────────────────────────────────────


def _output_json_findings(findings: list[Finding], elapsed: float) -> None:
    """Serialize findings list to JSON and print to stdout."""
    report = {
        "findings": [
            {
                "rel_path": f.rel_path,
                "line_no": f.line_no,
                "code": f.code,
                "severity": f.severity,
                "message": f.message,
            }
            for f in findings
        ],
        "summary": {
            "errors": sum(1 for f in findings if f.severity == "error"),
            "warnings": sum(1 for f in findings if f.severity == "warning"),
            "info": sum(1 for f in findings if f.severity == "info"),
            "security_incidents": sum(1 for f in findings if f.severity == "security_incident"),
            "security_breaches": sum(1 for f in findings if f.severity == "security_breach"),
            "elapsed_seconds": round(elapsed, 3),
        },
    }
    print(json.dumps(report, indent=2))


# ── Link error renderer ───────────────────────────────────────────────────────


def _render_link_error(err: object, docs_root: Path) -> None:
    """Print a single LinkError with a Visual Snippet when source context is available."""
    from zenzic.core.validator import LinkError

    assert isinstance(err, LinkError)
    try:
        rel = err.file_path.relative_to(docs_root)
        location = f"[dim]{rel}:{err.line_no}[/]"
    except ValueError:
        location = f"[dim]{err.file_path.name}:{err.line_no}[/]"

    raw_msg = err.message
    prefix = f"{err.file_path.relative_to(docs_root).as_posix() if err.file_path != docs_root else ''}:{err.line_no}: "
    body = raw_msg[len(prefix) :] if raw_msg.startswith(prefix) else raw_msg

    type_badge = f"[[bold red]{err.error_type}[/]]" if err.error_type != "LINK_ERROR" else ""
    header = f"  {type_badge} {location} — {body}"
    console.print(header)

    if err.source_line:
        console.print(f"    [dim]│[/] [italic]{err.source_line}[/]")


# ── Exclusion manager factory ─────────────────────────────────────────────────


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
            f"[bold {ObsidianPalette.FATAL}]BLOOD SENTINEL:[/] docs_dir resolves to "
            f"[bold]{resolved_docs}[/] which is outside the repository root "
            f"[bold]{resolved_repo}[/]. Path traversal blocked."
        )
        raise typer.Exit(3) from None


# ── Telemetry counter ─────────────────────────────────────────────────────────


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
