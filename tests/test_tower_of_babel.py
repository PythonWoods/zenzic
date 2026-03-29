# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tower of Babel — comprehensive i18n folder-mode test suite (S4-5).

Covers the full matrix of i18n folder-mode scenarios:
  1.  Fully-translated page — both locales present, no errors.
  2.  Partial translation — fallback=true suppresses FileNotFound.
  3.  Partial translation — fallback=false reports the missing file.
  4.  Ghost link — missing in BOTH locales — always reported.
  5.  Cross-locale direct link (../en-file.md) — Resolved directly, no fallback.
  6.  Same-name asset in two locale dirs (case-sensitivity collision guard).
  7.  Nested path inside locale dir resolved via fallback.
  8.  Orphan exclusion — locale dirs excluded from find_orphans().
  9.  ConfigurationError for fallback=true with no default locale.
  10. Reference-style link ([text][id]) from a locale file resolved via fallback.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from zenzic.core.scanner import find_orphans
from zenzic.core.validator import validate_links


# ─── Fixture helpers ──────────────────────────────────────────────────────────


def _mkdocs_i18n(
    *,
    fallback: bool,
    locales: list[str],
    default_locale: str = "en",
    extra_languages: str = "",
) -> str:
    """Build a mkdocs.yml with the MkDocs i18n plugin in folder mode.

    Args:
        fallback: Value for ``fallback_to_default``.
        locales: Non-default locale codes to include (e.g. ``["it", "de"]``).
        default_locale: Locale code for the default language.
        extra_languages: Raw YAML block appended to the ``languages`` list.
    """
    fb = "true" if fallback else "false"
    lang_lines = [
        f"        - locale: {default_locale}\n          default: true\n          build: true\n"
    ]
    for loc in locales:
        lang_lines.append(f"        - locale: {loc}\n          build: true\n")
    languages_block = "".join(lang_lines) + (extra_languages or "")
    return (
        "site_name: Test\n"
        "plugins:\n"
        "  - i18n:\n"
        "      docs_structure: folder\n"
        f"      fallback_to_default: {fb}\n"
        "      languages:\n"
        f"{languages_block}"
    )


def _write_mkdocs(repo: Path, **kwargs: object) -> None:
    (repo / "mkdocs.yml").write_text(_mkdocs_i18n(**kwargs))  # type: ignore[arg-type]


# ─── Scenario 1: Fully-translated page ────────────────────────────────────────


class TestTowerScenario01FullyTranslated:
    """Both the default locale and the translated locale have the page."""

    def test_no_errors(self, tmp_path: Path) -> None:
        """When docs/it/guide.md links to api.md and docs/it/api.md exists — Resolved."""
        docs = tmp_path / "docs"
        docs_it = docs / "it"
        docs_it.mkdir(parents=True)
        _write_mkdocs(tmp_path, fallback=True, locales=["it"])
        (docs / "api.md").write_text("# API EN\n")
        (docs_it / "api.md").write_text("# API IT\n")
        (docs_it / "guide.md").write_text("[api](api.md)\n")
        assert validate_links(tmp_path) == []


# ─── Scenario 2: Partial translation — fallback=true ─────────────────────────


