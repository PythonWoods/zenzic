# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Shared i18n path-remapping utility for Zenzic adapters.

All adapters that support ``fallback_to_default`` folder-mode i18n share the
same "locale prefix stripping" logic: given a path inside a locale sub-tree
(e.g. ``docs/it/architecture.md``), produce the corresponding default-locale
path (``docs/architecture.md``).

This module centralises that logic so each adapter only needs to know *which*
directories are locale directories, and Zenzic owns *how* the remapping works.

Third-party adapters that use a different i18n convention (e.g. Hugo's
``content/<lang>/`` layout) are free to ignore this utility entirely and
implement their own ``resolve_asset`` / ``resolve_anchor`` logic.
"""

from __future__ import annotations

from pathlib import Path


def remap_to_default_locale(
    abs_path: Path,
    docs_root: Path,
    locale_dirs: frozenset[str],
) -> Path | None:
    """Return the default-locale equivalent of a path inside a locale sub-tree.

    Strips the first path component when it is a known locale directory name,
    producing the canonical default-locale path.  Returns ``None`` when the
    path is not inside any known locale directory — the caller should not apply
    fallback logic in that case.

    This function is **pure** — no I/O, no disk access.  The caller decides
    what to do with the returned path (existence check, anchor lookup, etc.).

    Examples::

        remap_to_default_locale(
            Path("/docs/it/architecture.md"),
            Path("/docs"),
            frozenset({"it", "fr"}),
        )
        # → Path("/docs/architecture.md")

        remap_to_default_locale(
            Path("/docs/architecture.md"),
            Path("/docs"),
            frozenset({"it", "fr"}),
        )
        # → None  (not inside a locale directory)

    Args:
        abs_path: Absolute path to remap.  May be a ``.md`` file, an asset,
            or any path inside ``docs_root``.
        docs_root: Resolved absolute ``docs/`` root.
        locale_dirs: Frozenset of non-default locale directory names
            (e.g. ``frozenset({"it", "fr"})``).

    Returns:
        Absolute :class:`~pathlib.Path` of the default-locale equivalent, or
        ``None`` when *abs_path* is not inside a recognised locale directory.
    """
    try:
        rel = abs_path.relative_to(docs_root)
    except ValueError:
        return None
    if not rel.parts or rel.parts[0] not in locale_dirs:
        return None
    return docs_root.joinpath(*rel.parts[1:])
