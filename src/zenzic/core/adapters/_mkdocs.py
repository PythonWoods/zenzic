# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""MkDocsAdapter — adapter for MkDocs folder-mode and suffix-mode i18n.

This module also owns all MkDocs-specific parsing utilities (YAML loading,
i18n plugin extraction, nav traversal).  The Scanner and Validator are pure
consumers of the adapter API and never import from this module directly.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from zenzic.core.adapters._utils import remap_to_default_locale
from zenzic.core.exceptions import ConfigurationError
from zenzic.models.config import BuildContext


_log = logging.getLogger(__name__)


if TYPE_CHECKING:
    from zenzic.models.vsm import RouteStatus


# ── YAML loader ───────────────────────────────────────────────────────────────


class _PermissiveYamlLoader(yaml.SafeLoader):
    """SafeLoader that silently ignores unknown tags (e.g. MkDocs ``!ENV``)."""


_PermissiveYamlLoader.add_multi_constructor("", lambda loader, tag_suffix, node: None)  # type: ignore[no-untyped-call]


# ── Config discovery & loading ────────────────────────────────────────────────


def find_config_file(repo_root: Path) -> Path | None:
    """Return the MkDocs config file path, or ``None`` if absent."""
    mkdocs_yml = repo_root / "mkdocs.yml"
    return mkdocs_yml if mkdocs_yml.exists() else None


def _load_doc_config(repo_root: Path) -> dict[str, Any]:
    """Load and parse ``mkdocs.yml``, returning ``{}`` on any failure."""
    config_file = find_config_file(repo_root)
    if config_file is None:
        return {}
    with config_file.open(encoding="utf-8") as f:
        try:
            return yaml.load(f, Loader=_PermissiveYamlLoader) or {}  # noqa: S506
        except yaml.YAMLError:
            return {}


# ── i18n plugin extraction helpers ───────────────────────────────────────────


def _extract_i18n_locale_patterns(doc_config: dict[str, Any]) -> set[str]:
    """Return filename glob patterns for non-default i18n locales (suffix mode).

    Reads the ``mkdocs-i18n`` plugin block and returns patterns like
    ``{'*.it.md', '*.fr.md'}`` when ``docs_structure: suffix`` is active.
    Returns an empty set for any other configuration (no plugin, folder
    structure, etc.).

    Only valid ISO 639-1 two-letter lowercase codes produce patterns.
    Version tags (``v1``), build tags (``beta``), and BCP 47 region codes
    are silently rejected.
    """
    patterns: set[str] = set()
    plugins = doc_config.get("plugins", [])
    if not isinstance(plugins, list):
        return patterns
    for plugin in plugins:
        if not isinstance(plugin, dict):
            continue
        i18n_config = plugin.get("i18n")
        if not isinstance(i18n_config, dict):
            continue
        if i18n_config.get("docs_structure") != "suffix":
            break
        for lang in i18n_config.get("languages") or []:
            if not isinstance(lang, dict):
                continue
            if not lang.get("default", False):
                locale = lang.get("locale", "")
                # ISO 639-1: exactly two lowercase ASCII letters.
                if locale and re.fullmatch(r"[a-z]{2}", locale):
                    patterns.add(f"*.{locale}.md")
        break
    return patterns


def _extract_i18n_locale_dirs(doc_config: dict[str, Any]) -> set[str]:
    """Return locale directory names for non-default i18n locales (folder mode).

    Reads the ``mkdocs-i18n`` plugin block and returns directory names like
    ``{'it', 'fr'}`` when ``docs_structure: folder`` is active.

    Returns an empty set for any other configuration (no plugin, suffix
    structure, missing locale list, etc.).

    Args:
        doc_config: Parsed documentation generator config (e.g. from mkdocs.yml).

    Returns:
        Set of non-default locale directory names, e.g. ``{'it', 'fr'}``.
    """
    dirs: set[str] = set()
    plugins = doc_config.get("plugins", [])
    if not isinstance(plugins, list):
        return dirs
    for plugin in plugins:
        if not isinstance(plugin, dict):
            continue
        i18n_config = plugin.get("i18n")
        if not isinstance(i18n_config, dict):
            continue
        if i18n_config.get("docs_structure") != "folder":
            break
        for lang in i18n_config.get("languages") or []:
            if not isinstance(lang, dict):
                continue
            if not lang.get("default", False):
                locale = lang.get("locale", "")
                if locale:
                    dirs.add(locale)
        break
    return dirs


