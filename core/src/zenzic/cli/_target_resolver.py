# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Target resolution helpers for ``zenzic check`` and ``zenzic lab`` commands.

Provides :func:`_resolve_target` (path lookup) and :func:`_apply_target`
(config patching), extracted from ``_check.py`` as part of Phase 82 CLI
decomposition (ADR-082).
"""

from __future__ import annotations

import os
from pathlib import Path

import typer

from zenzic.models.config import ZenzicConfig

from . import _shared


def _resolve_target(repo_root: Path, config: ZenzicConfig, raw: str) -> Path:
    """Resolve *raw* to an existing file or directory.

    Search order: absolute as-is → relative to *repo_root* → relative to
    *repo_root/docs_dir*.  Files must have the ``.md`` extension.
    Exits with code 1 if nothing is found or the extension is wrong.
    """
    raw = raw.split("#")[0].split("?")[0]
    p = Path(raw)
    candidates: list[Path] = (
        [p] if p.is_absolute() else [repo_root / p, repo_root / config.docs_dir / p]
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
        if candidate.is_file():
            if candidate.suffix.lower() not in (".md", ".mdx"):
                _shared.console.print(
                    f"[red]ERROR:[/] [bold]{raw}[/] is not a Markdown file "
                    f"(expected .md or .mdx, got '{candidate.suffix}')."
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
    file mode.  *hint* is a short display string for the analysis header.
    """
    target = _resolve_target(repo_root, config, raw_path)

    try:
        rel = target.relative_to(repo_root)
        if rel == Path("."):
            # Target IS repo_root itself — use relpath from CWD for clean display.
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
