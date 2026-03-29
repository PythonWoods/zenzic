# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""BaseAdapter Protocol — the engine-agnostic contract every adapter must satisfy."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class BaseAdapter(Protocol):
    """Protocol that every build-engine adapter must satisfy.

    The Scanner and other core components depend only on this interface,
    never on a concrete adapter class, which keeps the Core engine-agnostic.
    """

    def is_locale_dir(self, part: str) -> bool:
        """Return ``True`` when *part* is a non-default locale directory name."""
        ...

    def resolve_asset(self, missing_abs: Path, docs_root: Path) -> Path | None:
        """Return the default-locale fallback for a missing asset, or ``None``."""
        ...

    def is_shadow_of_nav_page(self, rel: Path, nav_paths: frozenset[str]) -> bool:
        """Return ``True`` when *rel* is a locale-mirror of a nav-listed page."""
        ...

    def get_ignored_patterns(self) -> set[str]:
        """Return filename glob patterns for non-default locale files (suffix mode)."""
        ...

    def get_nav_paths(self) -> frozenset[str]:
        """Return ``.md`` paths listed in the nav, relative to ``docs_root``."""
        ...

    def has_engine_config(self) -> bool:
        """Return ``True`` when a build-engine config was found and loaded.

        ``VanillaAdapter`` returns ``False``.  All concrete adapters return
        ``True``.  Callers use this to decide whether a nav-based check
        (e.g. orphan detection) can produce meaningful results.
        """
        ...
