# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Build-engine adapters for locale-aware path resolution.

Public API
----------
All symbols below are importable from either ``zenzic.core.adapters`` or
the legacy alias ``zenzic.core.adapter`` (both resolve to the same objects).

Classes:
    BaseAdapter       — ``@runtime_checkable`` Protocol every adapter must satisfy.
    MkDocsAdapter     — Folder-mode and suffix-mode i18n for MkDocs projects.
    ZensicalAdapter   — Native TOML-based adapter for Zensical projects.
    VanillaAdapter    — No-op adapter for projects with no recognised engine.

Factory:
    get_adapter(context, docs_root, repo_root) → adapter instance.

MkDocs utilities (also used by tests and ``check_nav_contract``):
    find_config_file, _load_doc_config,
    _extract_i18n_locale_patterns, _extract_i18n_locale_dirs,
    _extract_i18n_fallback_to_default, _validate_i18n_fallback_config,
    _collect_nav_paths, _PermissiveYamlLoader.

Zensical utilities:
    find_zensical_config, _load_zensical_config.
"""

from __future__ import annotations

from ._base import BaseAdapter, RouteMetadata
from ._docusaurus import (
    DocusaurusAdapter,
    _extract_base_url,
    _extract_frontmatter_slug,
    _extract_route_base_path,
    _is_dynamic_config,
    _strip_js_comments,
    find_docusaurus_config,
)
from ._factory import get_adapter, list_adapter_engines
from ._mkdocs import (
    MkDocsAdapter,
    _collect_nav_paths,
    _extract_i18n_fallback_to_default,
    _extract_i18n_locale_dirs,
    _extract_i18n_locale_patterns,
    _load_doc_config,
    _PermissiveYamlLoader,
    _validate_i18n_fallback_config,
    find_config_file,
)
from ._vanilla import VanillaAdapter
from ._zensical import ZensicalAdapter, _load_zensical_config, find_zensical_config


__all__ = [
    # Protocol & Metadata
    "BaseAdapter",
    "RouteMetadata",
    # Adapters
    "DocusaurusAdapter",
    "MkDocsAdapter",
    "ZensicalAdapter",
    "VanillaAdapter",
    # Factory
    "get_adapter",
    "list_adapter_engines",
    # MkDocs utilities
    "find_config_file",
    "_load_doc_config",
    "_PermissiveYamlLoader",
    "_collect_nav_paths",
    "_extract_i18n_locale_patterns",
    "_extract_i18n_locale_dirs",
    "_extract_i18n_fallback_to_default",
    "_validate_i18n_fallback_config",
    # Zensical utilities
    "find_zensical_config",
    "_load_zensical_config",
    # Docusaurus utilities
    "find_docusaurus_config",
    "_extract_base_url",
    "_extract_route_base_path",
    "_extract_frontmatter_slug",
    "_is_dynamic_config",
    "_strip_js_comments",
]
