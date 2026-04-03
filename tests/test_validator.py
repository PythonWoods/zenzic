# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for Zenzic validator: link extraction, internal / external link validation, snippets."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from zenzic.core.validator import (
    _MAX_CONCURRENT_REQUESTS,
    _build_ref_map,
    anchors_in_file,
    extract_links,
    extract_ref_links,
    slug_heading,
    validate_links,
    validate_snippets,
)
from zenzic.models.config import ZenzicConfig


# ─── extract_links (pure) ─────────────────────────────────────────────────────


class TestExtractLinks:
    """Pure extraction of (url, lineno) pairs from raw markdown text."""

    def test_simple_link(self) -> None:
        assert extract_links("[text](page.md)") == [("page.md", 1)]

    def test_image_link(self) -> None:
        assert extract_links("![logo](assets/logo.png)") == [("assets/logo.png", 1)]

    def test_link_with_title_stripped(self) -> None:
        assert extract_links('[click](page.md "My Page")') == [("page.md", 1)]

    def test_link_with_single_quote_title_stripped(self) -> None:
        assert extract_links("[click](page.md 'My Page')") == [("page.md", 1)]

    def test_empty_url_ignored(self) -> None:
        assert extract_links("[empty]()") == []

    def test_multiple_links_same_line(self) -> None:
        assert extract_links("[a](a.md) and [b](b.md)") == [("a.md", 1), ("b.md", 1)]

    def test_correct_line_numbers(self) -> None:
        text = "line one\n[link](target.md)\nline three"
        assert extract_links(text) == [("target.md", 2)]

    def test_link_inside_fenced_block_ignored(self) -> None:
        text = "```\n[fake](ghost.md)\n```"
        assert extract_links(text) == []

    def test_link_before_and_after_fenced_block_found(self) -> None:
        text = "[before](before.md)\n```\n[fake](ghost.md)\n```\n[after](after.md)"
        urls = [u for u, _ in extract_links(text)]
        assert urls == ["before.md", "after.md"]
        assert "ghost.md" not in urls

    def test_link_inside_inline_code_ignored(self) -> None:
        assert extract_links("Use `[text](url)` syntax.") == []

    def test_link_mixed_inline_code_and_real(self) -> None:
        text = "Example: `[fake](nope.md)` but [real](page.md)."
        urls = [u for u, _ in extract_links(text)]
        assert urls == ["page.md"]
        assert "nope.md" not in urls

    def test_link_with_fragment(self) -> None:
        assert extract_links("[sec](page.md#setup)") == [("page.md#setup", 1)]

    def test_external_https_url(self) -> None:
        assert extract_links("[docs](https://example.com)") == [("https://example.com", 1)]

    def test_reference_style_link_not_extracted(self) -> None:
        # [text][ref] is reference-style; not an inline link — must not be matched.
        assert extract_links("[text][ref]\n[ref]: page.md") == []

    @pytest.mark.parametrize(
        "content",
        [
            "~~~\n[fake](ghost.md)\n~~~",  # tilde fenced block
            "```python\n[fake](ghost.md)\n```",  # fenced block with language
        ],
    )
    def test_various_fence_styles_ignored(self, content: str) -> None:
        assert extract_links(content) == []


# ─── slug_heading (pure) ──────────────────────────────────────────────────────


class TestSlugHeading:
    """Heading text → URL-safe anchor slug."""

    @pytest.mark.parametrize(
        "heading, expected",
        [
            ("Hello World", "hello-world"),
            ("Quick-Start Guide!", "quick-start-guide"),
            ("foo-bar", "foo-bar"),
            ("  foo   bar  ", "foo-bar"),
            ("API Reference (v2)", "api-reference-v2"),
            ("", ""),
        ],
    )
    def test_slug(self, heading: str, expected: str) -> None:
        assert slug_heading(heading) == expected


# ─── anchors_in_file (pure) ───────────────────────────────────────────────────


class TestAnchorsInFile:
    """Extract anchor slug set from raw markdown content."""

    def test_single_heading(self) -> None:
        assert anchors_in_file("# Introduction\n") == {"introduction"}

    def test_multiple_heading_levels(self) -> None:
        content = "# Top\n## Sub\n### Deep\n"
        assert anchors_in_file(content) == {"top", "sub", "deep"}

    def test_mixed_content(self) -> None:
        content = "# Quick Start\n\nSome text.\n\n## Installation\n"
        assert anchors_in_file(content) == {"quick-start", "installation"}

    def test_no_headings(self) -> None:
        assert anchors_in_file("Just plain text.") == set()

    def test_heading_with_special_chars(self) -> None:
        assert "api-reference-v2" in anchors_in_file("## API Reference (v2)\n")


