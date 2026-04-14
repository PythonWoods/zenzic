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

import os
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING

from zenzic.models.config import ZenzicConfig


if TYPE_CHECKING:
    from zenzic.core.exclusion import LayeredExclusionManager


# Extensions recognised as documentation source files (not assets).
DOC_SUFFIXES: frozenset[str] = frozenset({".md", ".mdx"})


def walk_files(
    root: Path,
    excluded_dirs: set[str] | frozenset[str],
    exclusion_manager: LayeredExclusionManager,
) -> Generator[Path, None, None]:
    """Yield all regular files under *root*, pruning excluded directories.

    Unlike ``Path.rglob("*")``, this uses :func:`os.walk` with in-place
    directory pruning so that large excluded trees (e.g. ``.nox/``,
    ``node_modules/``) are never entered at all.

    The *exclusion_manager* drives directory exclusion decisions via
    :meth:`~LayeredExclusionManager.should_exclude_dir`.  The
    *excluded_dirs* set provides an additional hard-prune layer (used by
    ``find_unused_assets`` for ``excluded_asset_dirs``).
    """
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d
            for d in dirnames
            if not exclusion_manager.should_exclude_dir(d) and d not in excluded_dirs
        )
        for fname in sorted(filenames):
            yield Path(dirpath) / fname


def iter_locale_markdown_sources(
    locale_root: Path,
    locale_name: str,
    config: ZenzicConfig,
    exclusion_manager: LayeredExclusionManager,
) -> Generator[tuple[Path, Path], None, None]:
    """Yield ``(abs_path, logical_rel)`` for source files in a Docusaurus locale tree.

    ``logical_rel`` is the path that the core should use as the file's identity
    within the broader documentation namespace — it starts with the locale
    prefix so that the adapter can route it correctly::

        i18n/it/.../current/architecture.mdx  →  (abs_path, Path("it/architecture.mdx"))

    The locale prefix makes ``map_url(logical_rel)`` produce the correct
    locale-prefixed URL (e.g. ``/it/architecture/``) without any special-casing
    in the adapter.

    Args:
        locale_root: Absolute path to the locale docs root
            (e.g. ``i18n/it/docusaurus-plugin-content-docs/current/``).
        locale_name: ISO locale code used as the path prefix (e.g. ``'it'``).
        config: Loaded Zenzic configuration.
        exclusion_manager: Layered exclusion manager.

    Yields:
        ``(abs_path, logical_rel)`` tuples where
        ``logical_rel = Path(locale_name) / path.relative_to(locale_root)``.
    """
    if not locale_root.is_dir():
        return
    excluded_dirs = set(config.excluded_dirs)
    for md_file in walk_files(locale_root, excluded_dirs, exclusion_manager):
        if md_file.suffix not in DOC_SUFFIXES:
            continue
        if md_file.is_symlink():
            continue
        if exclusion_manager.should_exclude_file(md_file, locale_root):
            continue
        logical_rel = Path(locale_name) / md_file.relative_to(locale_root)
        yield md_file, logical_rel


def iter_markdown_sources(
    docs_root: Path,
    config: ZenzicConfig,
    exclusion_manager: LayeredExclusionManager,
) -> Generator[Path, None, None]:
    """Yield absolute paths to ``.md`` / ``.mdx`` files, honouring all exclusions.

    All exclusion decisions are delegated to the *exclusion_manager*,
    which implements the 4-level Layered Exclusion model (System Guardrails,
    VCS, Config, CLI).

    This is the **single authorised entry point** for discovering documentation
    source files.  All modules (scanner, validator, orphan-checker) must use
    this function instead of calling ``rglob`` or ``walk_files`` directly for
    Markdown iteration.

    Args:
        docs_root: Absolute path to the documentation root directory.
        config: Loaded Zenzic configuration (provides ``excluded_dirs``).
        exclusion_manager: Layered Exclusion Manager for full
            4-level exclusion evaluation.

    Yields:
        Absolute :class:`~pathlib.Path` objects for each qualifying source file,
        in deterministic sorted order (imposed by :func:`walk_files`).
    """
    excluded_dirs = set(config.excluded_dirs)
    for md_file in walk_files(docs_root, excluded_dirs, exclusion_manager):
        if md_file.suffix not in DOC_SUFFIXES:
            continue
        if md_file.is_symlink():
            continue
        if exclusion_manager.should_exclude_file(md_file, docs_root):
            continue
        yield md_file