def _extract_i18n_reconfigure_material(doc_config: dict[str, Any]) -> bool:
    """Return ``True`` when the i18n plugin has ``reconfigure_material: true``.

    When this flag is active, ``mkdocs-material`` auto-generates the language
    switcher and the alternate-locale entry points (e.g. ``/it/``) at build
    time.  These routes are **not** listed in ``nav:`` or ``extra.alternate``
    and must therefore be treated as auto-generated REACHABLE routes in the
    VSM — otherwise Zenzic would flag the locale index pages as orphans.

    Only meaningful when ``docs_structure: folder`` is active; returns
    ``False`` for suffix mode and for configs that omit the setting (the
    plugin default is ``false``).

    Args:
        doc_config: Parsed documentation generator config (e.g. from mkdocs.yml).

    Returns:
        ``True`` when ``reconfigure_material: true`` is set on the i18n plugin
        block with ``docs_structure: folder``; ``False`` otherwise.
    """
    plugins = doc_config.get("plugins", [])
    if not isinstance(plugins, list):
        return False
    for plugin in plugins:
        if not isinstance(plugin, dict):
            continue
        i18n_config = plugin.get("i18n")
        if not isinstance(i18n_config, dict):
            continue
        if i18n_config.get("docs_structure") != "folder":
            return False
        return bool(i18n_config.get("reconfigure_material", False))
    return False


def _detect_redundant_alternate(doc_config: dict[str, Any]) -> bool:
    """Return ``True`` when ``reconfigure_material: true`` and ``extra.alternate`` coexist.

    This combination is redundant: ``reconfigure_material`` delegates the
    language switcher to the i18n plugin, which auto-generates it from the
    ``languages`` list.  A manual ``extra.alternate`` block then competes with
    the auto-generated switcher and causes the switcher to disappear in some
    plugin versions.

    This is a pure diagnostic helper — it reads only the already-parsed config
    dict and has no side effects.

    Args:
        doc_config: Parsed documentation generator config (e.g. from mkdocs.yml).

    Returns:
        ``True`` when both ``reconfigure_material: true`` and ``extra.alternate``
        are present; ``False`` otherwise.
    """
    if not _extract_i18n_reconfigure_material(doc_config):
        return False
    alternate = doc_config.get("extra", {})
    if not isinstance(alternate, dict):
        return False
    return bool(alternate.get("alternate"))


def _extract_i18n_fallback_to_default(doc_config: dict[str, Any]) -> bool:
    """Return the ``fallback_to_default`` value from the i18n plugin block.

    Returns ``True`` (the plugin default) when the setting is absent or
    the plugin block cannot be found.
    """
    plugins = doc_config.get("plugins", [])
    if not isinstance(plugins, list):
        return True
    for plugin in plugins:
        if not isinstance(plugin, dict):
            continue
        i18n_config = plugin.get("i18n")
        if not isinstance(i18n_config, dict):
            continue
        return bool(i18n_config.get("fallback_to_default", True))
    return True


def _validate_i18n_fallback_config(doc_config: dict[str, Any]) -> None:
    """Raise ConfigurationError when fallback_to_default is true but no default locale exists.

    Only active for ``docs_structure: folder`` with ``fallback_to_default: true``.
    No-op for suffix mode, unconfigured projects, or when a default locale is present.

    Raises:
        :class:`~zenzic.core.exceptions.ConfigurationError`: When the i18n plugin
            requires fallback but cannot determine the fallback target locale.
    """
    plugins = doc_config.get("plugins")
    if not isinstance(plugins, list):
        return
    for plugin in plugins:
        if not isinstance(plugin, dict):
            continue
        i18n = plugin.get("i18n")
        if not isinstance(i18n, dict):
            continue
        if i18n.get("docs_structure") != "folder":
            break
        if not i18n.get("fallback_to_default", False):
            break
        default_locale = ""
        locale_dirs: set[str] = set()
        for lang in i18n.get("languages") or []:
            if not isinstance(lang, dict):
                continue
            locale = lang.get("locale", "")
            if not locale:
                continue
            if lang.get("default", False):
                default_locale = locale
            else:
                locale_dirs.add(locale)
        if not locale_dirs and not default_locale:
            break
        if not default_locale:
            raise ConfigurationError(
                "i18n plugin has fallback_to_default: true but no language with "
                "default: true — Zenzic cannot determine the fallback target locale.",
                context={"docs_structure": "folder", "fallback_to_default": True},
            )
        break