class TestTowerScenario02PartialFallbackOn:
    """Untranslated page suppressed when fallback_to_default is true."""

    def test_missing_md_suppressed(self, tmp_path: Path) -> None:
        """docs/it/api.md absent — fallback maps to docs/api.md (exists)."""
        docs = tmp_path / "docs"
        docs_it = docs / "it"
        docs_it.mkdir(parents=True)
        _write_mkdocs(tmp_path, fallback=True, locales=["it"])
        (docs / "api.md").write_text("# API EN\n")
        (docs_it / "guide.md").write_text("[api](api.md)\n")
        assert validate_links(tmp_path) == []

    def test_missing_asset_suppressed(self, tmp_path: Path) -> None:
        """docs/it/assets/diagram.png absent — fallback maps to docs/assets/diagram.png."""
        docs = tmp_path / "docs"
        docs_it = docs / "it"
        (docs_it / "assets").mkdir(parents=True)
        (docs / "assets").mkdir()
        _write_mkdocs(tmp_path, fallback=True, locales=["it"])
        (docs / "assets" / "diagram.png").write_bytes(b"\x89PNG")
        (docs_it / "guide.md").write_text("![diagram](assets/diagram.png)\n")
        assert validate_links(tmp_path) == []

    def test_multi_locale_each_suppressed_independently(self, tmp_path: Path) -> None:
        """Multiple non-default locales (it, de) — each fallback resolved independently."""
        docs = tmp_path / "docs"
        (docs / "it").mkdir(parents=True)
        (docs / "de").mkdir(parents=True)
        _write_mkdocs(tmp_path, fallback=True, locales=["it", "de"])
        (docs / "api.md").write_text("# API EN\n")
        (docs / "it" / "guide.md").write_text("[api](api.md)\n")
        (docs / "de" / "guide.md").write_text("[api](api.md)\n")
        assert validate_links(tmp_path) == []


# ─── Scenario 3: Partial translation — fallback=false ────────────────────────


class TestTowerScenario03PartialFallbackOff:
    """Untranslated page reported when fallback_to_default is false."""

    def test_missing_md_reported(self, tmp_path: Path) -> None:
        """docs/it/api.md absent and fallback=false — error reported."""
        docs = tmp_path / "docs"
        docs_it = docs / "it"
        docs_it.mkdir(parents=True)
        _write_mkdocs(tmp_path, fallback=False, locales=["it"])
        (docs / "api.md").write_text("# API EN\n")
        (docs_it / "guide.md").write_text("[api](api.md)\n")
        errors = validate_links(tmp_path)
        assert len(errors) == 1
        assert "api.md" in errors[0]


# ─── Scenario 4: Ghost link — missing in both locales ────────────────────────


class TestTowerScenario04GhostLink:
    """A link to a file absent from BOTH locales is always reported."""

    def test_ghost_reported_fallback_on(self, tmp_path: Path) -> None:
        """ghost.md absent in both docs/ and docs/it/ — fallback cannot rescue it."""
        docs = tmp_path / "docs"
        docs_it = docs / "it"
        docs_it.mkdir(parents=True)
        _write_mkdocs(tmp_path, fallback=True, locales=["it"])
        (docs_it / "guide.md").write_text("[ghost](ghost.md)\n")
        errors = validate_links(tmp_path)
        assert any("ghost" in e for e in errors)

    def test_ghost_reported_fallback_off(self, tmp_path: Path) -> None:
        """Same scenario with fallback=false — ghost is still reported."""
        docs = tmp_path / "docs"
        docs_it = docs / "it"
        docs_it.mkdir(parents=True)
        _write_mkdocs(tmp_path, fallback=False, locales=["it"])
        (docs_it / "guide.md").write_text("[ghost](ghost.md)\n")
        errors = validate_links(tmp_path)
        assert any("ghost" in e for e in errors)


# ─── Scenario 5: Cross-locale direct link ─────────────────────────────────────


class TestTowerScenario05CrossLocaleDirectLink:
    """Links that navigate out of the locale dir are Resolved directly."""

    def test_parent_traversal_resolved(self, tmp_path: Path) -> None:
        """../en.md from docs/it/guide.md resolves to docs/en.md — no fallback path."""
        docs = tmp_path / "docs"
        docs_it = docs / "it"
        docs_it.mkdir(parents=True)
        _write_mkdocs(tmp_path, fallback=True, locales=["it"])
        (docs / "en.md").write_text("# EN only\n")
        (docs_it / "guide.md").write_text("[en](../en.md)\n")
        assert validate_links(tmp_path) == []

    def test_parent_traversal_missing_reported(self, tmp_path: Path) -> None:
        """../missing.md from docs/it/guide.md is not in docs/ — FileNotFound, not suppressed."""
        docs = tmp_path / "docs"
        docs_it = docs / "it"
        docs_it.mkdir(parents=True)
        _write_mkdocs(tmp_path, fallback=True, locales=["it"])
        (docs_it / "guide.md").write_text("[missing](../missing.md)\n")
        errors = validate_links(tmp_path)
        assert any("missing" in e for e in errors)


