# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""TEAM BLUE — i18n fallback / cross-locale resolution edge-case tests.

Tests: links from locale files to default-locale assets, missing locale
directories, partial translations, locale codes with variants (pt-BR).
"""

from __future__ import annotations

from pathlib import Path

from zenzic.core.adapters._utils import remap_to_default_locale


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
        assert result == Path("/docs")

    def test_locale_asset_not_md(self) -> None:
        """Non-md files (images) should also remap correctly."""
        result = remap_to_default_locale(
            Path("/docs/it/img/logo.png"), Path("/docs"), frozenset({"it"})
        )
        assert result == Path("/docs/img/logo.png")
