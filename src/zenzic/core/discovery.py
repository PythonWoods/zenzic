# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Centralised file-discovery utilities for the Zenzic Core.

Every module that needs to iterate over documentation source files or asset
files must use the helpers defined here.  This ensures that ``excluded_dirs``
(including the ``SYSTEM_EXCLUDED_DIRS`` guardrails merged at config load time)
and ``excluded_file_patterns`` are applied **universally** — scanner, validator,
Shield, and orphan-checker all see the exact same file set.

Public API
----------
* :func:`walk_files` — low-level ``os.walk`` with directory pruning.
* :func:`iter_markdown_sources` — yield ``.md`` / ``.mdx`` files honouring
  both directory *and* filename exclusions.
"""

from __future__ import annotations

import fnmatch
import os
from collections.abc import Generator
from pathlib import Path

from zenzic.models.config import ZenzicConfig


# Extensions recognised as documentation source files (not assets).
DOC_SUFFIXES: frozenset[str] = frozenset({".md", ".mdx"})


def walk_files(
    root: Path,
    excluded_dirs: set[str] | frozenset[str],
) -> Generator[Path, None, None]:
    """Yield all regular files under *root*, pruning excluded directories.

    Unlike ``Path.rglob("*")``, this uses :func:`os.walk` with in-place
    directory pruning so that large excluded trees (e.g. ``.nox/``,
    ``node_modules/``) are never entered at all.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune in-place: remove excluded directory names so os.walk
        # does not descend into them.
        dirnames[:] = sorted(d for d in dirnames if d not in excluded_dirs)
        for fname in sorted(filenames):
            yield Path(dirpath) / fname


def iter_markdown_sources(
    docs_root: Path,
    config: ZenzicConfig,
) -> Generator[Path, None, None]:
    """Yield absolute paths to ``.md`` / ``.mdx`` files, honouring all exclusions.

    Applies both ``config.excluded_dirs`` (directory-level pruning via
    :func:`walk_files`) and ``config.excluded_file_patterns`` (filename-level
    ``fnmatch`` filtering).  Symlinks are silently skipped.

    This is the **single authorised entry point** for discovering documentation
    source files.  All modules (scanner, validator, orphan-checker) must use
    this function instead of calling ``rglob`` or ``walk_files`` directly for
    Markdown iteration.

    Args:
        docs_root: Absolute path to the documentation root directory.
        config: Loaded Zenzic configuration (provides ``excluded_dirs`` and
            ``excluded_file_patterns``).

    Yields:
        Absolute :class:`~pathlib.Path` objects for each qualifying source file,
        in deterministic sorted order (imposed by :func:`walk_files`).
    """
    excluded_dirs = set(config.excluded_dirs)
    exclusion_patterns = set(config.excluded_file_patterns)
    for md_file in walk_files(docs_root, excluded_dirs):
        if md_file.suffix not in DOC_SUFFIXES:
            continue
        if md_file.is_symlink():
            continue
        rel = md_file.relative_to(docs_root)
        if any(part in excluded_dirs for part in rel.parts):
            continue
        if exclusion_patterns and any(
            fnmatch.fnmatch(md_file.name, pat) for pat in exclusion_patterns
        ):
            continue
        yield md_file