# ─── Scenario 6: Case-sensitivity collision ───────────────────────────────────


class TestTowerScenario06CaseSensitivity:
    """Zenzic is case-sensitive (Unix/Web standard). docs/assets/Logo.png ≠ docs/assets/logo.png."""

    def test_case_mismatch_asset_not_suppressed(self, tmp_path: Path) -> None:
        """docs/it/guide.md links to assets/Logo.png but only logo.png (lowercase) exists."""
        docs = tmp_path / "docs"
        docs_it = docs / "it"
        docs_it.mkdir(parents=True)
        (docs / "assets").mkdir()
        _write_mkdocs(tmp_path, fallback=True, locales=["it"])
        # Only lowercase variant in the default locale root.
        (docs / "assets" / "logo.png").write_bytes(b"\x89PNG")
        # Link uses Title-case — case-sensitive lookup must NOT find logo.png.
        (docs_it / "guide.md").write_text("![logo](assets/Logo.png)\n")
        errors = validate_links(tmp_path)
        assert any("Logo.png" in e for e in errors)

    def test_same_name_different_case_in_locale_vs_default(self, tmp_path: Path) -> None:
        """docs/it/assets/report.PDF and docs/assets/report.pdf are distinct files."""
        docs = tmp_path / "docs"
        docs_it = docs / "it"
        (docs_it / "assets").mkdir(parents=True)
        (docs / "assets").mkdir()
        _write_mkdocs(tmp_path, fallback=True, locales=["it"])
        # Locale has uppercase extension; default has lowercase — different assets.
        (docs_it / "assets" / "report.PDF").write_bytes(b"%PDF")
        (docs / "assets" / "report.pdf").write_bytes(b"%PDF")
        # Link to exact uppercase variant in locale dir — found in known_assets.
        (docs_it / "guide.md").write_text("![report](assets/report.PDF)\n")
        assert validate_links(tmp_path) == []


# ─── Scenario 7: Nested path inside locale dir ────────────────────────────────


class TestTowerScenario07NestedPath:
    """Fallback logic handles files nested in subdirectories of a locale dir."""

    def test_nested_md_fallback(self, tmp_path: Path) -> None:
        """docs/it/reference/cli.md absent — fallback maps to docs/reference/cli.md."""
        docs = tmp_path / "docs"
        (docs / "it" / "reference").mkdir(parents=True)
        (docs / "reference").mkdir()
        _write_mkdocs(tmp_path, fallback=True, locales=["it"])
        (docs / "reference" / "cli.md").write_text("# CLI\n")
        (docs / "it" / "guide.md").write_text("[cli](reference/cli.md)\n")
        assert validate_links(tmp_path) == []

    def test_nested_asset_fallback(self, tmp_path: Path) -> None:
        """docs/it/img/hero.jpg absent — fallback maps to docs/img/hero.jpg."""
        docs = tmp_path / "docs"
        (docs / "it" / "img").mkdir(parents=True)
        (docs / "img").mkdir()
        _write_mkdocs(tmp_path, fallback=True, locales=["it"])
        (docs / "img" / "hero.jpg").write_bytes(b"\xff\xd8")
        (docs / "it" / "guide.md").write_text("![hero](img/hero.jpg)\n")
        assert validate_links(tmp_path) == []


# ─── Scenario 8: Orphan exclusion ─────────────────────────────────────────────


