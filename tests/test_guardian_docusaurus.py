# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Guardians of Quality — DocusaurusAdapter targeted coverage test suite.

Closes gaps identified in sprint v0.6.1 coverage audit:
  - set_slug_map: ValueError branch (file outside docs_root)
  - resolve_asset: fallback exists on disk
  - resolve_anchor: anchor found via i18n fallback
  - is_shadow_of_nav_page: default_abs is None
  - map_url: double-extension stem edge case, locale prefix, version sentinel,
             index collapsing, empty route_base_path, offline mode
  - classify_route: _version_ sentinel reachability, locale ghost entry point
  - get_route_info: proxy locale entry point flag, version field extraction
  - get_locale_source_roots: versioned docs + translated versioned docs on disk
"""

from __future__ import annotations

from pathlib import Path

from zenzic.core.adapters._docusaurus import DocusaurusAdapter
from zenzic.models.config import BuildContext


# ── Helpers ───────────────────────────────────────────────────────────────────


def _ctx(
    *,
    locales: list[str] | None = None,
    fallback: bool = True,
    offline: bool = False,
) -> BuildContext:
    return BuildContext(
        engine="docusaurus",
        locales=locales or [],
        fallback_to_default=fallback,
        offline_mode=offline,
    )


def _adapter(
    docs_root: Path,
    *,
    locales: list[str] | None = None,
    route_base_path: str | None = None,
    versions: list[str] | None = None,
    offline: bool = False,
) -> DocusaurusAdapter:
    ctx = _ctx(locales=locales or [], offline=offline)
    return DocusaurusAdapter(ctx, docs_root, "/", route_base_path, versions or [])


# ── set_slug_map ──────────────────────────────────────────────────────────────


class TestSetSlugMap:
    """set_slug_map() must skip files that are not relative to docs_root."""

    def test_file_outside_docs_root_is_skipped(self, tmp_path: Path) -> None:
        """Files outside docs_root raise ValueError in relative_to — must be silently skipped."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        adapter = _adapter(docs_root)

        outside_file = tmp_path / "other" / "page.mdx"
        md_contents = {outside_file: "---\nslug: /custom\n---\n# Page"}
        adapter.set_slug_map(md_contents)

        # The slug must NOT have been registered
        assert adapter._slug_map == {}

    def test_file_inside_docs_root_is_registered(self, tmp_path: Path) -> None:
        """Files inside docs_root get their slug registered correctly."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        adapter = _adapter(docs_root)

        inside_file = docs_root / "guide.mdx"
        md_contents = {inside_file: "---\nslug: /custom-guide\n---\n# Guide"}
        adapter.set_slug_map(md_contents)

        assert adapter._slug_map == {"guide.mdx": "/custom-guide"}

    def test_mixed_inside_outside(self, tmp_path: Path) -> None:
        """Only files inside docs_root populate the slug map."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        adapter = _adapter(docs_root)

        inside = docs_root / "api.mdx"
        outside = tmp_path / "readme.mdx"
        adapter.set_slug_map(
            {
                inside: "---\nslug: /api\n---\n",
                outside: "---\nslug: /outside\n---\n",
            }
        )

        assert "api.mdx" in adapter._slug_map
        assert "readme.mdx" not in adapter._slug_map


# ── resolve_asset ─────────────────────────────────────────────────────────────


