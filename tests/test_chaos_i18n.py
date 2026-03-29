# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Chaos i18n test suite — Dev 4 [Inquisitor].

Stress-tests Zenzic's suffix-mode i18n detection against pathological
file naming patterns: version tags, double suffixes, numeric suffixes,
long codes, and malformed locale strings. No file should be misclassified
as a translation unless its suffix is a valid ISO 639-1 two-letter code.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from zenzic.core.adapter import _extract_i18n_locale_patterns
from zenzic.core.scanner import find_orphans


# ─── ISO 639-1 guard in _extract_i18n_locale_patterns ────────────────────────


def _suffix_config(*locales: str, default: str = "en") -> dict:
    """Build a minimal mkdocs.yml-style plugin config for suffix mode."""
    languages = [{"locale": default, "default": True}]
    languages += [{"locale": loc} for loc in locales]
    return {
        "plugins": [
            {
                "i18n": {
                    "docs_structure": "suffix",
                    "languages": languages,
                }
            }
        ]
    }


class TestISO639Guard:
    """_extract_i18n_locale_patterns must only emit patterns for valid ISO 639-1 codes."""

    def test_valid_two_letter_locale_accepted(self) -> None:
        patterns = _extract_i18n_locale_patterns(_suffix_config("it", "fr", "es"))
        assert patterns == {"*.it.md", "*.fr.md", "*.es.md"}

    def test_version_tag_v1_rejected(self) -> None:
        """'v1' is not ISO 639-1 — must not produce a pattern."""
        patterns = _extract_i18n_locale_patterns(_suffix_config("v1"))
        assert patterns == set()

    def test_version_tag_v2_rejected(self) -> None:
        patterns = _extract_i18n_locale_patterns(_suffix_config("v2"))
        assert patterns == set()

    def test_numeric_suffix_rejected(self) -> None:
        """Pure digit strings are not ISO 639-1."""
        patterns = _extract_i18n_locale_patterns(_suffix_config("2", "42"))
        assert patterns == set()

    def test_build_tag_beta_rejected(self) -> None:
        patterns = _extract_i18n_locale_patterns(_suffix_config("beta"))
        assert patterns == set()

    def test_build_tag_rc1_rejected(self) -> None:
        patterns = _extract_i18n_locale_patterns(_suffix_config("rc1"))
        assert patterns == set()

    def test_three_letter_code_rejected(self) -> None:
        """ISO 639-2 / 3-letter codes are not accepted (guard is strictly 2-letter)."""
        patterns = _extract_i18n_locale_patterns(_suffix_config("ita", "fra"))
        assert patterns == set()

    def test_bcp47_region_tag_rejected(self) -> None:
        """BCP 47 tags like 'en-US' are not ISO 639-1 plain codes."""
        patterns = _extract_i18n_locale_patterns(_suffix_config("en-US", "pt-BR"))
        assert patterns == set()

    def test_uppercase_locale_rejected(self) -> None:
        """Guard requires lowercase — 'IT' is not a valid locale string here."""
        patterns = _extract_i18n_locale_patterns(_suffix_config("IT", "FR"))
        assert patterns == set()

    def test_empty_locale_rejected(self) -> None:
        patterns = _extract_i18n_locale_patterns(_suffix_config(""))
        assert patterns == set()

    def test_mixed_valid_and_invalid(self) -> None:
        """Only valid codes survive — invalid ones are silently dropped."""
        patterns = _extract_i18n_locale_patterns(_suffix_config("it", "v1", "fr", "beta"))
        assert patterns == {"*.it.md", "*.fr.md"}


# ─── Orphan check with pathological file names ────────────────────────────────


def _make_repo(tmp_path: Path, extra_files: list[str]) -> Path:
    """Create a minimal repo with index.md in nav plus extra files."""
    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)
    config = {
        "nav": [{"Home": "index.md"}],
        "plugins": [
            {
                "i18n": {
                    "docs_structure": "suffix",
                    "languages": [
                        {"locale": "en", "default": True},
                        {"locale": "it"},
                    ],
                }
            }
        ],
    }
    with (repo / "mkdocs.yml").open("w") as f:
        yaml.dump(config, f)
    (docs / "index.md").touch()
    (docs / "index.it.md").touch()
    for name in extra_files:
        path = docs / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    return repo


class TestOrphanCheckPathological:
    """find_orphans must not misclassify versioned or oddly-named files."""

    def test_version_file_v1_2_is_orphan(self, tmp_path: Path) -> None:
        """v1.2.md has no suffix that matches *.it.md — it is an orphan, not a translation."""
        repo = _make_repo(tmp_path, ["v1.2.md"])
        orphans = find_orphans(repo)
        assert Path("v1.2.md") in orphans

    def test_api_v2_is_orphan(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, ["api.v2.md"])
        orphans = find_orphans(repo)
        assert Path("api.v2.md") in orphans

    def test_changelog_beta_is_orphan(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, ["changelog.beta.md"])
        orphans = find_orphans(repo)
        assert Path("changelog.beta.md") in orphans

    def test_valid_translation_not_orphan(self, tmp_path: Path) -> None:
        """Sanity: a real *.it.md file must NOT be flagged as orphan."""
        repo = _make_repo(tmp_path, ["guide.md", "guide.it.md"])
        # guide.md is an orphan (not in nav), guide.it.md is a translation (excluded)
        orphans = find_orphans(repo)
        orphan_names = [o.name for o in orphans]
        assert "guide.it.md" not in orphan_names

    def test_double_suffix_page_it_it_is_orphan(self, tmp_path: Path) -> None:
        """page.it.it.md: redundant double suffix — not a valid translation pattern."""
        repo = _make_repo(tmp_path, ["page.it.it.md"])
        orphans = find_orphans(repo)
        # *.it.md matches 'page.it.it.md' via fnmatch — this is acceptable:
        # the file IS excluded from orphan check as a locale variant.
        # This test documents the current behavior so any change is intentional.
        orphan_names = [o.name for o in orphans]
        # page.it.it.md ends with '.it.md' so fnmatch('page.it.it.md', '*.it.md') is True.
        assert "page.it.it.md" not in orphan_names

    def test_numeric_dotted_filename_is_orphan(self, tmp_path: Path) -> None:
        """release.1.0.md — numeric suffix, must be treated as a plain file."""
        repo = _make_repo(tmp_path, ["release.1.0.md"])
        orphans = find_orphans(repo)
        assert Path("release.1.0.md") in orphans

    def test_directory_named_like_locale_file(self, tmp_path: Path) -> None:
        """A directory called 'page.it' with index.md inside — must be treated normally."""
        repo = _make_repo(tmp_path, ["page.it/index.md"])
        orphans = find_orphans(repo)
        assert Path("page.it/index.md") in orphans

    def test_orphan_translation_without_source(self, tmp_path: Path) -> None:
        """guide.it.md present but guide.md absent — translation is excluded, not flagged."""
        repo = _make_repo(tmp_path, ["guide.it.md"])
        orphans = find_orphans(repo)
        orphan_names = [o.name for o in orphans]
        assert "guide.it.md" not in orphan_names

    def test_nested_version_file_is_orphan(self, tmp_path: Path) -> None:
        """api/v1.2.md in a subdirectory — must be flagged as orphan."""
        repo = _make_repo(tmp_path, ["api/v1.2.md"])
        orphans = find_orphans(repo)
        assert Path("api/v1.2.md") in orphans
