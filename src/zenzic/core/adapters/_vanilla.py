# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""VanillaAdapter — no-op adapter for projects with no recognised build engine."""

from __future__ import annotations

from pathlib import Path


class VanillaAdapter:
    """Adapter for projects with no recognised build engine.

    Returned by :func:`~zenzic.core.adapters.get_adapter` when neither a
    ``mkdocs.yml`` nor explicit locales are detected.  Provides neutral,
    no-op behaviour so Zenzic operates as a plain Markdown linter without
    any i18n awareness.

    All methods are pure and perform no I/O.
    """

    def is_locale_dir(self, part: str) -> bool:  # noqa: ARG002
        """Always ``False`` — no locale directories without an engine config."""
        return False

    def resolve_asset(self, missing_abs: Path, docs_root: Path) -> Path | None:  # noqa: ARG002
        """Always ``None`` — no fallback logic without a locale tree."""
        return None

    def resolve_anchor(  # noqa: ARG002
        self,
        resolved_file: Path,
        anchor: str,
        anchors_cache: dict[Path, set[str]],
        docs_root: Path,
    ) -> bool:
        """Always ``False`` — no i18n anchor fallback without a locale tree."""
        return False

    def is_shadow_of_nav_page(self, rel: Path, nav_paths: frozenset[str]) -> bool:  # noqa: ARG002
        """Always ``False`` — no shadow pages without a nav."""
        return False

    def get_ignored_patterns(self) -> set[str]:
        """Empty set — no suffix-mode i18n patterns."""
        return set()

    def get_nav_paths(self) -> frozenset[str]:
        """Empty frozenset — no engine config means no declared nav."""
        return frozenset()

    def has_engine_config(self) -> bool:
        """``False`` — VanillaAdapter is active only when no engine was detected."""
        return False
