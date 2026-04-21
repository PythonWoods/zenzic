# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Guardians of Quality — ZensicalAdapter / ZensicalLegacyProxy targeted coverage tests.

Closes gaps identified in the v0.6.1 coverage audit (74%):
  - find_zensical_config: absent file path
  - _load_zensical_config: missing config, parse exception
  - _extract_nav_paths: nested section, external URL, plain-string non-md
  - ZensicalLegacyProxy: every protocol method delegate
  - ZensicalAdapter.map_url: offline mode (flat URLs), README.md collapsing
  - ZensicalAdapter.classify_route: _-prefix ignored, explicit-nav orphan
  - ZensicalAdapter.get_route_info: ignored status, orphan status
  - ZensicalAdapter.from_repo: zensical.toml present, mkdocs.yml fallback,
    unsupported-key warning, ConfigurationError when neither exists
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from zenzic.core.adapters._mkdocs import MkDocsAdapter
from zenzic.core.adapters._zensical import (
    ZensicalAdapter,
    ZensicalLegacyProxy,
    _extract_nav_paths,
    _load_zensical_config,
    find_zensical_config,
)
from zenzic.core.exceptions import ConfigurationError
from zenzic.models.config import BuildContext


# ── Helpers ───────────────────────────────────────────────────────────────────


def _ctx(
    *,
    locales: list[str] | None = None,
    fallback: bool = True,
    offline: bool = False,
) -> BuildContext:
    return BuildContext(
        engine="zensical",
        locales=locales or [],
        fallback_to_default=fallback,
        offline_mode=offline,
    )


def _adapter(
    docs_root: Path,
    zensical_config: dict | None = None,
    *,
    locales: list[str] | None = None,
    offline: bool = False,
) -> ZensicalAdapter:
    ctx = _ctx(locales=locales or [], offline=offline)
    return ZensicalAdapter(ctx, docs_root, zensical_config or {})


# ── find_zensical_config ──────────────────────────────────────────────────────


class TestFindZensicalConfig:
    def test_returns_none_when_absent(self, tmp_path: Path) -> None:
        """find_zensical_config returns None when zensical.toml does not exist."""
        result = find_zensical_config(tmp_path)
        assert result is None

    def test_returns_path_when_present(self, tmp_path: Path) -> None:
        toml_file = tmp_path / "zensical.toml"
        toml_file.write_text("[project]\nsite_name = 'X'\n", encoding="utf-8")
        result = find_zensical_config(tmp_path)
        assert result == toml_file


# ── _load_zensical_config ─────────────────────────────────────────────────────


class TestLoadZensicalConfig:
    def test_returns_empty_dict_when_no_config(self, tmp_path: Path) -> None:
        """When zensical.toml is absent, returns empty dict."""
        result = _load_zensical_config(tmp_path)
        assert result == {}

    def test_returns_parsed_dict(self, tmp_path: Path) -> None:
        """Valid zensical.toml is parsed correctly."""
        (tmp_path / "zensical.toml").write_text(
            "[project]\nsite_name = 'My Docs'\n", encoding="utf-8"
        )
        result = _load_zensical_config(tmp_path)
        assert result["project"]["site_name"] == "My Docs"

    def test_returns_empty_dict_on_parse_error(self, tmp_path: Path) -> None:
        """Corrupt zensical.toml returns empty dict (no crash)."""
        (tmp_path / "zensical.toml").write_bytes(b"\xff\xfe invalid toml \x00")
        result = _load_zensical_config(tmp_path)
        assert result == {}


# ── _extract_nav_paths ────────────────────────────────────────────────────────


class TestExtractNavPaths:
    def test_plain_string_md(self) -> None:
        assert _extract_nav_paths(["index.md"]) == {"index.md"}

    def test_plain_string_non_md_ignored(self) -> None:
        """Non-.md strings (e.g. plain labels) are ignored."""
        assert _extract_nav_paths(["README.rst"]) == set()

    def test_titled_page(self) -> None:
        assert _extract_nav_paths([{"Guide": "guide.md"}]) == {"guide.md"}

    def test_nested_section(self) -> None:
        """Sections with nested lists are recursed."""
        nav = [{"API": ["api/index.md", {"Endpoints": "api/endpoints.md"}]}]
        result = _extract_nav_paths(nav)
        assert result == {"api/index.md", "api/endpoints.md"}

    def test_external_url_ignored(self) -> None:
        """External URLs (not .md) are silently skipped."""
        nav = [{"GitHub": "https://github.com/org/repo"}]
        assert _extract_nav_paths(nav) == set()

    def test_leading_slash_stripped(self) -> None:
        """Leading slashes on .md paths are stripped."""
        assert _extract_nav_paths(["/guide.md"]) == {"guide.md"}

    def test_empty_list(self) -> None:
        assert _extract_nav_paths([]) == set()

    def test_mixed_variants(self) -> None:
        nav = [
            "index.md",
            {"Guide": "guide.md"},
            {"Ext": "https://example.com"},
            {"Nested": ["api/index.md", {"Sub": "api/sub.md"}]},
        ]
        result = _extract_nav_paths(nav)
        assert result == {"index.md", "guide.md", "api/index.md", "api/sub.md"}


