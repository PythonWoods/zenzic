# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""BaseAdapter Protocol — the engine-agnostic contract every adapter must satisfy."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from zenzic.models.vsm import RouteStatus


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

    def resolve_anchor(
        self,
        resolved_file: Path,
        anchor: str,
        anchors_cache: dict[Path, set[str]],
        docs_root: Path,
    ) -> bool:
        """Return ``True`` if an anchor miss should be suppressed via i18n fallback.

        When a file inside a locale sub-tree (e.g. ``docs/it/architecture.md``)
        does not contain the requested anchor — because headings are translated —
        this method checks whether the anchor exists in the corresponding
        default-locale file (e.g. ``docs/architecture.md``).  If it does, the
        ``AnchorMissing`` error is suppressed: MkDocs / Zensical will serve the
        default-locale page for this anchor at build time.

        Args:
            resolved_file: Absolute path of the locale file that was found but
                whose anchor set does not contain *anchor*.
            anchor: The fragment identifier that was not found (without ``#``).
            anchors_cache: Pre-built mapping of absolute ``Path`` → anchor slug
                set.  No disk I/O is performed — this is a pure in-memory check.
            docs_root: Resolved absolute ``docs/`` root (for path stripping).

        Returns:
            ``True`` if the anchor exists in the default-locale equivalent file
            and the error should be suppressed; ``False`` otherwise.
        """
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

    def map_url(self, rel: Path) -> str:
        """Map a physical source file path to its canonical virtual URL.

        Args:
            rel: Path of the Markdown source file, relative to ``docs_root``.

        Returns:
            Canonical URL string with leading and trailing slash
            (e.g. ``'/guide/installation/'``).
        """
        ...

    def classify_route(self, rel: Path, nav_paths: frozenset[str]) -> RouteStatus:
        """Classify a source file's routing status.

        Args:
            rel:       Path relative to ``docs_root``.
            nav_paths: Frozenset of nav-listed ``.md`` paths (from
                       ``get_nav_paths()``).

        Returns:
            ``RouteStatus`` literal: ``'REACHABLE'``, ``'ORPHAN_BUT_EXISTING'``,
            or ``'IGNORED'``.  ``'CONFLICT'`` is set later by
            ``_detect_collisions()`` and must not be returned here.
        """
        ...
