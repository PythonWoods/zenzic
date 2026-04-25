# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Guardians — Precision Calibration (Direttiva CEO 055).

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

from _helpers import make_mgr

from zenzic.core.scanner import check_placeholder_content
from zenzic.core.validator import validate_links_structured
from zenzic.models.config import BuildContext, ZenzicConfig


# ── PREC-001: Frontmatter is invisible to the word counter ───────────────────


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
            "{/* SPDX-FileCopyrightText: 2026 PythonWoods */}\n"
            "---\n" + frontmatter_keys + "\n"
            "---\n\n"
            "This page has exactly ten words of real prose content.\n"
        )
        config = ZenzicConfig(placeholder_max_words=50)
        findings = check_placeholder_content(content, "test.mdx", config)
        assert len(findings) == 1, (
            f"Expected exactly one Z502 finding (10 prose words < 50 threshold) but got: {findings}"
        )
        finding = findings[0]
        assert finding.issue == "short-content"
        assert "10 words" in finding.detail, (
            f"Word count in detail must be 10 (prose only), got: {finding.detail!r}"
        )

    def test_plain_frontmatter_stripped(self) -> None:
        """Standard frontmatter without a preceding comment is also stripped."""
        content = (
            "---\n"
            "title: My Page\n"
            "description: A long description with many words to verify exclusion.\n"
            "---\n\n"
            "One two three.\n"
        )
        config = ZenzicConfig(placeholder_max_words=50)
        findings = check_placeholder_content(content, "test.md", config)
        assert len(findings) == 1
        assert findings[0].issue == "short-content"
        assert "3 words" in findings[0].detail

    def test_html_comment_before_frontmatter_stripped(self) -> None:
        """HTML comment before frontmatter also must not block frontmatter stripping."""
        content = (
            "<!-- SPDX-FileCopyrightText: 2026 PythonWoods -->\n"
            "---\n"
            "title: My Page\n"
            "description: Long description with lots and lots of words here.\n"
            "---\n\n"
            "Hello world.\n"
        )
        config = ZenzicConfig(placeholder_max_words=50)
        findings = check_placeholder_content(content, "test.md", config)
        assert len(findings) == 1
        assert "2 words" in findings[0].detail


# ── PREC-002: pathname:/// is portable ───────────────────────────────────────


class TestPathnameIsPortable:
    """CEO-055 / PREC-002: pathname:/// must not trigger Z105 (ABSOLUTE_PATH)."""

    def test_pathname_is_portable(self, tmp_path: Path) -> None:
        """pathname:/// in Docusaurus mode generates no ABSOLUTE_PATH finding.

        Root cause (D055): ``urlsplit("pathname:///assets/file.html")`` yields
        ``scheme="pathname"``, ``path="/assets/file.html"``.  The Z105 gate
        previously checked only ``parsed.path.startswith("/")``, so the
        leading "/" triggered an ABSOLUTE_PATH error even though the link
        carries an explicit URI scheme.

        Fix: in Docusaurus mode, the ``pathname:///`` scheme is the
        "Diplomatic Courier" escape hatch for static assets.  The gate is
        now conditioned on ``not (parsed.scheme == "pathname" and engine ==
        "docusaurus")``.  In other engines (e.g. MkDocs), pathname:/// is
        unrecognized and still triggers Z105.
        """
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text(
            "See the [brand system](pathname:///assets/brand/zenzic-brand-system.html)\n",
            encoding="utf-8",
        )
        config = ZenzicConfig(build_context=BuildContext(engine="docusaurus"))
        mgr = make_mgr(config, repo_root=tmp_path)
        errors = validate_links_structured(docs, mgr, repo_root=tmp_path, config=config)
        error_types = {e.error_type for e in errors}
        assert "ABSOLUTE_PATH" not in error_types, (
            "pathname:/// must not trigger Z105 — it carries an explicit URI scheme"
        )

    def test_bare_absolute_path_still_fires(self, tmp_path: Path) -> None:
        """Sanity check: a bare /path link (no scheme) still triggers Z105."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text(
            "![logo](/assets/logo.png)\n",
            encoding="utf-8",
        )
        config = ZenzicConfig(build_context=BuildContext(engine="docusaurus"))
        mgr = make_mgr(config, repo_root=tmp_path)
        errors = validate_links_structured(docs, mgr, repo_root=tmp_path, config=config)
        error_types = {e.error_type for e in errors}
        assert "ABSOLUTE_PATH" in error_types, (
            "A bare /path link (no scheme) must still trigger Z105"
        )