class TestTowerScenario08OrphanExclusion:
    """find_orphans() must not flag files inside locale subdirectories."""

    def test_locale_files_not_orphaned(self, tmp_path: Path) -> None:
        """docs/it/guide.md is a locale file — should never appear in orphan list."""
        docs = tmp_path / "docs"
        docs_it = docs / "it"
        docs_it.mkdir(parents=True)
        _write_mkdocs(tmp_path, fallback=True, locales=["it"])
        (docs / "index.md").write_text("# Home\n")
        (docs_it / "guide.md").write_text("# Guida\n")
        from zenzic.models.config import ZenzicConfig

        config = ZenzicConfig.model_validate({"docs_dir": str(docs)})
        orphans = find_orphans(tmp_path, config=config)
        locale_orphans = [p for p in orphans if "it" in p.parts]
        assert locale_orphans == [], f"Locale files wrongly flagged as orphans: {locale_orphans}"

    def test_multi_locale_none_orphaned(self, tmp_path: Path) -> None:
        """files in docs/it/ and docs/de/ — neither should be flagged as orphans."""
        docs = tmp_path / "docs"
        (docs / "it").mkdir(parents=True)
        (docs / "de").mkdir(parents=True)
        _write_mkdocs(tmp_path, fallback=True, locales=["it", "de"])
        (docs / "index.md").write_text("# Home\n")
        (docs / "it" / "guide.md").write_text("# Guida\n")
        (docs / "de" / "guide.md").write_text("# Anleitung\n")
        from zenzic.models.config import ZenzicConfig

        config = ZenzicConfig.model_validate({"docs_dir": str(docs)})
        orphans = find_orphans(tmp_path, config=config)
        locale_orphans = [p for p in orphans if ("it" in p.parts or "de" in p.parts)]
        assert locale_orphans == []


# ─── Scenario 9: ConfigurationError for bad config ────────────────────────────


class TestTowerScenario09ConfigError:
    """ConfigurationError when fallback=true but no language has default: true."""

    def test_raises_on_no_default_locale(self, tmp_path: Path) -> None:
        """Neither 'en' nor 'it' is marked default: true — ConfigurationError."""
        from zenzic.core.exceptions import ConfigurationError

        docs = tmp_path / "docs"
        (docs / "it").mkdir(parents=True)
        bad_mkdocs = (
            "site_name: Test\n"
            "plugins:\n"
            "  - i18n:\n"
            "      docs_structure: folder\n"
            "      fallback_to_default: true\n"
            "      languages:\n"
            "        - locale: en\n"
            "        - locale: it\n"
        )
        (tmp_path / "mkdocs.yml").write_text(bad_mkdocs)
        (docs / "index.md").touch()
        with pytest.raises(ConfigurationError, match="fallback_to_default"):
            validate_links(tmp_path)

    def test_null_languages_does_not_raise(self, tmp_path: Path) -> None:
        """languages: null with fallback_to_default: true — treated as disabled, no error."""
        docs = tmp_path / "docs"
        (docs / "it").mkdir(parents=True)
        null_languages = (
            "site_name: Test\n"
            "plugins:\n"
            "  - i18n:\n"
            "      docs_structure: folder\n"
            "      fallback_to_default: true\n"
            "      languages:\n"
        )
        (tmp_path / "mkdocs.yml").write_text(null_languages)
        (docs / "index.md").touch()
        # Must not raise — null languages means i18n is not properly configured.
        errors = validate_links(tmp_path)
        assert isinstance(errors, list)


# ─── Scenario 10: Reference-style links from locale files ─────────────────────