# ── Nav traversal ─────────────────────────────────────────────────────────────


def _collect_nav_paths(nav: list[Any] | dict[str, Any] | str | None, acc: set[str]) -> None:
    """Recursively walk the mkdocs nav structure and collect all .md paths."""
    if nav is None:
        return
    if isinstance(nav, str):
        acc.add(nav)
        return
    if isinstance(nav, dict):
        for value in nav.values():
            if isinstance(value, str):
                acc.add(value)
            else:
                _collect_nav_paths(value, acc)
        return
    if isinstance(nav, list):
        for item in nav:
            _collect_nav_paths(item, acc)


# ── Adapter ───────────────────────────────────────────────────────────────────


class MkDocsAdapter:
    """Adapter for MkDocs folder-mode and suffix-mode i18n.

    In folder mode every non-default locale lives in a top-level directory
    under ``docs/`` whose name equals the locale code (e.g. ``docs/it/``).
    In suffix mode, translated pages are named ``page.it.md`` alongside the
    default ``page.md``.

    Assets are **shared** — ``docs/it/index.md`` may reference
    ``assets/logo.svg`` intending ``docs/assets/logo.svg`` (the build engine
    resolves them relative to the site root, not the locale sub-tree).

    Args:
        context: :class:`~zenzic.models.config.BuildContext` loaded from
            ``zenzic.toml``.  Provides ``locales`` and ``default_locale``.
            When ``context.locales`` is empty the adapter falls back to
            extracting locale information from *doc_config*.
        docs_root: Resolved absolute path to the ``docs/`` directory.
        doc_config: Pre-parsed documentation generator config dict (e.g. the
            contents of ``mkdocs.yml``).  When provided and
            ``context.locales`` is empty, locale dirs and fallback behaviour
            are derived from this config rather than hard-coded defaults.
    """

    def __init__(
        self,
        context: BuildContext,
        docs_root: Path,
        doc_config: dict[str, Any] | None = None,
        *,
        config_file_found: bool = False,
    ) -> None:
        self._docs_root = docs_root
        self._doc_config: dict[str, Any] = doc_config if doc_config is not None else {}
        self._config_file_found: bool = config_file_found

        # Validate i18n fallback configuration eagerly so callers get a clear
        # ConfigurationError rather than silent misbehaviour at link-check time.
        _validate_i18n_fallback_config(self._doc_config)

        # Locales: prefer explicit context (from zenzic.toml); fall back to
        # extraction from the engine config (mkdocs.yml) when absent.
        if context.locales:
            self._locale_dirs: frozenset[str] = frozenset(context.locales)
            self._fallback_to_default: bool = context.fallback_to_default
        else:
            self._locale_dirs = frozenset(_extract_i18n_locale_dirs(self._doc_config))
            self._fallback_to_default = _extract_i18n_fallback_to_default(self._doc_config)

        # When reconfigure_material: true the Material theme auto-generates
        # the language switcher and the locale entry points (e.g. /it/) at
        # build time.  These routes never appear in nav: so classify_route()
        # must treat locale index pages as REACHABLE without nav evidence.
        self._reconfigure_material: bool = _extract_i18n_reconfigure_material(self._doc_config)

        # Emit a UX hint when the config is redundant: reconfigure_material
        # auto-generates the switcher, so extra.alternate is both unnecessary
        # and harmful (it competes with the plugin and can hide the switcher).
        if _detect_redundant_alternate(self._doc_config):
            _log.warning(
                "mkdocs.yml: 'extra.alternate' is redundant when "
                "'plugins.i18n.reconfigure_material: true' is set. "
                "The i18n plugin auto-generates the language switcher from the "
                "'languages' list — remove 'extra.alternate' to avoid routing "
                "conflicts that can cause the language switcher to disappear."
            )

    # ── Public contract ────────────────────────────────────────────────────────

    def is_locale_dir(self, part: str) -> bool:
        """Return ``True`` when *part* is a non-default locale directory name."""
        return part in self._locale_dirs

    def resolve_asset(self, missing_abs: Path, docs_root: Path) -> Path | None:
        """Return the default-locale fallback for a missing asset, or ``None``.

        When a file inside a locale sub-tree (e.g. ``docs/it/``) references
        an asset using a path that resolves to ``docs/it/assets/logo.svg``
        (which does not exist), this method checks whether the corresponding
        default-locale path ``docs/assets/logo.svg`` exists and returns it.

        Args:
            missing_abs: Absolute path that was not found on disk.
            docs_root: Resolved absolute ``docs/`` root (for path stripping).

        Returns:
            Resolved absolute :class:`~pathlib.Path` of the fallback asset, or
            ``None`` if no fallback exists.
        """
        if not self._fallback_to_default:
            return None
        fallback = remap_to_default_locale(missing_abs, docs_root, self._locale_dirs)
        return fallback if fallback is not None and fallback.exists() else None

    def resolve_anchor(
        self,
        resolved_file: Path,
        anchor: str,
        anchors_cache: dict[Path, set[str]],
        docs_root: Path,
    ) -> bool:
        """Return ``True`` if an anchor miss should be suppressed via i18n fallback.

        When a locale file (e.g. ``docs/it/architecture.md``) exists but does
        not contain the requested anchor — because its headings are translated —
        this method checks whether the anchor exists in the default-locale
        equivalent (e.g. ``docs/architecture.md``).  If it does, MkDocs will
        serve the default-locale page for this anchor, so the error is spurious.

        The check is pure: only ``anchors_cache`` (already in memory) is
        consulted.  No disk I/O occurs.

        Args:
            resolved_file: Absolute path of the locale file that was found but
                whose anchor set does not contain *anchor*.
            anchor: The fragment identifier that was not found (without ``#``).
            anchors_cache: Pre-built mapping of absolute ``Path`` → anchor slug
                set (same mapping used by :class:`~zenzic.core.resolver.InMemoryPathResolver`).
            docs_root: Resolved absolute ``docs/`` root (for path stripping).

        Returns:
            ``True`` if the anchor exists in the default-locale equivalent file;
            ``False`` otherwise.
        """
        if not self._fallback_to_default:
            return False
        default_file = remap_to_default_locale(resolved_file, docs_root, self._locale_dirs)
        if default_file is None:
            return False
        return anchor.lower() in anchors_cache.get(default_file, set())

    def is_shadow_of_nav_page(self, rel: Path, nav_paths: frozenset[str]) -> bool:
        """Return ``True`` when *rel* is a locale-mirror of a nav-listed page.

        A file ``it/about/index.md`` is a shadow of ``about/index.md``.  If
        ``about/index.md`` appears in the nav the shadow is not an orphan —
        it inherits its nav membership from the default-locale original.

        Args:
            rel: Path of the candidate file, relative to ``docs_root``.
            nav_paths: Frozenset of ``.md`` paths listed in the nav.

        Returns:
            ``True`` when the file is a shadow of a nav-listed page.
        """
        default_abs = remap_to_default_locale(
            self._docs_root / rel, self._docs_root, self._locale_dirs
        )
        if default_abs is None:
            return False
        return default_abs.relative_to(self._docs_root).as_posix() in nav_paths

    def get_ignored_patterns(self) -> set[str]:
        """Return filename glob patterns for non-default locale files (suffix mode)."""
        return _extract_i18n_locale_patterns(self._doc_config)

    def get_nav_paths(self) -> frozenset[str]:
        """Return ``.md`` paths listed in the nav, relative to ``docs_root``."""
        raw: set[str] = set()
        _collect_nav_paths(self._doc_config.get("nav"), raw)
        return frozenset(p.lstrip("/") for p in raw if p.endswith(".md"))

    def has_engine_config(self) -> bool:
        """``True`` when ``mkdocs.yml`` was found on disk **or** locales were declared.

        Returns ``False`` only when both the engine config file is absent
        **and** no locales were declared in ``zenzic.toml`` — the truly bare
        scenario where the adapter has no nav or i18n information to contribute.
        """
        return self._config_file_found or bool(self._locale_dirs)

    # ── VSM integration ────────────────────────────────────────────────────────

    def map_url(self, rel: Path) -> str:
        """Map a physical source path to its MkDocs canonical URL.

        Applies the MkDocs ``use_directory_urls`` rule (default ``true``):

        * ``page.md``           → ``/page/``
        * ``dir/index.md``      → ``/dir/``
        * ``dir/README.md``     → ``/dir/``       (same URL as index.md → CONFLICT)
        * ``index.md``          → ``/``           (root)
        * ``page.md`` (no-dir)  → ``/page.html``

        The Double-Index case (``index.md`` **and** ``README.md`` coexist in
        the same directory) produces two routes with the identical URL, which
        ``_detect_collisions()`` will mark as ``CONFLICT``.

        Args:
            rel: Path of the source file relative to ``docs_root``.

        Returns:
            Canonical URL string (always starts and ends with ``/``).
        """
        use_dir = self._doc_config.get("use_directory_urls", True)
        stem = rel.with_suffix("")
        parts = list(stem.parts)
        if not parts:
            return "/"
        # index.md and README.md both collapse to the parent directory URL
        if parts[-1] in ("index", "README"):
            parts = parts[:-1]
        if not parts:
            return "/"
        if use_dir:
            return "/" + "/".join(parts) + "/"
        return "/" + "/".join(parts) + ".html"

    def classify_route(self, rel: Path, nav_paths: frozenset[str]) -> RouteStatus:
        """Classify a MkDocs route as REACHABLE, ORPHAN_BUT_EXISTING, or IGNORED.

        Classification rules (in priority order):

        0. No nav declared (``nav_paths`` empty) → all files ``REACHABLE``
           (MkDocs auto-includes every page when ``nav:`` is absent), except
           ``README.md`` which is always ``IGNORED``.
        1. ``README.md`` **not** listed in nav → ``IGNORED``.
        2. File in nav_paths (or is a locale shadow of a nav page) → ``REACHABLE``.
        3. ``reconfigure_material: true`` and file is a top-level locale entry
           point (e.g. ``it/index.md``) → ``REACHABLE`` (auto-generated route).
           This check fires only when rules 0-2 have not already resolved the
           status, so an explicit nav entry for ``it/index.md`` is never
           overridden.
        4. Otherwise → ``ORPHAN_BUT_EXISTING``.

        Args:
            rel:       Source path relative to ``docs_root``.
            nav_paths: Nav-listed ``.md`` paths from ``get_nav_paths()``.

        Returns:
            ``RouteStatus`` literal (never ``'CONFLICT'``).
        """
        rel_posix = rel.as_posix()

        # When no nav is declared in mkdocs.yml, MkDocs auto-includes every
        # page — equivalent to every file being REACHABLE.  Only README.md
        # is still excluded (MkDocs never auto-promotes it).
        if not nav_paths:
            if rel.name == "README.md":
                return "IGNORED"
            return "REACHABLE"

        # README.md not in nav → IGNORED (MkDocs does not auto-promote it)
        if rel.name == "README.md" and rel_posix not in nav_paths:
            return "IGNORED"

        if rel_posix in nav_paths:
            return "REACHABLE"

        # Locale shadows inherit their nav membership from the default locale
        if self.is_shadow_of_nav_page(rel, nav_paths):
            return "REACHABLE"

        # When reconfigure_material: true, the Material theme auto-generates
        # the language switcher and synthetic entry points for every non-default
        # locale (e.g. docs/it/index.md → /it/).  These pages are never listed
        # in nav: but they are live routes — mark them REACHABLE so Zenzic does
        # not report them as orphans.
        if self._reconfigure_material and rel.name in ("index.md", "README.md"):
            parts = rel.parts
            if len(parts) == 2 and parts[0] in self._locale_dirs:  # e.g. it/index.md
                return "REACHABLE"

        return "ORPHAN_BUT_EXISTING"

    @classmethod
    def from_repo(
        cls,
        context: BuildContext,
        docs_root: Path,
        repo_root: Path,
    ) -> MkDocsAdapter:
        """Construct from a live repository root.

        Loads ``mkdocs.yml`` from *repo_root* and falls back to an empty config
        dict when the file is absent or contains invalid YAML.  The
        ``config_file_found`` flag distinguishes "file absent" from
        "file present but unparseable" — only the former triggers vanilla
        fallback in the factory.
        """
        config_file_found = find_config_file(repo_root) is not None
        return cls(
            context,
            docs_root,
            _load_doc_config(repo_root),
            config_file_found=config_file_found,
        )