class TestResolveAsset:
    """resolve_asset() returns fallback when it exists on disk."""

    def test_fallback_exists_returns_path(self, tmp_path: Path) -> None:
        """When the default-locale fallback exists, resolve_asset returns it."""
        docs_root = tmp_path / "docs"
        it_docs = docs_root / "it"
        it_docs.mkdir(parents=True)
        en_img = docs_root / "img" / "logo.png"
        en_img.parent.mkdir(parents=True)
        en_img.write_bytes(b"\x89PNG")

        adapter = _adapter(docs_root, locales=["it"])
        missing = it_docs / "img" / "logo.png"
        result = adapter.resolve_asset(missing, docs_root)
        assert result == en_img

    def test_fallback_disabled_returns_none(self, tmp_path: Path) -> None:
        """When fallback_to_default=False, always returns None."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir(parents=True)
        ctx = _ctx(locales=["it"], fallback=False)
        adapter = DocusaurusAdapter(ctx, docs_root)
        result = adapter.resolve_asset(docs_root / "it" / "logo.png", docs_root)
        assert result is None

    def test_fallback_missing_returns_none(self, tmp_path: Path) -> None:
        """When fallback exists in logic but not on disk, returns None."""
        docs_root = tmp_path / "docs"
        (docs_root / "it").mkdir(parents=True)
        adapter = _adapter(docs_root, locales=["it"])
        # No en fallback created on disk
        result = adapter.resolve_asset(docs_root / "it" / "ghost.png", docs_root)
        assert result is None


# ── resolve_anchor ────────────────────────────────────────────────────────────


class TestResolveAnchor:
    """resolve_anchor() returns True when the anchor exists in the default-locale file."""

    def test_anchor_found_in_default_locale(self, tmp_path: Path) -> None:
        """Anchor missing in IT locale but present in EN fallback → True."""
        docs_root = tmp_path / "docs"
        it_docs = docs_root / "it"
        it_docs.mkdir(parents=True)
        en_page = docs_root / "guide.mdx"
        en_page.write_text("# Guide\n## Install\n", encoding="utf-8")

        adapter = _adapter(docs_root, locales=["it"])
        it_page = it_docs / "guide.mdx"
        it_page.write_text("# Guida\n", encoding="utf-8")

        anchors_cache = {en_page: {"guide", "install"}}
        result = adapter.resolve_anchor(it_page, "install", anchors_cache, docs_root)
        assert result is True

    def test_anchor_not_in_default_locale(self, tmp_path: Path) -> None:
        """Anchor absent in both locales → False."""
        docs_root = tmp_path / "docs"
        it_docs = docs_root / "it"
        it_docs.mkdir(parents=True)
        en_page = docs_root / "guide.mdx"
        en_page.write_text("# Guide\n", encoding="utf-8")

        adapter = _adapter(docs_root, locales=["it"])
        it_page = it_docs / "guide.mdx"
        anchors_cache = {en_page: {"guide"}}
        result = adapter.resolve_anchor(it_page, "missing-anchor", anchors_cache, docs_root)
        assert result is False


# ── is_shadow_of_nav_page ─────────────────────────────────────────────────────


class TestIsShadowOfNavPage:
    """is_shadow_of_nav_page() returns False when default_abs is None."""

    def test_no_locale_no_shadow(self, tmp_path: Path) -> None:
        """A file with no locale prefix cannot be a locale shadow — default_abs is None."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        adapter = _adapter(docs_root, locales=["it"])

        # Path has no locale prefix → remap_to_default_locale returns None
        rel = Path("guide.mdx")
        result = adapter.is_shadow_of_nav_page(rel, frozenset({"guide.mdx"}))
        assert result is False


# ── map_url ───────────────────────────────────────────────────────────────────


class TestMapUrl:
    """map_url() covers all URL derivation paths."""

    def test_locale_prefix_stripped_from_url_and_reinjected(self, tmp_path: Path) -> None:
        """Files with a locale prefix produce /{locale}/docs/.../ URL."""
        adapter = _adapter(tmp_path, locales=["it"])
        url = adapter.map_url(Path("it/guide/install.mdx"))
        assert url == "/it/docs/guide/install/"

    def test_version_sentinel_produces_versioned_url(self, tmp_path: Path) -> None:
        """Non-latest versioned files get the version label in the URL."""
        # Use two versions so 1.0 is NOT the latest (2.0 is).
        adapter = _adapter(tmp_path, versions=["2.0", "1.0"])
        url = adapter.map_url(Path("_version_/1.0/guide/install.mdx"))
        assert url == "/docs/1.0/guide/install/"

    def test_version_sentinel_index_collapses(self, tmp_path: Path) -> None:
        """Non-latest version index.mdx collapses to /{rbp}/{ver}/."""
        # Use two versions so 2.0 is NOT the latest (3.0 is).
        adapter = _adapter(tmp_path, versions=["3.0", "2.0"])
        url = adapter.map_url(Path("_version_/2.0/index.mdx"))
        assert url == "/docs/2.0/"

    def test_index_collapses_to_parent(self, tmp_path: Path) -> None:
        """guide/index.mdx maps to /docs/guide/."""
        adapter = _adapter(tmp_path)
        assert adapter.map_url(Path("guide/index.mdx")) == "/docs/guide/"

    def test_root_index_collapses_to_slash(self, tmp_path: Path) -> None:
        """index.mdx at docs root collapses to /docs/."""
        adapter = _adapter(tmp_path)
        assert adapter.map_url(Path("index.mdx")) == "/docs/"

    def test_empty_route_base_path(self, tmp_path: Path) -> None:
        """routeBasePath='' serves docs at site root."""
        adapter = _adapter(tmp_path, route_base_path="")
        url = adapter.map_url(Path("guide/install.mdx"))
        assert url == "/guide/install/"

    def test_custom_route_base_path(self, tmp_path: Path) -> None:
        """routeBasePath='reference' prefixes URL accordingly."""
        adapter = _adapter(tmp_path, route_base_path="reference")
        url = adapter.map_url(Path("api.mdx"))
        assert url == "/reference/api/"

    def test_offline_mode_produces_html_extension(self, tmp_path: Path) -> None:
        """With offline_mode=True, URLs end in .html instead of /."""
        adapter = _adapter(tmp_path, offline=True)
        url = adapter.map_url(Path("guide/install.mdx"))
        assert url == "/docs/guide/install.html"

    def test_offline_mode_empty_url_parts_returns_index_html(self, tmp_path: Path) -> None:
        """With offline_mode and empty routeBasePath, root index → /index.html."""
        adapter = _adapter(tmp_path, route_base_path="", offline=True)
        url = adapter.map_url(Path("index.mdx"))
        assert url == "/index.html"

    def test_locale_with_empty_rbp_offline(self, tmp_path: Path) -> None:
        """Locale + empty rbp + offline = /{locale}/page.html."""
        adapter = _adapter(tmp_path, locales=["fr"], route_base_path="", offline=True)
        url = adapter.map_url(Path("fr/page.mdx"))
        assert url == "/fr/page.html"