class TestTowerScenario10ReferenceLinks:
    """Reference-style [text][id] links from locale files are resolved + fallback applied."""

    def test_ref_link_fallback_suppressed(self, tmp_path: Path) -> None:
        """[api][api-ref] in docs/it/guide.md — ref resolves to api.md (intra-locale).
        docs/it/api.md absent, fallback finds docs/api.md — suppressed.
        """
        docs = tmp_path / "docs"
        docs_it = docs / "it"
        docs_it.mkdir(parents=True)
        _write_mkdocs(tmp_path, fallback=True, locales=["it"])
        (docs / "api.md").write_text("# API EN\n")
        (docs_it / "guide.md").write_text("[api][api-ref]\n\n[api-ref]: api.md\n")
        assert validate_links(tmp_path) == []

    def test_ref_link_fallback_off_reported(self, tmp_path: Path) -> None:
        """Same scenario with fallback=false — error reported for the missing translation."""
        docs = tmp_path / "docs"
        docs_it = docs / "it"
        docs_it.mkdir(parents=True)
        _write_mkdocs(tmp_path, fallback=False, locales=["it"])
        (docs / "api.md").write_text("# API EN\n")
        (docs_it / "guide.md").write_text("[api][api-ref]\n\n[api-ref]: api.md\n")
        errors = validate_links(tmp_path)
        assert len(errors) == 1
        assert "api.md" in errors[0]

    def test_ref_link_ghost_reported(self, tmp_path: Path) -> None:
        """[ghost][g] in docs/it/guide.md — ghost.md absent in both locales — error."""
        docs = tmp_path / "docs"
        docs_it = docs / "it"
        docs_it.mkdir(parents=True)
        _write_mkdocs(tmp_path, fallback=True, locales=["it"])
        (docs_it / "guide.md").write_text("[ghost][g]\n\n[g]: ghost.md\n")
        errors = validate_links(tmp_path)
        assert any("ghost" in e for e in errors)


# ─── Suffix Mode: Base-link strategy ─────────────────────────────────────────


def _mkdocs_suffix(*, locales: list[str], default_locale: str = "en") -> str:
    """Build a mkdocs.yml with the MkDocs i18n plugin in suffix mode."""
    lang_lines = [
        f"        - locale: {default_locale}\n          default: true\n          build: true\n"
    ]
    for loc in locales:
        lang_lines.append(f"        - locale: {loc}\n          build: true\n")
    return (
        "site_name: Test\n"
        "plugins:\n"
        "  - i18n:\n"
        "      docs_structure: suffix\n"
        "      fallback_to_default: true\n"
        "      languages:\n" + "".join(lang_lines)
    )


def _write_mkdocs_suffix(repo: Path, **kwargs: object) -> None:
    (repo / "mkdocs.yml").write_text(_mkdocs_suffix(**kwargs))  # type: ignore[arg-type]


class TestSuffixModeBaseLinkStrategy:
    """Suffix mode: translated files must link to base .md files, not .locale.md siblings.

    Best practice (D3 / Base-link strategy): a link inside ``guide.it.md`` should
    point to ``index.md``, not ``index.it.md``.  Zenzic must validate the base file
    exists and report success — the build engine decides at render time whether to
    serve the translated or fallback version.
    """

    def test_translated_file_linking_base_md_is_ok(self, tmp_path: Path) -> None:
        """guide.it.md links to index.md (base file) — base file exists — no error."""
        docs = tmp_path / "docs"
        docs.mkdir()
        _write_mkdocs_suffix(tmp_path, locales=["it"])
        (docs / "index.md").write_text("# Home EN\n")
        (docs / "index.it.md").write_text("# Home IT\n")
        (docs / "guide.it.md").write_text("[Home](index.md)\n")
        errors = validate_links(tmp_path)
        assert errors == []

    def test_translated_file_linking_missing_base_is_error(self, tmp_path: Path) -> None:
        """guide.it.md links to missing.md — file absent in all locales — error reported."""
        docs = tmp_path / "docs"
        docs.mkdir()
        _write_mkdocs_suffix(tmp_path, locales=["it"])
        (docs / "guide.it.md").write_text("[Missing](missing.md)\n")
        errors = validate_links(tmp_path)
        assert any("missing.md" in e for e in errors)

    def test_translated_file_linking_sibling_locale_is_ok(self, tmp_path: Path) -> None:
        """guide.it.md links to other.it.md — sibling translation exists — no error.

        Some authors prefer intra-locale links for sections unique to the translation.
        Zenzic permits this as long as the target file exists on disk.
        """
        docs = tmp_path / "docs"
        docs.mkdir()
        _write_mkdocs_suffix(tmp_path, locales=["it"])
        (docs / "guide.it.md").write_text("[Other IT](other.it.md)\n")
        (docs / "other.it.md").write_text("# Other IT\n")
        errors = validate_links(tmp_path)
        assert errors == []
