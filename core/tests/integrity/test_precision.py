# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Precision Calibration (Direttiva CEO 055).

Two sensor calibration invariants:

  PREC-001  Frontmatter is invisible to the word counter.
            MDX files often open with a ``{/* SPDX … */}`` licence header
            *before* the ``---`` block.  When that happens the word counter
            must still strip the YAML block in its entirety and count only
            rendered prose.  A page with 50 frontmatter keys + 10 prose words
            must report exactly 10 words — not 10 + every YAML token.

  PREC-002  ``pathname:///`` links are portable.
            Docusaurus's static-asset escape hatch (the "Diplomatic Courier")
            must not trigger Z105 (ABSOLUTE_PATH).  The triple-slash is part
            of the URI scheme convention, not an absolute server-root path.
"""

from __future__ import annotations

from pathlib import Path

from zenzic.core.rules import ShortContentRule
from zenzic.models.config import ZenzicConfig


class TestFrontmatterInvisible:
    """CEO-055 / PREC-001: YAML frontmatter must be fully stripped before counting."""

    def test_frontmatter_is_invisible(self) -> None:
        """MDX SPDX header before frontmatter must not prevent frontmatter stripping.

        Root cause (D055): _FRONTMATTER_RE is anchored to \\A.  When an MDX
        comment ``{/* … */}`` precedes the ``---`` block, the ``{`` character
        stops ``\\s*`` from advancing, the regex fails, and all YAML key-value
        pairs are counted as prose words.

        Fix: strip MDX/HTML comments *before* running the frontmatter regex.
        """
        frontmatter_keys = "\n".join(f"key_{i}: value_number_{i}" for i in range(50))
        content = (
            "{/* SPDX-FileCopyrightText: 2026 PythonWoods */}\n---\n"
            + frontmatter_keys
            + "\n---\n\nThis page has exactly ten words of real prose content.\n"
        )
        config = ZenzicConfig(placeholder_max_words=50)
        rule = ShortContentRule(config.placeholder_max_words)
        findings = rule.check(Path("test.mdx"), content)
        assert len(findings) == 1, (
            f"Expected exactly one Z502 finding (10 prose words < 50 threshold) but got: {findings}"
        )
        finding = findings[0]
        assert finding.rule_id == "Z502"
        assert "10 words" in finding.message, (
            f"Word count in detail must be 10 (prose only), got: {finding.message!r}"
        )

    def test_plain_frontmatter_stripped(self) -> None:
        """Standard frontmatter without a preceding comment is also stripped."""
        content = "---\ntitle: My Page\ndescription: A long description with many words to verify exclusion.\n---\n\nOne two three.\n"
        config = ZenzicConfig(placeholder_max_words=50)
        rule = ShortContentRule(config.placeholder_max_words)
        findings = rule.check(Path("test.md"), content)
        assert len(findings) == 1
        assert findings[0].rule_id == "Z502"
        assert "3 words" in findings[0].message

    def test_html_comment_before_frontmatter_stripped(self) -> None:
        """HTML comment before frontmatter also must not block frontmatter stripping."""
        content = "<!-- SPDX-FileCopyrightText: 2026 PythonWoods -->\n---\ntitle: My Page\ndescription: Long description with lots and lots of words here.\n---\n\nHello world.\n"
        config = ZenzicConfig(placeholder_max_words=50)
        rule = ShortContentRule(config.placeholder_max_words)
        findings = rule.check(Path("test.md"), content)
        assert len(findings) == 1
        assert "2 words" in findings[0].message
