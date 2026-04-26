# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""ZensicalAdapter — native adapter for the Zensical build engine.

Reads ``zensical.toml`` exclusively via Python's ``tomllib``.  Zero YAML.

Zensical v0.0.31+ uses a single ``[project]`` scope for all settings::

    [project]
    site_name = "My Docs"
    docs_dir  = "docs"
    nav = [
        "index.md",
        {"Guide" = "guide.md"},
        {"API" = [
            "api/index.md",
            {"Endpoints" = "api/endpoints.md"},
        ]},
    ]
"""

from __future__ import annotations

import logging
import re
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, Any

from zenzic.core.adapters._mkdocs import MkDocsAdapter, _load_doc_config, find_config_file
from zenzic.core.adapters._utils import case_sensitive_exists, remap_to_default_locale
from zenzic.core.exceptions import ConfigurationError
from zenzic.models.config import BuildContext


_log = logging.getLogger(__name__)

_UNSUPPORTED_MKDOCS_KEYS = {
    "remote_branch",
    "remote_name",
    "exclude_docs",
    "draft_docs",
    "not_in_nav",
    "validation",
    "strict",
    "hooks",
    "watch",
}


if TYPE_CHECKING:
    from zenzic.core.adapters._base import RouteMetadata
    from zenzic.models.vsm import RouteStatus


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


# ── Infrastructure asset path extraction (Z404) ──────────────────────────────

_IMAGE_EXT_RE_ZENSICAL = re.compile(r"\.(?:png|jpg|jpeg|svg|gif|ico|webp)$", re.IGNORECASE)


def check_config_assets(repo_root: Path) -> list[tuple[str, str]]:
    """Check that theme assets declared in ``zensical.toml`` exist on disk.

    Checks ``[project].favicon`` and ``[project].logo`` (file-path values only).
    Both fields are resolved relative to ``[project].docs_dir`` (default: ``docs/``).

    Args:
        repo_root: Repository root (parent of ``zensical.toml``).

    Returns:
        List of ``(rel_path, message)`` tuples for each missing asset.
        Empty list when all referenced assets exist or the config is absent.
    """
    zensical_cfg = _load_zensical_config(repo_root)
    if not zensical_cfg:
        return []

    project = zensical_cfg.get("project") or {}
    if not isinstance(project, dict):
        return []

    docs_dir = str(project.get("docs_dir") or "docs")
    docs_root = repo_root / docs_dir

    issues: list[tuple[str, str]] = []

    for field_key in ("favicon", "logo"):
        value = project.get(field_key)
        if not value or not isinstance(value, str):
            continue
        if not _IMAGE_EXT_RE_ZENSICAL.search(value):
            continue
        asset_path = docs_root / value.lstrip("/")
        if not asset_path.exists():
            rel = f"{docs_dir}/{value.lstrip('/')}"
            issues.append(
                (
                    rel,
                    f"{field_key} asset not found on disk: '{rel}' "
                    f"(declared as [project].{field_key}: '{value}' in zensical.toml) [Z404]",
                )
            )

    return issues


def _extract_nav_paths(items: list[object]) -> set[str]:
    """Recursively extract ``.md`` file paths from a Zensical nav list.

    Handles all official nav variants (v0.0.31+):

    * Plain string: ``"page.md"``
    * Titled page: ``{"Title" = "page.md"}``
    * Section:      ``{"Section" = ["page.md", …]}``
    * External URL: ``{"GitHub" = "https://…"}``  — skipped.

    Args:
        items: List of nav entries from ``[project].nav`` in ``zensical.toml``.

    Returns:
        Set of ``.md`` paths, relative to ``docs_root``, without leading slash.
    """
    paths: set[str] = set()
    for item in items:
        if isinstance(item, str):
            if item.endswith(".md"):
                paths.add(item.lstrip("/"))
        elif isinstance(item, dict):
            for _title, val in item.items():
                if isinstance(val, str) and val.endswith(".md"):
                    paths.add(val.lstrip("/"))
                elif isinstance(val, list):
                    paths |= _extract_nav_paths(val)
    return paths


# ── Adapter ───────────────────────────────────────────────────────────────────


class ZensicalLegacyProxy:
    """Proxy that wraps MkDocsAdapter for Zensical legacy compatibility mode.

    Delegates all BaseAdapter protocol methods to the underlying MkDocsAdapter,
    while carrying the is_compatibility_mode flag for upstream reporting.
    """

    def __init__(self, adapter: MkDocsAdapter) -> None:
        self._adapter = adapter
        self.is_compatibility_mode = True

    def is_locale_dir(self, part: str) -> bool:
        return self._adapter.is_locale_dir(part)

    def resolve_asset(self, missing_abs: Path, docs_root: Path) -> Path | None:
        return self._adapter.resolve_asset(missing_abs, docs_root)

    def resolve_anchor(
        self, resolved_file: Path, anchor: str, anchors_cache: dict[Path, set[str]], docs_root: Path
    ) -> bool:
        return self._adapter.resolve_anchor(resolved_file, anchor, anchors_cache, docs_root)

    def is_shadow_of_nav_page(self, rel: Path, nav_paths: frozenset[str]) -> bool:
        return self._adapter.is_shadow_of_nav_page(rel, nav_paths)

    def get_ignored_patterns(self) -> set[str]:
        return self._adapter.get_ignored_patterns()

    def get_nav_paths(self) -> frozenset[str]:
        return self._adapter.get_nav_paths()

    def has_engine_config(self) -> bool:
        return self._adapter.has_engine_config()

    def get_metadata_files(self) -> frozenset[str]:
        return self._adapter.get_metadata_files()

    def map_url(self, rel: Path) -> str:
        return self._adapter.map_url(rel)

    def classify_route(self, rel: Path, nav_paths: frozenset[str]) -> RouteStatus:
        return self._adapter.classify_route(rel, nav_paths)

    def get_route_info(self, rel: Path) -> RouteMetadata:
        return self._adapter.get_route_info(rel)

    def provides_index(self, directory_path: Path) -> bool:
        return self._adapter.provides_index(directory_path)

    def get_link_scheme_bypasses(self) -> frozenset[str]:
        return self._adapter.get_link_scheme_bypasses()


class ZensicalAdapter:
    """Adapter for the Zensical build engine — reads ``zensical.toml`` natively.

    Zero YAML.  All configuration is sourced from ``zensical.toml``.
    Navigation is declared under ``[project].nav`` (Zensical v0.0.31+)::

        [project]
        site_name = "My Docs"
        nav = [
            "index.md",
            {"Guide" = "guide.md"},
            {"API" = ["api/index.md", {"Endpoints" = "api/endpoints.md"}]},
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

        # Pre-compute nav state from [project].nav in zensical.toml.
        _project = self._zensical_config.get("project", {})
        _raw_nav: list[object] = _project.get("nav", [])
        self._nav_paths: frozenset[str] = frozenset(_extract_nav_paths(_raw_nav))
        # True only when the user supplied an explicit, non-empty nav list.
        self._has_explicit_nav: bool = bool(_raw_nav)
        # Offline Mode Tactical Fix
        if context.offline_mode:
            self._use_directory_urls = False
        else:
            self._use_directory_urls = bool(_project.get("use_directory_urls", True))

    # ── Public contract ────────────────────────────────────────────────────────

    def is_locale_dir(self, part: str) -> bool:
        """Return ``True`` when *part* is a non-default locale directory name."""
        return part in self._locale_dirs

    def resolve_asset(self, missing_abs: Path, docs_root: Path) -> Path | None:
        """Return the default-locale fallback for a missing asset, or ``None``."""
        if not self._fallback_to_default:
            return None
        fallback = remap_to_default_locale(missing_abs, docs_root, self._locale_dirs)
        return fallback if fallback is not None and case_sensitive_exists(fallback) else None

    def resolve_anchor(
        self,
        resolved_file: Path,
        anchor: str,
        anchors_cache: dict[Path, set[str]],
        docs_root: Path,
    ) -> bool:
        """Return ``True`` if an anchor miss should be suppressed via i18n fallback.

        Locale configuration is sourced from ``BuildContext`` (``zenzic.toml``).

        Args:
            resolved_file: Absolute path of the locale file whose anchor set
                does not contain *anchor*.
            anchor: Fragment identifier that was not found (without ``#``).
            anchors_cache: Pre-built ``Path`` → anchor slug set mapping.
            docs_root: Resolved absolute ``docs/`` root.

        Returns:
            ``True`` if the anchor exists in the default-locale equivalent file.
        """
        if not self._fallback_to_default:
            return False
        default_file = remap_to_default_locale(resolved_file, docs_root, self._locale_dirs)
        if default_file is None:
            return False
        return anchor.lower() in anchors_cache.get(default_file, set())

    def is_shadow_of_nav_page(self, rel: Path, nav_paths: frozenset[str]) -> bool:
        """Return ``True`` when *rel* is a locale-mirror of a nav-listed page."""
        default_abs = remap_to_default_locale(
            self._docs_root / rel, self._docs_root, self._locale_dirs
        )
        if default_abs is None:
            return False
        return default_abs.relative_to(self._docs_root).as_posix() in nav_paths

    def get_ignored_patterns(self) -> set[str]:
        """Empty set — Zensical does not use MkDocs suffix-mode i18n patterns."""
        return set()

    def has_engine_config(self) -> bool:
        """``True`` — ZensicalAdapter is constructed only when zensical.toml exists."""
        return True

    def get_metadata_files(self) -> frozenset[str]:
        """Zensical configuration file — shielded from Z903."""
        return frozenset({"zensical.toml"})

    # ── VSM integration ────────────────────────────────────────────────────────

    def map_url(self, rel: Path) -> str:
        """Map a physical source path to its Zensical canonical URL.

        Zensical always serves clean directory-style URLs.  Both ``index.md``
        and ``README.md`` collapse to the parent directory URL (Zensical treats
        ``README.md`` as an implicit index).

        With ``use_directory_urls = true`` (default)::

            page.md        → /page/
            dir/index.md   → /dir/
            dir/README.md  → /dir/   (same URL → CONFLICT if both exist)
            index.md       → /

        With ``use_directory_urls = false``::

            page.md        → /page.html
            dir/index.md   → /dir/index.html
            index.md       → /index.html

        Files inside ``_private``-prefixed path segments are mapped normally
        here; ``classify_route()`` marks them ``IGNORED``.

        Args:
            rel: Path of the source file relative to ``docs_root``.

        Returns:
            Canonical URL string with leading slash.
        """
        if not self._use_directory_urls:
            # Flat URL mode: preserve suffix, no directory collapsing.
            return "/" + rel.as_posix()

        stem = rel.with_suffix("")
        parts = list(stem.parts)
        if not parts:
            return "/"
        if parts[-1] in ("index", "README"):
            parts = parts[:-1]
        if not parts:
            return "/"
        return "/" + "/".join(parts) + "/"

    def classify_route(self, rel: Path, nav_paths: frozenset[str]) -> RouteStatus:
        """Classify a Zensical route by filesystem and nav rules.

        Priority chain:

        1. ``IGNORED`` — any path segment starts with ``_``.
        2. ``ORPHAN_BUT_EXISTING`` — an explicit ``[project].nav`` is defined
           in ``zensical.toml`` and *rel* is not listed in it.  The file is
           served (Zensical is filesystem-based) but is not sidebar-navigable.
        3. ``REACHABLE`` — all other files when no explicit nav is declared.

        Args:
            rel:       Source path relative to ``docs_root``.
            nav_paths: Frozenset of nav-listed paths from ``get_nav_paths()``.

        Returns:
            ``'IGNORED'``, ``'ORPHAN_BUT_EXISTING'``, or ``'REACHABLE'``.
        """
        if any(part.startswith("_") for part in rel.parts):
            return "IGNORED"
        if self._has_explicit_nav and rel.as_posix() not in nav_paths:
            return "ORPHAN_BUT_EXISTING"
        return "REACHABLE"

    def get_nav_paths(self) -> frozenset[str]:
        """Return ``.md`` paths from ``[project].nav`` in ``zensical.toml``.

        Supports all Zensical v0.0.31+ nav variants — plain strings, titled
        pages, nested sections (see :func:`_extract_nav_paths`).

        Returns:
            Frozenset of nav-listed ``.md`` paths, relative to ``docs_root``
            and without leading slash.  Empty frozenset when no explicit
            ``[project].nav`` is declared.
        """
        return self._nav_paths

    def get_route_info(self, rel: Path) -> RouteMetadata:
        """Return unified routing metadata for a Zensical source file.

        Zensical does not support frontmatter ``slug:`` — the slug field is
        always ``None``.  Files under ``_private/`` directories are ``IGNORED``.
        """
        from zenzic.core.adapters._base import RouteMetadata

        nav_paths = self.get_nav_paths()
        return RouteMetadata(
            canonical_url=self.map_url(rel),
            status=self.classify_route(rel, nav_paths),
        )

    def provides_index(self, directory_path: Path) -> bool:
        """Return ``True`` when Zensical will serve an index page for this directory.

        Zensical uses ``index.md`` as the canonical index file for a directory,
        rendering it at the directory URL without a filename suffix.

        I/O is permitted here — this method is called once per directory during
        the discovery phase, never inside per-link or per-file hot loops.

        Args:
            directory_path: Absolute path to the directory to inspect.

        Returns:
            ``True`` if an ``index.md`` exists in the directory.
        """
        return (directory_path / "index.md").exists()

    def get_link_scheme_bypasses(self) -> frozenset[str]:
        """Zensical has no engine-specific link-scheme bypass."""
        return frozenset()

    @classmethod
    def from_repo(
        cls,
        context: BuildContext,
        docs_root: Path,
        repo_root: Path,
    ) -> ZensicalAdapter | ZensicalLegacyProxy:
        """Construct from a live repository root.

        Enforces the Zensical contract: if ``zensical.toml`` is missing but
        ``mkdocs.yml`` is present, returns a ZensicalLegacyProxy that delegates
        to MkDocsAdapter, enabling a seamless migration path.
        """
        if find_zensical_config(repo_root) is not None:
            return cls(context, docs_root, _load_zensical_config(repo_root))

        # Transparent Bridge: fallback to MkDocs config
        if find_config_file(repo_root) is not None:
            mkdocs_config = _load_doc_config(repo_root)
            # Warn about unsupported keys
            for key in _UNSUPPORTED_MKDOCS_KEYS:
                if key in mkdocs_config:
                    _log.warning(
                        "Zensical ignores MkDocs '%s' parameter — it will not affect the build.",
                        key,
                    )

            # Delegate to MkDocsAdapter
            adapter = MkDocsAdapter(context, docs_root, mkdocs_config, config_file_found=True)
            return ZensicalLegacyProxy(adapter)

        # Neither config exists
        raise ConfigurationError(
            "engine 'zensical' declared in zenzic.toml but no configuration file was found",
            context={
                "repo_root": str(repo_root),
                "hint": "create zensical.toml (or mkdocs.yml for legacy mode)",
            },
        )