# ── classify_route ────────────────────────────────────────────────────────────


class TestClassifyRoute:
    """classify_route() covers version sentinel and locale ghost routes."""

    def test_version_sentinel_is_reachable(self, tmp_path: Path) -> None:
        """Files under _version_/<label>/ are always REACHABLE."""
        adapter = _adapter(tmp_path, versions=["1.0"])
        status = adapter.classify_route(Path("_version_/1.0/guide/install.mdx"), frozenset())
        assert status == "REACHABLE"

    def test_underscore_in_version_path_is_not_ignored(self, tmp_path: Path) -> None:
        """_version_ sentinel exemption: only _version_ is exempt from IGNORED rule."""
        adapter = _adapter(tmp_path, versions=["1.0"])
        # A real user dir starting with _ inside the version path should be IGNORED
        status = adapter.classify_route(Path("_version_/1.0/_private/page.mdx"), frozenset())
        assert status == "IGNORED"

    def test_locale_index_is_ghost_route_reachable(self, tmp_path: Path) -> None:
        """Locale entry point index.mdx is a ghost route → REACHABLE even without nav."""
        adapter = _adapter(tmp_path, locales=["it"])
        nav = frozenset({"intro.mdx"})  # it/index.mdx not listed
        status = adapter.classify_route(Path("it/index.mdx"), nav)
        assert status == "REACHABLE"

    def test_locale_index_md_also_ghost_route(self, tmp_path: Path) -> None:
        """index.md (not .mdx) also qualifies as a ghost locale route."""
        adapter = _adapter(tmp_path, locales=["fr"])
        nav = frozenset({"intro.mdx"})
        status = adapter.classify_route(Path("fr/index.md"), nav)
        assert status == "REACHABLE"

    def test_orphan_when_explicit_nav_and_not_listed(self, tmp_path: Path) -> None:
        """File present but not in explicit nav → ORPHAN_BUT_EXISTING.

        Note: DocusaurusAdapter always returns empty frozenset from get_nav_paths()
        (autogenerated sidebar mode), but classify_route still handles explicit nav
        when nav_paths is passed from external callers.
        """
        adapter = _adapter(tmp_path)
        nav = frozenset({"listed.mdx"})
        status = adapter.classify_route(Path("unlisted.mdx"), nav)
        assert status == "ORPHAN_BUT_EXISTING"


# ── get_route_info ────────────────────────────────────────────────────────────


