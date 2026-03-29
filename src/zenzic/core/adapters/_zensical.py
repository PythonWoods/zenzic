# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""ZensicalAdapter — native adapter for the Zensical build engine.

Reads ``zensical.toml`` exclusively via Python's ``tomllib``.  Zero YAML.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from zenzic.core.exceptions import ConfigurationError
from zenzic.models.config import BuildContext


# ── Config discovery & loading ────────────────────────────────────────────────


def find_zensical_config(repo_root: Path) -> Path | None:
    """Return the Zensical native config file path, or ``None`` if absent."""
    zensical_toml = repo_root / "zensical.toml"
    return zensical_toml if zensical_toml.exists() else None


def _load_zensical_config(repo_root: Path) -> dict[str, Any]:
    """Load and parse ``zensical.toml``, returning ``{}`` on any failure."""
    config_file = find_zensical_config(repo_root)
    if config_file is None:
        return {}
    try:
        with config_file.open("rb") as f:
            return tomllib.load(f)
    except Exception:  # noqa: BLE001
        return {}


# ── Adapter ───────────────────────────────────────────────────────────────────


class ZensicalAdapter:
    """Adapter for the Zensical build engine — reads ``zensical.toml`` natively.

    Zero YAML.  All configuration is sourced from ``zensical.toml``, whose
    ``[nav]`` section provides the declared page list::

        [nav]
        nav = [
            {title = "Home",     file = "index.md"},
            {title = "Tutorial", file = "tutorial.md"},
        ]

    Locale information is sourced from ``[build_context]`` in ``zenzic.toml``
    (the :class:`~zenzic.models.config.BuildContext`).  Zensical does not yet
    expose its own i18n configuration in ``zensical.toml``; when it does, this
    adapter will be updated to read it directly.

    Enforcement contract: if ``engine = "zensical"`` is declared in
    ``zenzic.toml`` but ``zensical.toml`` is absent, :func:`get_adapter`
    raises :class:`~zenzic.core.exceptions.ConfigurationError` before this
    class is ever instantiated.

    Args:
        context: Build context from ``zenzic.toml``.
        docs_root: Resolved absolute path to the ``docs/`` directory.
        zensical_config: Parsed ``zensical.toml`` contents.
    """

    def __init__(
        self,
        context: BuildContext,
        docs_root: Path,
        zensical_config: dict[str, Any] | None = None,
    ) -> None:
        self._docs_root = docs_root
        self._zensical_config: dict[str, Any] = (
            zensical_config if zensical_config is not None else {}
        )
        # Locale configuration sourced entirely from BuildContext (zenzic.toml).
        self._locale_dirs: frozenset[str] = frozenset(context.locales)
        self._fallback_to_default: bool = context.fallback_to_default

    # ── Public contract ────────────────────────────────────────────────────────

    def is_locale_dir(self, part: str) -> bool:
        """Return ``True`` when *part* is a non-default locale directory name."""
        return part in self._locale_dirs

    def resolve_asset(self, missing_abs: Path, docs_root: Path) -> Path | None:
        """Return the default-locale fallback for a missing asset, or ``None``."""
        if not self._fallback_to_default:
            return None
        try:
            rel = missing_abs.relative_to(docs_root)
        except ValueError:
            return None
        if not rel.parts or rel.parts[0] not in self._locale_dirs:
            return None
        fallback = docs_root.joinpath(*rel.parts[1:])
        return fallback if fallback.exists() else None

    def is_shadow_of_nav_page(self, rel: Path, nav_paths: frozenset[str]) -> bool:
        """Return ``True`` when *rel* is a locale-mirror of a nav-listed page."""
        if not rel.parts or rel.parts[0] not in self._locale_dirs:
            return False
        default_rel = Path(*rel.parts[1:]).as_posix()
        return default_rel in nav_paths

    def get_ignored_patterns(self) -> set[str]:
        """Empty set — Zensical does not use MkDocs suffix-mode i18n patterns."""
        return set()

    def has_engine_config(self) -> bool:
        """``True`` — ZensicalAdapter is constructed only when zensical.toml exists."""
        return True

    def get_nav_paths(self) -> frozenset[str]:
        """Return ``.md`` paths from the ``[nav]`` section of ``zensical.toml``.

        Expects the canonical Zensical nav format::

            [nav]
            nav = [{title = "…", file = "page.md"}, …]

        Returns:
            Frozenset of nav-listed ``.md`` paths, stripped of any leading
            slash and relative to ``docs_root``.
        """
        nav_items = self._zensical_config.get("nav", {}).get("nav", [])
        paths: set[str] = set()
        for item in nav_items:
            if isinstance(item, dict):
                f = item.get("file", "")
                if isinstance(f, str) and f.endswith(".md"):
                    paths.add(f.lstrip("/"))
        return frozenset(paths)

    @classmethod
    def from_repo(
        cls,
        context: BuildContext,
        docs_root: Path,
        repo_root: Path,
    ) -> ZensicalAdapter:
        """Construct from a live repository root.

        Enforces the Zensical contract: ``zensical.toml`` **must** exist in
        *repo_root*.  Raises :class:`~zenzic.core.exceptions.ConfigurationError`
        when it is absent so callers get an actionable error rather than a
        silent no-op.
        """
        if find_zensical_config(repo_root) is None:
            raise ConfigurationError(
                "engine 'zensical' declared in zenzic.toml but zensical.toml is missing",
                context={
                    "repo_root": str(repo_root),
                    "hint": "create zensical.toml or set engine = 'mkdocs' for MkDocs projects",
                },
            )
        return cls(context, docs_root, _load_zensical_config(repo_root))
