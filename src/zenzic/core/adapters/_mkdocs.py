# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""MkDocsAdapter — adapter for MkDocs folder-mode and suffix-mode i18n.

This module also owns all MkDocs-specific parsing utilities (YAML loading,
i18n plugin extraction, nav traversal).  The Scanner and Validator are pure
consumers of the adapter API and never import from this module directly.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from zenzic.core.exceptions import ConfigurationError
from zenzic.models.config import BuildContext


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
        try:
            rel = missing_abs.relative_to(docs_root)
        except ValueError:
            return None
        if not rel.parts or rel.parts[0] not in self._locale_dirs:
            return None
        fallback = docs_root.joinpath(*rel.parts[1:])
        return fallback if fallback.exists() else None

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
        if not rel.parts or rel.parts[0] not in self._locale_dirs:
            return False
        default_rel = Path(*rel.parts[1:]).as_posix()
        return default_rel in nav_paths

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