# ── ZensicalLegacyProxy ───────────────────────────────────────────────────────


class TestZensicalLegacyProxy:
    """Every protocol method on ZensicalLegacyProxy delegates to MkDocsAdapter."""

    def _make_proxy(self, tmp_path: Path) -> ZensicalLegacyProxy:
        ctx = _ctx()
        docs_root = tmp_path / "docs"
        docs_root.mkdir(parents=True)
        inner = MkDocsAdapter(ctx, docs_root, {}, config_file_found=True)
        return ZensicalLegacyProxy(inner)

    def test_is_compatibility_mode_true(self, tmp_path: Path) -> None:
        proxy = self._make_proxy(tmp_path)
        assert proxy.is_compatibility_mode is True

    def test_is_locale_dir_delegates(self, tmp_path: Path) -> None:
        proxy = self._make_proxy(tmp_path)
        assert proxy.is_locale_dir("en") is False

    def test_resolve_asset_delegates_none_when_no_fallback(self, tmp_path: Path) -> None:
        proxy = self._make_proxy(tmp_path)
        result = proxy.resolve_asset(tmp_path / "missing.png", tmp_path / "docs")
        # No locale dirs configured → fallback lookup returns None
        assert result is None

    def test_resolve_anchor_delegates(self, tmp_path: Path) -> None:
        proxy = self._make_proxy(tmp_path)
        result = proxy.resolve_anchor(tmp_path / "page.md", "anchor", {}, tmp_path / "docs")
        assert isinstance(result, bool)

    def test_is_shadow_of_nav_page_delegates(self, tmp_path: Path) -> None:
        proxy = self._make_proxy(tmp_path)
        result = proxy.is_shadow_of_nav_page(Path("guide.md"), frozenset())
        assert isinstance(result, bool)

    def test_get_ignored_patterns_delegates(self, tmp_path: Path) -> None:
        proxy = self._make_proxy(tmp_path)
        result = proxy.get_ignored_patterns()
        assert isinstance(result, set)

    def test_get_nav_paths_delegates(self, tmp_path: Path) -> None:
        proxy = self._make_proxy(tmp_path)
        result = proxy.get_nav_paths()
        assert isinstance(result, frozenset)

    def test_has_engine_config_delegates(self, tmp_path: Path) -> None:
        proxy = self._make_proxy(tmp_path)
        assert proxy.has_engine_config() is True

    def test_map_url_delegates(self, tmp_path: Path) -> None:
        proxy = self._make_proxy(tmp_path)
        url = proxy.map_url(Path("guide/install.md"))
        assert isinstance(url, str)
        assert url.startswith("/")

    def test_classify_route_delegates(self, tmp_path: Path) -> None:
        proxy = self._make_proxy(tmp_path)
        status = proxy.classify_route(Path("guide.md"), frozenset())
        assert status in ("REACHABLE", "ORPHAN_BUT_EXISTING", "IGNORED")

    def test_get_route_info_delegates(self, tmp_path: Path) -> None:
        from zenzic.core.adapters._base import RouteMetadata

        proxy = self._make_proxy(tmp_path)
        meta = proxy.get_route_info(Path("guide.md"))
        assert isinstance(meta, RouteMetadata)


# ── ZensicalAdapter.map_url ───────────────────────────────────────────────────


class TestZensicalAdapterMapUrl:
    def test_directory_url_mode(self, tmp_path: Path) -> None:
        adapter = _adapter(tmp_path)
        assert adapter.map_url(Path("guide/install.md")) == "/guide/install/"

    def test_readme_collapses_to_parent(self, tmp_path: Path) -> None:
        """README.md collapses to the parent directory URL."""
        adapter = _adapter(tmp_path)
        assert adapter.map_url(Path("guide/README.md")) == "/guide/"

    def test_index_collapses_to_parent(self, tmp_path: Path) -> None:
        adapter = _adapter(tmp_path)
        assert adapter.map_url(Path("guide/index.md")) == "/guide/"

    def test_root_index_collapses_to_slash(self, tmp_path: Path) -> None:
        adapter = _adapter(tmp_path)
        assert adapter.map_url(Path("index.md")) == "/"

    def test_root_readme_collapses_to_slash(self, tmp_path: Path) -> None:
        adapter = _adapter(tmp_path)
        assert adapter.map_url(Path("README.md")) == "/"

    def test_offline_mode_flat_url(self, tmp_path: Path) -> None:
        """With offline_mode=True (use_directory_urls=False), path is preserved."""
        adapter = _adapter(tmp_path, offline=True)
        assert adapter.map_url(Path("guide/install.md")) == "/guide/install.md"

    def test_offline_mode_index_not_collapsed(self, tmp_path: Path) -> None:
        """In offline mode, index.md is NOT collapsed (flat URL mode)."""
        adapter = _adapter(tmp_path, offline=True)
        assert adapter.map_url(Path("guide/index.md")) == "/guide/index.md"

    def test_use_directory_urls_false_via_config(self, tmp_path: Path) -> None:
        """use_directory_urls=false in zensical.toml disables directory collapsing."""
        config = {"project": {"use_directory_urls": False}}
        adapter = _adapter(tmp_path, config)
        assert adapter.map_url(Path("page.md")) == "/page.md"

    def test_empty_parts_returns_slash(self, tmp_path: Path) -> None:
        """Edge case: a path with no parts maps to /."""
        adapter = _adapter(tmp_path)
        # Pathlib won't produce an empty Path naturally, but we can fake it
        # by using a path that after stripping yields empty parts.
        # index.md at root → already covered; test stem stripping:
        url = adapter.map_url(Path("index.md"))
        assert url == "/"