# ─── Internal link validation ─────────────────────────────────────────────────


class TestInternalLinks:
    """validate_links with strict=False (default) — no network, filesystem only."""

    def test_valid_link(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("[setup](setup.md)")
        (docs / "setup.md").write_text("# Setup\n")
        assert validate_links(tmp_path) == []

    def test_missing_target_file(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("[ghost](ghost.md)")
        errors = validate_links(tmp_path)
        assert len(errors) == 1
        assert "ghost.md" in errors[0]

    def test_valid_anchor(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("[section](guide.md#installation)")
        (docs / "guide.md").write_text("# Guide\n\n## Installation\n")
        assert validate_links(tmp_path) == []

    def test_invalid_anchor(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("[broken](guide.md#nonexistent)")
        (docs / "guide.md").write_text("# Guide\n")
        errors = validate_links(tmp_path)
        assert len(errors) == 1
        assert "nonexistent" in errors[0]

    def test_link_in_fenced_block_ignored(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("```\n[fake](ghost.md)\n```\n")
        assert validate_links(tmp_path) == []

    def test_path_traversal_rejected(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("[escape](../../etc/passwd)")
        errors = validate_links(tmp_path)
        assert len(errors) == 1
        assert "outside" in errors[0]

    def test_extension_less_link_resolves(self, tmp_path: Path) -> None:
        """MkDocs pretty URLs: [setup](setup) should resolve to setup.md."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("[setup](setup)")
        (docs / "setup.md").write_text("# Setup\n")
        assert validate_links(tmp_path) == []

    def test_directory_index_link_resolves(self, tmp_path: Path) -> None:
        """[section](section/) should resolve to section/index.md."""
        docs = tmp_path / "docs"
        docs.mkdir()
        section = docs / "section"
        section.mkdir()
        (section / "index.md").write_text("# Section\n")
        (docs / "index.md").write_text("[section](section/)")
        assert validate_links(tmp_path) == []

    def test_non_markdown_asset_missing_reported(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("[dl](files/report.pdf)")
        errors = validate_links(tmp_path)
        assert len(errors) == 1
        assert "report.pdf" in errors[0]

    def test_non_markdown_asset_exists_ok(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "files").mkdir()
        (docs / "files" / "report.pdf").write_bytes(b"%PDF")
        (docs / "index.md").write_text("[dl](files/report.pdf)")
        assert validate_links(tmp_path) == []

    def test_skip_schemes_ignored(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text(
            "[mail](mailto:dev@example.com)\n[data](data:text/plain,hello)\n"
        )
        assert validate_links(tmp_path) == []

    def test_docs_dir_missing_returns_empty(self, tmp_path: Path) -> None:
        assert validate_links(tmp_path) == []

    def test_symlinks_skipped(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        real = tmp_path / "real.md"
        real.write_text("[broken](ghost.md)")
        (docs / "linked.md").symlink_to(real)
        assert validate_links(tmp_path) == []

    def test_excluded_dir_not_scanned(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        overrides = docs / "overrides"
        overrides.mkdir()
        (overrides / "page.md").write_text("[broken](ghost.md)")
        (tmp_path / "zenzic.toml").write_text('excluded_dirs = ["overrides"]\n')
        assert validate_links(tmp_path) == []

    def test_errors_are_sorted(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "a.md").write_text("[z](zzz.md)")
        (docs / "b.md").write_text("[a](aaa.md)")
        errors = validate_links(tmp_path)
        assert errors == sorted(errors)

    @pytest.mark.slow
    def test_anchor_torture_parallel_indexing_1000_files(self, tmp_path: Path) -> None:
        """1000 cross-linked anchors must validate without race-induced false positives."""
        docs = tmp_path / "docs"
        docs.mkdir()

        total = 1000
        for i in range(total):
            nxt = (i + 1) % total
            (docs / f"page_{i:04d}.md").write_text(
                "\n".join(
                    [
                        f"# Page {i}",
                        f"## Section {i}",
                        "",
                        f"Forward link: [next](page_{nxt:04d}.md#section-{nxt})",
                        "",
                        "This page is part of the anchor torture fixture and remains deterministic.",
                    ]
                ),
                encoding="utf-8",
            )

        assert validate_links(tmp_path) == []


# ─── Absolute-path prohibition ───────────────────────────────────────────────


class TestAbsolutePathProhibition:
    """Absolute internal links (starting with /) must be rejected."""

    def test_absolute_link_is_error(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("[logo](/assets/logo.png)\n")
        (docs / "assets").mkdir()
        (docs / "assets" / "logo.png").write_bytes(b"")
        errors = validate_links(tmp_path)
        assert len(errors) == 1
        assert "/assets/logo.png" in errors[0]
        assert "absolute path" in errors[0]

    def test_absolute_link_to_md_is_error(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("[guide](/guide.md)\n")
        (docs / "guide.md").write_text("# Guide\n")
        errors = validate_links(tmp_path)
        assert len(errors) == 1
        assert "absolute path" in errors[0]

    def test_relative_link_not_affected(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("[guide](guide.md)\n")
        (docs / "guide.md").write_text("# Guide\n")
        assert validate_links(tmp_path) == []

    def test_external_https_not_affected(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("[ext](https://example.com)\n")
        assert validate_links(tmp_path) == []

    def test_absolute_path_with_anchor_is_error(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("[section](/guide.md#intro)\n")
        (docs / "guide.md").write_text("# Intro\n")
        errors = validate_links(tmp_path)
        assert len(errors) == 1
        assert "absolute path" in errors[0]


# ─── S4-2: known_assets pre-map + excluded_build_artifacts ───────────────────


class TestAssetPreMap:
    """Verify that asset validation is entirely in-memory after Pass 1.

    The key invariant: once known_assets is built in Pass 1, no Path.exists()
    call must occur inside the Pass 2 link-resolution loop.
    """

    def test_existing_asset_link_is_valid(self, tmp_path: Path) -> None:
        """A link to a non-.md file that exists in docs/ produces no error."""
        docs = tmp_path / "docs"
        (docs / "assets").mkdir(parents=True)
        (docs / "assets" / "logo.png").write_bytes(b"\x89PNG")
        (docs / "index.md").write_text("![logo](assets/logo.png)")
        assert validate_links(tmp_path) == []

    def test_missing_asset_link_is_reported(self, tmp_path: Path) -> None:
        """A link to a non-.md file that does NOT exist in docs/ is an error."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("[dl](files/report.pdf)")
        errors = validate_links(tmp_path)
        assert len(errors) == 1
        assert "report.pdf" in errors[0]

    def test_excluded_build_artifact_not_reported(self, tmp_path: Path) -> None:
        """Links to build-time generated assets (matching excluded_build_artifacts) are suppressed."""
        docs = tmp_path / "docs"
        (docs / "pdf").mkdir(parents=True)
        # pdf/document.pdf does NOT exist — generated by to-pdf at build time
        (docs / "index.md").write_text("[PDF](pdf/document.pdf)")
        (tmp_path / "zenzic.toml").write_text('excluded_build_artifacts = ["pdf/*.pdf"]\n')
        assert validate_links(tmp_path) == []

    def test_excluded_build_artifact_does_not_suppress_other_missing(self, tmp_path: Path) -> None:
        """excluded_build_artifacts patterns are scoped — non-matching missing assets still error."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("[PDF](pdf/document.pdf)\n[broken](other/file.zip)")
        (tmp_path / "zenzic.toml").write_text('excluded_build_artifacts = ["pdf/*.pdf"]\n')
        errors = validate_links(tmp_path)
        assert len(errors) == 1
        assert "file.zip" in errors[0]

    def test_absolute_asset_link_is_prohibited(self, tmp_path: Path) -> None:
        """Site-absolute asset links (/assets/logo.png) are now prohibited.

        Absolute paths break portability when the site is hosted in a
        subdirectory. The Absolute Link Prohibition rule catches them before
        any asset lookup, so the file existence is irrelevant.
        """
        docs = tmp_path / "docs"
        (docs / "assets").mkdir(parents=True)
        (docs / "assets" / "logo.png").write_bytes(b"\x89PNG")
        (docs / "index.md").write_text("![logo](/assets/logo.png)")
        errors = validate_links(tmp_path)
        assert len(errors) == 1
        assert "absolute path" in errors[0]

    def test_asset_case_sensitivity_linux(self, tmp_path: Path) -> None:
        """known_assets lookup is case-sensitive (Standard Unix/Web behaviour).

        Zenzic targets correctness on the canonical web platform (Linux/POSIX).
        ``documento.pdf`` and ``Documento.pdf`` are distinct files — a link to
        the wrong casing must be reported as a missing asset.

        Policy: Zenzic is case-sensitive by default.  Authors must use the
        exact case as on disk.  This matches the behaviour of web servers
        serving static files on Linux and avoids silent breakage when deploying
        a site built on macOS (case-insensitive HFS+) to a Linux host.
        """
        docs = tmp_path / "docs"
        (docs / "assets").mkdir(parents=True)
        # Only the lowercase file exists on disk
        (docs / "assets" / "documento.pdf").write_bytes(b"%PDF")
        (docs / "index.md").write_text("[PDF](assets/Documento.pdf)")  # wrong case
        errors = validate_links(tmp_path)
        # On Linux (case-sensitive FS) the wrong-case link must be reported.
        # This test is authoritative on Linux CI; on macOS it may pass silently
        # due to HFS+ case-folding — that is a known platform divergence.
        import sys

        if sys.platform.startswith("linux"):
            assert len(errors) == 1
            assert "Documento.pdf" in errors[0]

    def test_no_path_exists_called_in_pass2(self, tmp_path: Path) -> None:
        """Path.exists() must not be called during Pass 2 (hot path is I/O-free)."""
        docs = tmp_path / "docs"
        (docs / "pdf").mkdir(parents=True)
        (docs / "pdf" / "real.pdf").write_bytes(b"%PDF")
        (docs / "index.md").write_text("[dl](pdf/real.pdf)")

        call_log: list[str] = []

        original_exists = Path.exists

        def spy_exists(self: Path) -> bool:  # type: ignore[override]
            call_log.append(str(self))
            return original_exists(self)

        with patch.object(Path, "exists", spy_exists):
            errors = validate_links(tmp_path)

        assert errors == []
        # Pass 1 I/O is permitted (docs_root.is_dir(), rglob traversal calls exist internally).
        # The critical assertion: the resolved PDF path must NOT appear in call_log —
        # it must be found in known_assets without a disk call.
        pdf_str = str((docs / "pdf" / "real.pdf").resolve())
        assert pdf_str not in call_log, (
            f"Path.exists() was called for {pdf_str} — asset check is not in-memory!"
        )


# ─── S4-3: i18n fallback_to_default ─────────────────────────────────────────


def _mkdocs_i18n_folder(fallback: bool = True) -> str:
    """Return a minimal mkdocs.yml snippet with folder-mode i18n."""
    fallback_str = "true" if fallback else "false"
    return (
        "site_name: Test\n"
        "plugins:\n"
        "  - i18n:\n"
        "      docs_structure: folder\n"
        f"      fallback_to_default: {fallback_str}\n"
        "      languages:\n"
        "        - locale: en\n"
        "          default: true\n"
        "          build: true\n"
        "        - locale: it\n"
        "          build: true\n"
    )


class TestI18nFallbackIntegration:
    """Integration tests: validate_links with i18n fallback semantics."""

    def _setup(self, tmp_path: Path, *, fallback: bool = True) -> tuple[Path, Path, Path]:
        """Create a minimal folder-mode i18n repo. Returns (repo, docs, docs_it)."""
        docs = tmp_path / "docs"
        docs_it = docs / "it"
        docs_it.mkdir(parents=True)
        (tmp_path / "mkdocs.yml").write_text(_mkdocs_i18n_folder(fallback=fallback))
        return tmp_path, docs, docs_it

    def test_fallback_suppresses_untranslated_md_link(self, tmp_path: Path) -> None:
        """Link from it/ to an untranslated page is suppressed when fallback is on.

        docs/it/guide.md links to api.md (intra-locale).  The resolver looks for
        docs/it/api.md — which does not exist — producing FileNotFound.  Fallback
        then checks docs/api.md (default locale), finds it, and suppresses the error.
        """
        repo, docs, docs_it = self._setup(tmp_path)
        # Default-locale file exists; translated equivalent is absent.
        (docs / "api.md").write_text("# API\n")
        (docs_it / "guide.md").write_text("[api](api.md)\n")
        assert validate_links(repo) == []

    def test_no_fallback_reports_untranslated_md_link(self, tmp_path: Path) -> None:
        """Same intra-locale link is reported when fallback_to_default is false."""
        repo, docs, docs_it = self._setup(tmp_path, fallback=False)
        (docs / "api.md").write_text("# API\n")
        (docs_it / "guide.md").write_text("[api](api.md)\n")
        errors = validate_links(repo)
        assert len(errors) == 1
        assert "api.md" in errors[0]

    def test_fallback_reports_link_missing_in_both_locales(self, tmp_path: Path) -> None:
        """A page missing in BOTH locales is always reported as broken."""
        repo, docs, docs_it = self._setup(tmp_path)
        # ghost.md absent from both docs/ and docs/it/ — fallback cannot rescue it.
        (docs_it / "guide.md").write_text("[ghost](ghost.md)\n")
        errors = validate_links(repo)
        assert any("ghost" in e for e in errors)

    def test_fallback_suppresses_asset_missing_in_locale(self, tmp_path: Path) -> None:
        """Asset missing in it/ but present in default locale is suppressed by fallback."""
        repo, docs, docs_it = self._setup(tmp_path)
        (docs / "assets").mkdir()
        (docs / "assets" / "logo.png").write_bytes(b"\x89PNG")
        # docs/it/assets/logo.png absent — intra-locale relative link triggers FileNotFound.
        # Fallback maps docs/it/assets/logo.png → docs/assets/logo.png (in known_assets).
        (docs_it / "guide.md").write_text("![logo](assets/logo.png)\n")
        assert validate_links(repo) == []

    def test_direct_cross_locale_link_resolves_without_warning(self, tmp_path: Path) -> None:
        """A link from it/ that navigates directly to an EN file is Resolved (not FileNotFound).

        ../guide.md from docs/it/index.md normalises to docs/guide.md which exists
        directly — Resolved, no fallback logic involved.
        """
        repo, docs, docs_it = self._setup(tmp_path)
        (docs / "guide.md").write_text("# EN Guide\n")
        (docs_it / "index.md").write_text("[EN guide](../guide.md)\n")
        assert validate_links(repo) == []

    def test_config_error_no_default_locale(self, tmp_path: Path) -> None:
        """ConfigurationError when fallback=true but no default locale is declared."""
        from zenzic.core.exceptions import ConfigurationError

        docs = tmp_path / "docs"
        (docs / "it").mkdir(parents=True)
        bad_config = (
            "plugins:\n  - i18n:\n      docs_structure: folder\n"
            "      fallback_to_default: true\n"
            "      languages:\n        - locale: en\n        - locale: it\n"
        )
        (tmp_path / "mkdocs.yml").write_text(bad_config)
        (docs / "index.md").touch()
        with pytest.raises(ConfigurationError):
            validate_links(tmp_path)

    # ── Anchor i18n fallback tests ─────────────────────────────────────────────

    def test_anchor_fallback_suppresses_translated_heading_miss(self, tmp_path: Path) -> None:
        """Anchor present in EN file but absent in IT file is suppressed by fallback.

        Scenario: docs/it/guide.md links to architecture.md#quick-start.
        The resolver normalises the target to docs/it/architecture.md (exists).
        docs/it/architecture.md uses translated headings, so "quick-start" is
        absent from its anchor set — AnchorMissing is produced.
        Fallback checks docs/architecture.md, finds "quick-start", and suppresses.
        """
        repo, docs, docs_it = self._setup(tmp_path)
        # EN file has the target anchor; IT file has a translated heading.
        (docs / "architecture.md").write_text("# Architecture\n\n## Quick Start\n")
        (docs_it / "architecture.md").write_text("# Architettura\n\n## Avvio Rapido\n")
        (docs_it / "guide.md").write_text("[qs](architecture.md#quick-start)\n")
        assert validate_links(repo) == []

    def test_anchor_fallback_reports_when_anchor_missing_in_both_locales(
        self, tmp_path: Path
    ) -> None:
        """An anchor absent in BOTH the IT and EN files is always reported.

        Fallback can only suppress the error when the EN file contains the anchor.
        If neither locale has it, the link is genuinely broken.
        """
        repo, docs, docs_it = self._setup(tmp_path)
        (docs / "architecture.md").write_text("# Architecture\n\n## Overview\n")
        (docs_it / "architecture.md").write_text("# Architettura\n\n## Panoramica\n")
        # "ghost-anchor" exists in neither EN nor IT file.
        (docs_it / "guide.md").write_text("[x](architecture.md#ghost-anchor)\n")
        errors = validate_links(repo)
        assert any("ghost-anchor" in e for e in errors)

    def test_anchor_fallback_disabled_reports_translated_heading_miss(self, tmp_path: Path) -> None:
        """When fallback_to_default is false, translated-heading misses are reported."""
        repo, docs, docs_it = self._setup(tmp_path, fallback=False)
        (docs / "architecture.md").write_text("# Architecture\n\n## Quick Start\n")
        (docs_it / "architecture.md").write_text("# Architettura\n\n## Avvio Rapido\n")
        (docs_it / "guide.md").write_text("[qs](architecture.md#quick-start)\n")
        errors = validate_links(repo)
        assert any("quick-start" in e for e in errors)

    def test_anchor_fallback_not_triggered_for_en_file_anchor_miss(self, tmp_path: Path) -> None:
        """A broken anchor in a default-locale (EN) file is always reported.

        Fallback suppression only applies when the source file is inside a
        non-default locale directory.  A link from docs/guide.md to
        docs/page.md#ghost must still be reported even with fallback enabled.
        """
        repo, docs, docs_it = self._setup(tmp_path)
        (docs / "page.md").write_text("# Page\n\n## Real Heading\n")
        (docs / "guide.md").write_text("[x](page.md#ghost-anchor)\n")
        errors = validate_links(repo)
        assert any("ghost-anchor" in e for e in errors)

    def test_anchor_in_it_file_resolves_directly_without_fallback(self, tmp_path: Path) -> None:
        """An anchor that exists in the IT file itself resolves without touching fallback."""
        repo, docs, docs_it = self._setup(tmp_path)
        (docs_it / "architecture.md").write_text("# Architettura\n\n## Avvio Rapido\n")
        (docs_it / "guide.md").write_text("[ar](architecture.md#avvio-rapido)\n")
        assert validate_links(repo) == []


# ─── S4-4: Reference-style link resolution ───────────────────────────────────


class TestBuildRefMap:
    """Unit tests for _build_ref_map (pure function)."""

    def test_basic_definition(self) -> None:
        assert _build_ref_map("[guide]: guide.md\n") == {"guide": "guide.md"}

    def test_case_insensitive_id(self) -> None:
        """CommonMark §4.7: reference IDs are case-insensitive."""
        result = _build_ref_map("[Guide]: guide.md\n[INSTALL]: install.md\n")
        assert result == {"guide": "guide.md", "install": "install.md"}

    def test_first_definition_wins(self) -> None:
        text = "[ref]: first.md\n[ref]: second.md\n"
        assert _build_ref_map(text) == {"ref": "first.md"}

    def test_skips_code_block(self) -> None:
        text = "```\n[in-block]: ghost.md\n```\n[real]: real.md\n"
        assert _build_ref_map(text) == {"real": "real.md"}

    def test_external_url_preserved(self) -> None:
        assert _build_ref_map("[ext]: https://example.com\n") == {"ext": "https://example.com"}

    def test_empty_content(self) -> None:
        assert _build_ref_map("") == {}

    def test_no_definitions(self) -> None:
        assert _build_ref_map("Just [some](inline.md) text.\n") == {}


class TestExtractRefLinks:
    """Unit tests for extract_ref_links (pure function)."""

    def test_simple_ref_link(self) -> None:
        text = "[guide][ref]\n[ref]: guide.md\n"
        ref_map = _build_ref_map(text)
        assert extract_ref_links(text, ref_map) == [("guide.md", 1)]

    def test_collapsed_ref_link(self) -> None:
        text = "[guide][]\n[guide]: guide.md\n"
        ref_map = _build_ref_map(text)
        links = [url for url, _ in extract_ref_links(text, ref_map)]
        assert "guide.md" in links

    def test_undefined_id_not_returned(self) -> None:
        text = "[ghost][undefined]\n"
        assert extract_ref_links(text, {}) == []

    def test_case_insensitive_lookup(self) -> None:
        ref_map = {"guide": "guide.md"}
        text = "[text][GUIDE]\n"
        links = [url for url, _ in extract_ref_links(text, ref_map)]
        assert "guide.md" in links

    def test_skips_fenced_block(self) -> None:
        text = "```\n[fake][ref]\n```\n[real][ref]\n"
        ref_map = {"ref": "target.md"}
        links = extract_ref_links(text, ref_map)
        assert len(links) == 1
        assert links[0][1] == 4  # line 4 (outside block)

    def test_skips_inline_code(self) -> None:
        text = "Use `[fake][ref]` syntax. [real][ref]\n"
        ref_map = {"ref": "target.md"}
        links = extract_ref_links(text, ref_map)
        assert len(links) == 1


class TestRefLinkValidation:
    """Integration: validate_links resolves reference-style links as internal links."""

    def test_ref_link_to_existing_md(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("[guide][ref]\n\n[ref]: guide.md\n")
        (docs / "guide.md").write_text("# Guide\n")
        assert validate_links(tmp_path) == []

    def test_ref_link_to_missing_md_reported(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("[ghost][ref]\n\n[ref]: ghost.md\n")
        errors = validate_links(tmp_path)
        assert any("ghost.md" in e for e in errors)

    def test_ref_link_external_url_checked_in_strict(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("[ext][ref]\n\n[ref]: https://example.com\n")
        with patch("zenzic.core.validator._ping_url", new=AsyncMock(return_value=None)):
            errors = validate_links(tmp_path, strict=True)
        assert errors == []

    def test_ref_link_case_insensitive_id(self, tmp_path: Path) -> None:
        """[text][ID] must resolve the same as [text][id]."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("[guide][GUIDE]\n\n[guide]: guide.md\n")
        (docs / "guide.md").write_text("# Guide\n")
        assert validate_links(tmp_path) == []

    def test_ref_link_with_anchor(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("[sec][ref]\n\n[ref]: guide.md#installation\n")
        (docs / "guide.md").write_text("# Guide\n## Installation\n")
        assert validate_links(tmp_path) == []


# ─── External link validation (httpx mocked via _ping_url) ───────────────────


class TestExternalLinks:
    """External link checks require strict=True.

    ``_ping_url`` is patched at module level so no real HTTP requests are made.
    The httpx.AsyncClient is still constructed but never used to send traffic.
    """

    def _setup_docs(self, tmp_path: Path, content: str) -> None:
        docs = tmp_path / "docs"
        docs.mkdir(exist_ok=True)
        (docs / "index.md").write_text(content)

    def test_strict_false_never_pings_external(self, tmp_path: Path) -> None:
        """With strict=False, _ping_url must never be invoked."""
        self._setup_docs(tmp_path, "[link](https://example.com/404)")
        mock_ping = AsyncMock(return_value=None)
        with patch("zenzic.core.validator._ping_url", new=mock_ping):
            errors = validate_links(tmp_path, strict=False)
        mock_ping.assert_not_called()
        assert errors == []

    def test_http_200_no_error(self, tmp_path: Path) -> None:
        self._setup_docs(tmp_path, "[link](https://example.com)")
        with patch("zenzic.core.validator._ping_url", new=AsyncMock(return_value=None)):
            errors = validate_links(tmp_path, strict=True)
        assert errors == []

    def test_http_404_reported(self, tmp_path: Path) -> None:
        url = "https://example.com/missing"
        self._setup_docs(tmp_path, f"[broken]({url})")
        err_msg = f"external link '{url}' returned HTTP 404"
        with patch("zenzic.core.validator._ping_url", new=AsyncMock(return_value=err_msg)):
            errors = validate_links(tmp_path, strict=True)
        assert len(errors) == 1
        assert "404" in errors[0]

    def test_http_403_treated_as_alive(self, tmp_path: Path) -> None:
        """403 is returned by _ping_url as None (no error) — servers restricting bots."""
        self._setup_docs(tmp_path, "[link](https://github.com)")
        with patch("zenzic.core.validator._ping_url", new=AsyncMock(return_value=None)):
            errors = validate_links(tmp_path, strict=True)
        assert errors == []

    def test_timeout_reported(self, tmp_path: Path) -> None:
        url = "https://slow.example.com"
        self._setup_docs(tmp_path, f"[slow]({url})")
        err_msg = f"external link '{url}' timed out (>10 s)"
        with patch("zenzic.core.validator._ping_url", new=AsyncMock(return_value=err_msg)):
            errors = validate_links(tmp_path, strict=True)
        assert len(errors) == 1
        assert "timed out" in errors[0]

    def test_connection_error_reported(self, tmp_path: Path) -> None:
        url = "https://unreachable.invalid"
        self._setup_docs(tmp_path, f"[dead]({url})")
        err_msg = f"external link '{url}' — connection error: [Errno -2] Name or service not known"
        with patch("zenzic.core.validator._ping_url", new=AsyncMock(return_value=err_msg)):
            errors = validate_links(tmp_path, strict=True)
        assert len(errors) == 1
        assert "connection error" in errors[0]

    def test_duplicate_url_pinged_exactly_once(self, tmp_path: Path) -> None:
        """The same URL in two files must result in exactly one HTTP request."""
        url = "https://example.com"
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "a.md").write_text(f"[link]({url})")
        (docs / "b.md").write_text(f"[link]({url})")
        mock_ping = AsyncMock(return_value=None)
        with patch("zenzic.core.validator._ping_url", new=mock_ping):
            validate_links(tmp_path, strict=True)
        assert mock_ping.call_count == 1

    def test_mixed_internal_and_external_errors(self, tmp_path: Path) -> None:
        """Both internal and external errors are returned together."""
        docs = tmp_path / "docs"
        docs.mkdir()
        url = "https://dead.example.com"
        (docs / "index.md").write_text(f"[broken-internal](ghost.md)\n[broken-external]({url})\n")
        err_msg = f"external link '{url}' returned HTTP 404"
        with patch("zenzic.core.validator._ping_url", new=AsyncMock(return_value=err_msg)):
            errors = validate_links(tmp_path, strict=True)
        assert len(errors) == 2
        assert any("ghost.md" in e for e in errors)
        assert any("404" in e for e in errors)

    def test_semaphore_constant_is_positive_int(self) -> None:
        """Sanity check: concurrency limit must be a positive integer."""
        assert isinstance(_MAX_CONCURRENT_REQUESTS, int)
        assert _MAX_CONCURRENT_REQUESTS > 0


# ─── Python snippet validation (unchanged behaviour) ─────────────────────────


def test_validate_snippets_valid_and_invalid(tmp_path: Path) -> None:
    repo = tmp_path / "my_repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)

    (docs / "valid.md").write_text("# Valid\n```python\ndef add(a, b):\n    return a + b\n```\n")
    (docs / "invalid.md").write_text(
        '# Invalid\n```python title="script.py"\ndef broken(a, b)\n    return a + b\n```\n'
    )
    # Short snippet below min_lines threshold — must be skipped
    (docs / "short.md").write_text("# Short\n```python\nx = 1\n```\n")

    # Excluded directory — must be skipped entirely
    includes = docs / "includes"
    includes.mkdir()
    (includes / "inc.md").write_text("# Inc\n```python\ninvalid syntax here\n```\n")

    config = ZenzicConfig(snippet_min_lines=2, excluded_dirs=["includes"])
    errors = validate_snippets(repo, config)

    assert len(errors) == 1
    assert errors[0].file_path.name == "invalid.md"
    assert "SyntaxError in Python snippet" in errors[0].message


def test_validate_snippets_no_code_blocks(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "page.md").write_text("No code blocks here.")
    assert validate_snippets(tmp_path) == []


def test_validate_snippets_docs_not_exist(tmp_path: Path) -> None:
    assert validate_snippets(tmp_path) == []


def test_validate_snippets_symlink_skipped(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    real_file = tmp_path / "real.md"
    real_file.write_text("```python\ndef broken(\n```")
    (docs / "linked.md").symlink_to(real_file)
    assert validate_snippets(tmp_path) == []


def test_validate_snippets_generic_exception_reported(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "page.md").write_text("```python\nx = 1\n```")
    with patch("zenzic.core.validator.compile", side_effect=MemoryError("oom")):
        errors = validate_snippets(tmp_path, ZenzicConfig(snippet_min_lines=1))
    assert len(errors) == 1
    assert "ParserError" in errors[0].message


# ─── YAML snippet validation ──────────────────────────────────────────────────


def test_validate_snippets_yaml_valid(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "page.md").write_text("```yaml\nkey: value\nlist:\n  - a\n  - b\n```\n")
    assert validate_snippets(tmp_path, ZenzicConfig(snippet_min_lines=1)) == []


def test_validate_snippets_yaml_invalid(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "page.md").write_text("```yaml\nkey: [\nunclosed bracket\n```\n")
    errors = validate_snippets(tmp_path, ZenzicConfig(snippet_min_lines=1))
    assert len(errors) == 1
    assert "SyntaxError in YAML snippet" in errors[0].message


def test_validate_snippets_yml_alias_invalid(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "page.md").write_text("```yml\n: bad mapping\n```\n")
    errors = validate_snippets(tmp_path, ZenzicConfig(snippet_min_lines=1))
    assert len(errors) == 1
    assert "SyntaxError in YAML snippet" in errors[0].message


# ─── JSON snippet validation ──────────────────────────────────────────────────


def test_validate_snippets_json_valid(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "page.md").write_text('```json\n{"key": "value", "num": 42}\n```\n')
    assert validate_snippets(tmp_path, ZenzicConfig(snippet_min_lines=1)) == []


def test_validate_snippets_json_invalid(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "page.md").write_text('```json\n{"key": "value",}\n```\n')
    errors = validate_snippets(tmp_path, ZenzicConfig(snippet_min_lines=1))
    assert len(errors) == 1
    assert "SyntaxError in JSON snippet" in errors[0].message


def test_validate_snippets_json_line_number(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    # fence opens at line 3 (two preceding lines), error is on line 2 of snippet
    (docs / "page.md").write_text("# Page\n\n```json\n{\n  bad\n}\n```\n")
    errors = validate_snippets(tmp_path, ZenzicConfig(snippet_min_lines=1))
    assert len(errors) == 1
    # fence_line=3, json error lineno=2 → reported line 5
    assert errors[0].line_no == 5


# ─── TOML snippet validation ──────────────────────────────────────────────────


def test_validate_snippets_toml_valid(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "page.md").write_text('```toml\ntitle = "Zenzic"\nversion = "0.4.0"\n```\n')
    assert validate_snippets(tmp_path, ZenzicConfig(snippet_min_lines=1)) == []


def test_validate_snippets_toml_invalid(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "page.md").write_text("```toml\ntitle = Zenzic  # missing quotes\n```\n")
    errors = validate_snippets(tmp_path, ZenzicConfig(snippet_min_lines=1))
    assert len(errors) == 1
    assert "SyntaxError in TOML snippet" in errors[0].message