class TestGetRouteInfo:
    """get_route_info() must set is_proxy and version fields correctly."""

    def test_locale_index_is_proxy(self, tmp_path: Path) -> None:
        """Locale entry-point index files are marked is_proxy=True."""
        adapter = _adapter(tmp_path, locales=["it"])
        meta = adapter.get_route_info(Path("it/index.mdx"))
        assert meta.is_proxy is True

    def test_regular_locale_file_not_proxy(self, tmp_path: Path) -> None:
        """Regular locale files are not proxy routes."""
        adapter = _adapter(tmp_path, locales=["it"])
        meta = adapter.get_route_info(Path("it/guide/install.mdx"))
        assert meta.is_proxy is False

    def test_version_field_extracted(self, tmp_path: Path) -> None:
        """Version is extracted from _version_/<label>/ path prefix."""
        adapter = _adapter(tmp_path, versions=["2.1"])
        meta = adapter.get_route_info(Path("_version_/2.1/api.mdx"))
        assert meta.version == "2.1"

    def test_non_version_path_has_no_version(self, tmp_path: Path) -> None:
        """Regular paths have version=None."""
        adapter = _adapter(tmp_path)
        meta = adapter.get_route_info(Path("guide/install.mdx"))
        assert meta.version is None

    def test_slug_from_map_is_carried(self, tmp_path: Path) -> None:
        """Registered slug is present in RouteMetadata."""
        adapter = _adapter(tmp_path)
        adapter._slug_map["guide/install.mdx"] = "/custom-install"
        meta = adapter.get_route_info(Path("guide/install.mdx"))
        assert meta.slug == "/custom-install"


# ── get_locale_source_roots ───────────────────────────────────────────────────


class TestGetLocaleSourceRoots:
    """get_locale_source_roots() returns correct entries for versioned docs."""

    def _setup_versioned_repo(
        self, tmp_path: Path, locale: str, version: str
    ) -> tuple[Path, Path, Path]:
        """Create the standard Docusaurus versioned directory structure on disk."""
        # Default locale versioned docs
        versioned = tmp_path / f"versioned_docs/version-{version}"
        versioned.mkdir(parents=True)

        # Translated versioned docs
        translated = (
            tmp_path / "i18n" / locale / "docusaurus-plugin-content-docs" / f"version-{version}"
        )
        translated.mkdir(parents=True)

        # Default locale i18n current
        locale_current = tmp_path / "i18n" / locale / "docusaurus-plugin-content-docs" / "current"
        locale_current.mkdir(parents=True)

        return versioned, translated, locale_current

    def test_versioned_docs_included(self, tmp_path: Path) -> None:
        """versioned_docs/version-<X>/ appears in result with sentinel label."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        versioned, _, _ = self._setup_versioned_repo(tmp_path, "it", "1.0")

        adapter = _adapter(docs_root, locales=["it"], versions=["1.0"])
        roots = adapter.get_locale_source_roots(tmp_path)
        paths = [p for p, _ in roots]
        labels = [lbl for _, lbl in roots]

        assert versioned.resolve() in paths
        assert "_version_/1.0" in labels

    def test_translated_versioned_docs_included(self, tmp_path: Path) -> None:
        """i18n/{locale}/.../version-<X>/ appears with combined label."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        versioned, translated, _ = self._setup_versioned_repo(tmp_path, "it", "1.0")

        adapter = _adapter(docs_root, locales=["it"], versions=["1.0"])
        roots = adapter.get_locale_source_roots(tmp_path)
        labels = [lbl for _, lbl in roots]

        assert "it/_version_/1.0" in labels

    def test_locale_current_included(self, tmp_path: Path) -> None:
        """i18n/{locale}/docusaurus-plugin-content-docs/current/ is included."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        _, _, locale_current = self._setup_versioned_repo(tmp_path, "it", "1.0")

        adapter = _adapter(docs_root, locales=["it"], versions=["1.0"])
        roots = adapter.get_locale_source_roots(tmp_path)
        paths = [p for p, _ in roots]
        labels = [lbl for _, lbl in roots]

        assert locale_current.resolve() in paths
        assert "it" in labels

    def test_missing_versioned_dir_excluded(self, tmp_path: Path) -> None:
        """If versioned_docs/version-X/ does not exist, it is not included."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        adapter = _adapter(docs_root, locales=[], versions=["99.0"])
        # No directories created → nothing should appear
        roots = adapter.get_locale_source_roots(tmp_path)
        assert roots == []

    def test_empty_versions_and_locales(self, tmp_path: Path) -> None:
        """With no versions and no locales, result is always empty."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        adapter = _adapter(docs_root, locales=[], versions=[])
        assert adapter.get_locale_source_roots(tmp_path) == []
