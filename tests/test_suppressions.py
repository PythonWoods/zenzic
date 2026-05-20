# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Strict suppression-parser contract tests (ADR-063).

Verifies that _is_suppressed accepts only the exact ``zenzic:ignore:``
directive — for both HTML (Markdown) and JSX (MDX) comment formats — and
rejects all syntactic deviations without exception.
"""

from __future__ import annotations

from zenzic.core.rules import _is_suppressed


# ---------------------------------------------------------------------------
# HTML / Markdown format  (<!-- zenzic:ignore: ZXXX -->)
# ---------------------------------------------------------------------------


class TestHtmlSuppressionStrictness:
    def test_positive_strict_match(self) -> None:
        line = "OldBrand was the codename. <!-- zenzic:ignore: Z601 - historical -->"
        assert _is_suppressed(line, "Z601") is True

    def test_negative_hyphen_fallacy(self) -> None:
        """zenzic-ignore (hyphen) must NOT be recognised as a suppression."""
        line = "OldBrand was the codename. <!-- zenzic-ignore: Z601 - historical -->"
        assert _is_suppressed(line, "Z601") is False

    def test_negative_missing_colon_after_ignore(self) -> None:
        """Omitting the colon after 'ignore' must NOT suppress."""
        line = "OldBrand was the codename. <!-- zenzic:ignore Z601 -->"
        assert _is_suppressed(line, "Z601") is False

    def test_negative_typo_in_keyword(self) -> None:
        """A typo in the directive keyword must NOT suppress."""
        line = "OldBrand was the codename. <!-- zenzic:ignor: Z601 -->"
        assert _is_suppressed(line, "Z601") is False


# ---------------------------------------------------------------------------
# JSX / MDX format  ({/* zenzic:ignore: ZXXX */})
# ---------------------------------------------------------------------------


class TestJsxSuppressionStrictness:
    def test_positive_strict_match(self) -> None:
        line = "OldBrand was the codename. {/* zenzic:ignore: Z601 - historical */}"
        assert _is_suppressed(line, "Z601") is True

    def test_negative_hyphen_fallacy(self) -> None:
        """zenzic-ignore (hyphen) inside JSX wrapper must NOT suppress."""
        line = "OldBrand was the codename. {/* zenzic-ignore: Z601 - historical */}"
        assert _is_suppressed(line, "Z601") is False

    def test_negative_wrong_comment_type(self) -> None:
        """Single-line JSX comment ({// ...}) must NOT suppress."""
        line = "OldBrand was the codename. {// zenzic:ignore: Z601 }"
        assert _is_suppressed(line, "Z601") is False

    def test_negative_malformed_closing(self) -> None:
        """Malformed closing (*} instead of */}) must NOT suppress."""
        line = "OldBrand was the codename. {/* zenzic:ignore: Z601 *}"
        assert _is_suppressed(line, "Z601") is False