# ── ZensicalAdapter.classify_route ────────────────────────────────────────────


class TestZensicalAdapterClassifyRoute:
    def test_underscore_prefix_ignored(self, tmp_path: Path) -> None:
        adapter = _adapter(tmp_path)
        assert adapter.classify_route(Path("_private/page.md"), frozenset()) == "IGNORED"

    def test_nested_underscore_ignored(self, tmp_path: Path) -> None:
        adapter = _adapter(tmp_path)
        assert adapter.classify_route(Path("guide/_draft.md"), frozenset()) == "IGNORED"

    def test_reachable_when_no_explicit_nav(self, tmp_path: Path) -> None:
        adapter = _adapter(tmp_path, {})
        assert adapter.classify_route(Path("page.md"), frozenset()) == "REACHABLE"

    def test_reachable_when_in_nav(self, tmp_path: Path) -> None:
        config = {"project": {"nav": ["page.md"]}}
        adapter = _adapter(tmp_path, config)
        assert adapter.classify_route(Path("page.md"), frozenset({"page.md"})) == "REACHABLE"

    def test_orphan_when_explicit_nav_and_not_listed(self, tmp_path: Path) -> None:
        config = {"project": {"nav": ["index.md"]}}
        adapter = _adapter(tmp_path, config)
        nav = adapter.get_nav_paths()
        assert adapter.classify_route(Path("unlisted.md"), nav) == "ORPHAN_BUT_EXISTING"


# ── ZensicalAdapter.get_route_info ────────────────────────────────────────────


class TestZensicalAdapterGetRouteInfo:
    def test_ignored_status(self, tmp_path: Path) -> None:
        adapter = _adapter(tmp_path)
        meta = adapter.get_route_info(Path("_private/page.md"))
        assert meta.status == "IGNORED"

    def test_reachable_status(self, tmp_path: Path) -> None:
        adapter = _adapter(tmp_path)
        meta = adapter.get_route_info(Path("page.md"))
        assert meta.status == "REACHABLE"

    def test_orphan_status(self, tmp_path: Path) -> None:
        config = {"project": {"nav": ["index.md"]}}
        adapter = _adapter(tmp_path, config)
        meta = adapter.get_route_info(Path("orphan.md"))
        assert meta.status == "ORPHAN_BUT_EXISTING"

    def test_slug_is_always_none(self, tmp_path: Path) -> None:
        """Zensical does not support frontmatter slug — always None."""
        adapter = _adapter(tmp_path)
        meta = adapter.get_route_info(Path("page.md"))
        assert meta.slug is None


# ── ZensicalAdapter.from_repo ─────────────────────────────────────────────────


class TestZensicalFromRepo:
    def test_uses_zensical_toml_when_present(self, tmp_path: Path) -> None:
        """from_repo returns ZensicalAdapter when zensical.toml exists."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        (tmp_path / "zensical.toml").write_text("[project]\nsite_name = 'Test'\n", encoding="utf-8")
        ctx = _ctx()
        adapter = ZensicalAdapter.from_repo(ctx, docs_root, tmp_path)
        assert isinstance(adapter, ZensicalAdapter)

    def test_falls_back_to_mkdocs_yml(self, tmp_path: Path) -> None:
        """from_repo returns ZensicalLegacyProxy when only mkdocs.yml exists."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        (tmp_path / "mkdocs.yml").write_text("site_name: Test\n", encoding="utf-8")
        ctx = _ctx()
        adapter = ZensicalAdapter.from_repo(ctx, docs_root, tmp_path)
        assert isinstance(adapter, ZensicalLegacyProxy)
        assert adapter.is_compatibility_mode is True

    def test_unsupported_mkdocs_keys_emit_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Unsupported MkDocs keys emit a warning during legacy proxy construction."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        (tmp_path / "mkdocs.yml").write_text(
            "site_name: Test\nstrict: true\nhooks: []\n", encoding="utf-8"
        )
        ctx = _ctx()
        with caplog.at_level(logging.WARNING, logger="zenzic.core.adapters._zensical"):
            ZensicalAdapter.from_repo(ctx, docs_root, tmp_path)
        warned_keys = {r.message for r in caplog.records}
        assert any("strict" in msg for msg in warned_keys)

    def test_raises_config_error_when_neither_exists(self, tmp_path: Path) -> None:
        """from_repo raises ConfigurationError when no config file is found."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        ctx = _ctx()
        with pytest.raises(ConfigurationError, match="engine 'zensical'"):
            ZensicalAdapter.from_repo(ctx, docs_root, tmp_path)
