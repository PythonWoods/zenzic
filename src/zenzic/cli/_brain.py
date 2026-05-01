# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""brain sub-commands — Developer Sovereign Cartography tools.

CEO-242: ``zenzic brain map [PATH]``
  Scans Python sources via AST and updates the [CODE MAP] section in
  ZENZIC_BRAIN.md, then performs Master-Shadow Sync to
  ``.github/copilot-instructions.md`` (CEO 103-B).

CEO-243: Zone B audit and Trinity Mesh status are reported on every run.

Only available in editable (dev) installs — see ``_is_dev_mode()`` in
``main.py`` (CEO-246 Identity Gate via PEP 610 ``direct_url.json``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from zenzic.core.cartography import (
    MAP_END,
    MAP_START,
    render_markdown_table,
    scan_python_sources,
    update_ledger,
)


brain_app = typer.Typer(
    name="brain",
    help=(
        "[bold]Sovereign Cartography tools.[/] "
        "AST-based module mapping and ZENZIC_BRAIN.md synchronisation.\n\n"
        "[dim]Only available in editable (dev) installs — CEO-246.[/]"
    ),
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# ─── Zone B audit constants (CEO-243) ─────────────────────────────────────────
_ZONE_B_START = "<!-- ZONE_B_START -->"
_ZONE_B_END = "<!-- ZONE_B_END -->"
_ZONE_B_LIMIT = 400

# Trinity Mesh sibling repositories (CEO-236 Silent Mind Protocol).
# INVARIANT: zenzic-brain is NEVER listed here.
_MESH_REPOS = ("zenzic", "zenzic-doc", "zenzic-action")


# ─── Private helpers ───────────────────────────────────────────────────────────


def _find_src_root(base: Path) -> Path:
    """Auto-detect the Python source root under *base*.

    Priority:
    1. First ``src/<package>/`` directory whose parent is ``src/``.
    2. ``src/`` itself if it exists.
    3. *base* as-is.
    """
    src_dir = base / "src"
    if src_dir.is_dir():
        # Return the first package directory inside src/ (e.g. src/zenzic/)
        candidates = [d for d in src_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        if candidates:
            return candidates[0]
        return src_dir
    return base


def _find_ledger(start: Path) -> Path | None:
    """Walk up from *start* to find ZENZIC_BRAIN.md (max 10 levels)."""
    current = start.resolve()
    for _ in range(10):
        candidate = current / "ZENZIC_BRAIN.md"
        if candidate.exists():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def _shadow_sync(ledger: Path) -> Path:
    """Copy ZENZIC_BRAIN.md → .github/copilot-instructions.md.

    Master-Shadow Sync — CEO 103-B.  Always runs as the final operation so the
    IDE always sees the freshest map.
    """
    shadow = ledger.parent / ".github" / "copilot-instructions.md"
    shadow.parent.mkdir(parents=True, exist_ok=True)
    shadow.write_text(ledger.read_text(encoding="utf-8"), encoding="utf-8")
    return shadow


def _audit_zone_b(ledger: Path) -> tuple[int, int]:
    """Count lines inside Zone B markers in *ledger*.

    Returns ``(line_count, limit)``.
    """
    text = ledger.read_text(encoding="utf-8")
    in_zone = False
    count = 0
    for line in text.splitlines():
        if _ZONE_B_START in line:
            in_zone = True
            continue
        if _ZONE_B_END in line:
            in_zone = False
            continue
        if in_zone:
            count += 1
    return count, _ZONE_B_LIMIT


def _detect_mesh_status(repo_root: Path) -> str:
    """Probe sibling repositories for ZENZIC_BRAIN.md presence.

    Returns a human-readable mesh status string.
    INVARIANT: zenzic-brain is never probed (Silent Mind Protocol — CEO-236).
    """
    parts = []
    for name in _MESH_REPOS:
        sibling = repo_root.parent / name
        if sibling.exists() and (sibling / "ZENZIC_BRAIN.md").exists():
            parts.append(f"{name} 🟢")
        else:
            parts.append(f"{name} 🔴")
    return "[MESH STATUS] " + " | ".join(parts)


# ─── Commands ──────────────────────────────────────────────────────────────────


@brain_app.command("map")
def brain_map(
    path: Annotated[
        Path,
        typer.Argument(
            help=(
                "Repo root to scan (defaults to current directory). "
                "The command auto-detects ``src/<package>/`` as the source root."
            ),
            show_default=True,
        ),
    ] = Path("."),
    check: Annotated[
        bool,
        typer.Option(
            "--check",
            help=(
                "Audit mode: compare the generated [CODE MAP] against "
                "ZENZIC_BRAIN.md without writing. "
                "Exits 1 (D001 MEMORY_STALE) if stale. "
                "Used by the pre-commit Quartz Audit Gate (CEO-257)."
            ),
        ),
    ] = False,
) -> None:
    """Scan Python sources via AST and update ZENZIC_BRAIN.md [CODE MAP].

    Performs Zone B audit, Trinity Mesh status check, and Master-Shadow Sync
    to ``.github/copilot-instructions.md`` as final steps.

    With ``--check``: read-only audit mode. Does not write; exits 1 (D001) if
    [CODE MAP] is stale. Designed for the pre-commit Quartz Audit Gate.
    """
    repo_root = path.resolve()
    if not repo_root.is_dir():
        typer.echo(f"[brain map] ERROR: {repo_root} is not a directory.", err=True)
        raise typer.Exit(1)

    scan_root = _find_src_root(repo_root)
    typer.echo(f"[brain map] Scanning {scan_root.relative_to(repo_root)} …")

    modules = scan_python_sources(scan_root)
    if not modules:
        typer.echo("[brain map] No Python source files found.", err=True)
        raise typer.Exit(1)

    map_block = render_markdown_table(modules)

    ledger = _find_ledger(repo_root)
    if ledger is None:
        if check:
            typer.echo(
                "\n✘ D001 MEMORY_STALE: No ZENZIC_BRAIN.md found upstream.\n"
                "  Action required: run 'just brain-map' to initialise the ledger.",
                err=True,
            )
            raise typer.Exit(1)
        # No ZENZIC_BRAIN.md — print for manual insertion
        typer.echo(f"\n{MAP_START}")
        typer.echo(map_block)
        typer.echo(f"{MAP_END}")
        typer.echo(
            "\n[brain map] No ZENZIC_BRAIN.md found upstream. Output printed for manual insertion.",
            err=True,
        )
        return

    # ── Quartz Audit Gate (--check mode, CEO-257) ──────────────────────────────
    if check:
        text = ledger.read_text(encoding="utf-8")
        start_idx = text.find(MAP_START)
        end_idx = text.find(MAP_END)
        if start_idx == -1 or end_idx == -1:
            typer.echo(
                "\n✘ D001 MEMORY_STALE: MAP_START/MAP_END markers missing in ZENZIC_BRAIN.md.\n"
                "  Action required: run 'just brain-map' to regenerate the ledger.",
                err=True,
            )
            raise typer.Exit(1)
        expected_block = f"{MAP_START}\n{map_block}\n{MAP_END}"
        current_block = text[start_idx : end_idx + len(MAP_END)]
        if current_block != expected_block:
            typer.echo(
                "\n✘ D001 MEMORY_STALE: The sovereign [CODE MAP] is out of sync with src/.\n"
                "  Action required: run 'just brain-map' and stage the changes to ZENZIC_BRAIN.md.",
                err=True,
            )
            raise typer.Exit(1)
        typer.echo(f"[brain map] ✔ {ledger.name} [CODE MAP] is in sync with src/ — memory intact.")
        return

    try:
        updated = update_ledger(ledger, map_block)
    except ValueError as exc:
        typer.echo(f"[brain map] ERROR: {exc}", err=True)
        raise typer.Exit(1) from exc

    if updated:
        typer.echo(
            f"[brain map] ✔ {ledger.name} [CODE MAP] updated — {len(modules)} modules mapped."
        )
    else:
        typer.echo(f"[brain map] ✔ {ledger.name} [CODE MAP] already up to date.")

    # Zone B audit (CEO-243) ───────────────────────────────────────────────────
    zone_b, limit = _audit_zone_b(ledger)
    if zone_b > limit:
        typer.echo(
            f"[Z907] MEMORY_OVERFLOW: Zone B has {zone_b}/{limit} lines. "
            "Curation required before next commit.",
            err=True,
        )
        # Shadow sync before exit so the IDE still sees the updated map
        _shadow_sync(ledger)
        raise typer.Exit(2)
    else:
        typer.echo(f"[brain map] Zone B: {zone_b}/{limit} lines — within guardrail.")

    # Trinity Mesh status ──────────────────────────────────────────────────────
    typer.echo(_detect_mesh_status(ledger.parent))

    # Master-Shadow Sync (CEO 103-B) — always runs as the final operation ──────
    shadow = _shadow_sync(ledger)
    typer.echo(f"[brain map] ✔ Shadow sync → {shadow.relative_to(ledger.parent)}")
