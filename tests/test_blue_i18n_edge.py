# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""TEAM BLUE — i18n fallback / cross-locale resolution edge-case tests.

Tests: links from locale files to default-locale assets, missing locale
directories, partial translations, locale codes with variants (pt-BR).
"""

from __future__ import annotations

from pathlib import Path

from zenzic.core.adapters._docusaurus import DocusaurusAdapter
from zenzic.core.adapters._utils import remap_to_default_locale
from zenzic.models.config import BuildContext
from zenzic.models.vsm import build_vsm


# ═══════════════════════════════════════════════════════════════════════════════
# I18N-01: remap_to_default_locale (pure function)
# ═══════════════════════════════════════════════════════════════════════════════


class TestRemapToDefaultLocale:
    """Test the core locale path remapping utility."""

    def test_locale_file_remaps(self) -> None:
        result = remap_to_default_locale(
            Path("/docs/it/guide.md"), Path("/docs"), frozenset({"it", "fr"})
        )
        assert result == Path("/docs/guide.md")

    def test_default_locale_file_returns_none(self) -> None:
        result = remap_to_default_locale(
            Path("/docs/guide.md"), Path("/docs"), frozenset({"it", "fr"})
        )
        assert result is None

    def test_unknown_locale_returns_none(self) -> None:
        """A file in a dir not in locale_dirs is not remapped."""
        result = remap_to_default_locale(
            Path("/docs/de/guide.md"), Path("/docs"), frozenset({"it", "fr"})
        )
        assert result is None

    def test_nested_locale_file(self) -> None:
        result = remap_to_default_locale(
            Path("/docs/fr/a/b/c.md"), Path("/docs"), frozenset({"fr"})
        )
        assert result == Path("/docs/a/b/c.md")

    def test_file_outside_docs_root(self) -> None:
        """Path not under docs_root returns None."""
        result = remap_to_default_locale(
            Path("/other/it/guide.md"), Path("/docs"), frozenset({"it"})
        )
        assert result is None

    def test_empty_locale_dirs(self) -> None:
        result = remap_to_default_locale(Path("/docs/it/guide.md"), Path("/docs"), frozenset())
        assert result is None

    def test_locale_root_only(self) -> None:
        """Just the locale dir with no file beneath: /docs/it → /docs."""
        result = remap_to_default_locale(Path("/docs/it"), Path("/docs"), frozenset({"it"}))
        # it's parts[0] == "it", so parts[1:] is empty → docs_root joinpath() → docs_root
        assert result == Path("/docs")

    def test_locale_asset_not_md(self) -> None:
        """Non-md files (images) should also remap correctly."""
        result = remap_to_default_locale(
            Path("/docs/it/img/logo.png"), Path("/docs"), frozenset({"it"})
        )
        assert result == Path("/docs/img/logo.png")


# ═══════════════════════════════════════════════════════════════════════════════
# I18N-02: Docusaurus resolve_asset fallback
# ═══════════════════════════════════════════════════════════════════════════════


class TestDocusaurusResolveAsset:
    """Test resolve_asset: locale file missing → fallback to default locale."""

    def test_fallback_finds_default_locale_asset(self, tmp_path: Path) -> None:
        """Asset only in /en/ (default), referenced from /it/ → found via fallback."""
        docs = tmp_path / "docs"
        docs.mkdir()
        # Default locale has the image
        (docs / "img").mkdir()
        (docs / "img" / "logo.png").write_text("img")
        # IT locale has no image
        (docs / "it").mkdir()

        ctx = BuildContext(engine="docusaurus", locales=["it"], fallback_to_default=True)
        adapter = DocusaurusAdapter(ctx, docs)

        missing = docs / "it" / "img" / "logo.png"
        result = adapter.resolve_asset(missing, docs)
        assert result is not None
        assert result == docs / "img" / "logo.png"

    def test_no_fallback_when_disabled(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "img").mkdir()
        (docs / "img" / "logo.png").write_text("img")

        ctx = BuildContext(engine="docusaurus", locales=["it"], fallback_to_default=False)
        adapter = DocusaurusAdapter(ctx, docs)

        missing = docs / "it" / "img" / "logo.png"
        result = adapter.resolve_asset(missing, docs)
        assert result is None

    def test_fallback_returns_none_when_default_also_missing(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "it").mkdir()

        ctx = BuildContext(engine="docusaurus", locales=["it"], fallback_to_default=True)
        adapter = DocusaurusAdapter(ctx, docs)

        missing = docs / "it" / "img" / "nonexistent.png"
        result = adapter.resolve_asset(missing, docs)
        assert result is None

    def test_fallback_for_non_locale_path_returns_none(self, tmp_path: Path) -> None:
        """A missing asset not in a locale dir → no fallback."""
        docs = tmp_path / "docs"
        docs.mkdir()

        ctx = BuildContext(engine="docusaurus", locales=["it"], fallback_to_default=True)
        adapter = DocusaurusAdapter(ctx, docs)

        missing = docs / "img" / "logo.png"
        result = adapter.resolve_asset(missing, docs)
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# I18N-03: Docusaurus resolve_anchor fallback
# ═══════════════════════════════════════════════════════════════════════════════


class TestDocusaurusResolveAnchor:
    """Test anchor fallback: anchor missing in locale → check default locale."""

    def test_anchor_found_in_default_locale(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "it").mkdir()

        ctx = BuildContext(engine="docusaurus", locales=["it"], fallback_to_default=True)
        adapter = DocusaurusAdapter(ctx, docs)

        locale_file = docs / "it" / "guide.md"
        default_file = docs / "guide.md"
        anchors_cache = {default_file: {"installation", "quick-start"}}

        assert adapter.resolve_anchor(locale_file, "installation", anchors_cache, docs) is True

    def test_anchor_not_in_default_locale(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "it").mkdir()

        ctx = BuildContext(engine="docusaurus", locales=["it"], fallback_to_default=True)
        adapter = DocusaurusAdapter(ctx, docs)

        locale_file = docs / "it" / "guide.md"
        default_file = docs / "guide.md"
        anchors_cache = {default_file: {"installation"}}

        assert adapter.resolve_anchor(locale_file, "nonexistent", anchors_cache, docs) is False

    def test_anchor_fallback_disabled(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()

        ctx = BuildContext(engine="docusaurus", locales=["it"], fallback_to_default=False)
        adapter = DocusaurusAdapter(ctx, docs)

        locale_file = docs / "it" / "guide.md"
        default_file = docs / "guide.md"
        anchors_cache = {default_file: {"installation"}}

        assert adapter.resolve_anchor(locale_file, "installation", anchors_cache, docs) is False


# ═══════════════════════════════════════════════════════════════════════════════
# I18N-04: Partial translations and missing locale directories
# ═══════════════════════════════════════════════════════════════════════════════


class TestPartialTranslations:
    """Test behavior when only some files exist in a locale."""

    def test_partial_translation_default_locale_files_reachable(self, tmp_path: Path) -> None:
        """Files only in default locale (not in IT) are still REACHABLE."""
        docs = tmp_path / "docs"
        for f in ["index.mdx", "guide.md"]:
            p = docs / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"# {f}")
        # IT has only index
        (docs / "it").mkdir()
        (docs / "it" / "index.mdx").write_text("# Home IT")

        ctx = BuildContext(engine="docusaurus", locales=["it"])
        adapter = DocusaurusAdapter(ctx, docs)

        md_contents = {
            docs / "index.mdx": "# Home",
            docs / "guide.md": "# Guide",
            docs / "it" / "index.mdx": "# Home IT",
        }
        vsm = build_vsm(adapter, docs, md_contents)
        assert vsm["/docs/"].status == "REACHABLE"
        assert vsm["/docs/guide/"].status == "REACHABLE"
        assert vsm["/it/docs/"].status == "REACHABLE"


# ═══════════════════════════════════════════════════════════════════════════════
# I18N-05: Locale codes with variants (pt-BR style)
# ═══════════════════════════════════════════════════════════════════════════════


class TestLocaleVariants:
    """Test locale codes with region variants like pt-BR."""

    def test_pt_br_is_locale_dir(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        ctx = BuildContext(engine="docusaurus", locales=["pt-BR"])
        adapter = DocusaurusAdapter(ctx, docs)
        assert adapter.is_locale_dir("pt-BR") is True
        assert adapter.is_locale_dir("pt") is False

    def test_pt_br_remap(self) -> None:
        result = remap_to_default_locale(
            Path("/docs/pt-BR/guide.md"), Path("/docs"), frozenset({"pt-BR"})
        )
        assert result == Path("/docs/guide.md")

    def test_pt_br_asset_fallback(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "img").mkdir()
        (docs / "img" / "logo.png").write_text("img")
        (docs / "pt-BR").mkdir()

        ctx = BuildContext(engine="docusaurus", locales=["pt-BR"], fallback_to_default=True)
        adapter = DocusaurusAdapter(ctx, docs)

        missing = docs / "pt-BR" / "img" / "logo.png"
        result = adapter.resolve_asset(missing, docs)
        assert result is not None
        assert result == docs / "img" / "logo.png"
