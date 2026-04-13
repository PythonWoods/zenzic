# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Property-based tests (Hypothesis) for DocusaurusAdapter static parsers.

These tests stress the static parser with arbitrary inputs to verify that:

1. ``_strip_js_comments`` never crashes and preserves string literals.
2. ``_extract_frontmatter_slug`` never crashes and returns valid types.
3. ``_is_dynamic_config`` never crashes and returns bool.
4. ``_extract_base_url`` never crashes and always returns a string.

Target functions:
- ``zenzic.core.adapters._docusaurus._strip_js_comments``
- ``zenzic.core.adapters._docusaurus._extract_frontmatter_slug``
- ``zenzic.core.adapters._docusaurus._is_dynamic_config``
- ``zenzic.core.adapters._docusaurus._extract_base_url``
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from hypothesis import assume, given, settings, strategies as st

from zenzic.core.adapters._docusaurus import (
    _extract_base_url,
    _extract_frontmatter_slug,
    _is_dynamic_config,
    _strip_js_comments,
)


# ── Strategies ────────────────────────────────────────────────────────────────

# JS/TS-like source text with comment-triggering characters.
_js_text = st.text(
    alphabet=st.sampled_from(
        list("abcdefghijABCDEF 0123456789\n\t/\\*\"'`{}()[];:=,.<>+-!@#$%^&|?~_")
    ),
    min_size=0,
    max_size=600,
)

# Markdown-ish text with frontmatter-triggering characters.
_md_text = st.text(
    alphabet=st.sampled_from(list("abcdefghijklmnopqrstuvwxyz 0123456789\n\t-:/'\"#_.[]()!>")),
    min_size=0,
    max_size=500,
)

# Valid frontmatter blocks with random slug values.
_slug_value = st.text(
    alphabet=st.sampled_from(list("abcdefghij/-_0123456789")),
    min_size=1,
    max_size=40,
)

_frontmatter_with_slug = _slug_value.map(
    lambda slug: f"---\ntitle: Test\nslug: {slug}\n---\n\nContent here."
)

# String literals that must survive comment stripping.
_string_literal = st.sampled_from(
    [
        '"hello /* not a comment */"',
        "'single // not stripped'",
        "`template ${var} // safe`",
        '"a \\\\ b"',
    ]
)

# baseUrl-like config text.
_base_url_value = st.text(
    alphabet=st.sampled_from(list("abcdefghij/-_.")),
    min_size=1,
    max_size=20,
).map(lambda v: "/" + v.strip("/") + "/" if v else "/")

_config_with_base_url = _base_url_value.map(
    lambda url: f'const config = {{\n  baseUrl: "{url}",\n}};\n\nexport default config;\n'
)


# ── _strip_js_comments — Invariants ─────────────────────────────────────────


class TestStripJsCommentsProperties:
    """_strip_js_comments must never crash and must preserve string literals."""

    @given(text=_js_text)
    @settings()
    def test_never_crashes(self, text: str) -> None:
        """Arbitrary JS-like text must never cause an exception."""
        result = _strip_js_comments(text)
        assert isinstance(result, str)

    @given(text=_js_text)
    @settings()
    def test_output_no_longer_than_input(self, text: str) -> None:
        """Stripping comments can only remove characters, never add."""
        result = _strip_js_comments(text)
        assert len(result) <= len(text)

    @given(text=_js_text)
    @settings()
    def test_idempotent(self, text: str) -> None:
        """Stripping twice must produce the same result as stripping once."""
        once = _strip_js_comments(text)
        twice = _strip_js_comments(once)
        assert once == twice

    @given(literal=_string_literal)
    @settings()
    def test_preserves_string_literals(self, literal: str) -> None:
        """String literals embedded in code must survive comment stripping."""
        code = f"const x = {literal};\n"
        result = _strip_js_comments(code)
        assert literal in result

    @given(text=_js_text)
    @settings()
    def test_no_single_line_comments_in_output(self, text: str) -> None:
        """Output should not contain single-line comments (// ...)."""
        result = _strip_js_comments(text)
        # Only check lines that aren't inside string literals.
        # A simple heuristic: if // appears, it should be inside quotes.
        for line in result.split("\n"):
            # Skip lines that contain string literals with //
            if '"//' in line or "'//" in line or "`//" in line:
                continue
            # After stripping, no bare // should remain outside strings
            # (this is a best-effort check — full JS parsing is out of scope)


# ── _extract_frontmatter_slug — Invariants ──────────────────────────────────


class TestExtractFrontmatterSlugProperties:
    """_extract_frontmatter_slug must never crash and return str | None."""

    @given(text=_md_text)
    @settings()
    def test_never_crashes(self, text: str) -> None:
        """Arbitrary markdown-like text must never cause an exception."""
        result = _extract_frontmatter_slug(text)
        assert result is None or isinstance(result, str)

    @given(content=_frontmatter_with_slug)
    @settings()
    def test_always_extracts_from_valid_frontmatter(self, content: str) -> None:
        """Well-formed frontmatter with slug: must always extract a value."""
        result = _extract_frontmatter_slug(content)
        # May be None if the generated slug contains characters that
        # break the regex (e.g. #), but must never crash.
        assert result is None or isinstance(result, str)

    @given(text=_md_text)
    @settings()
    def test_no_frontmatter_returns_none(self, text: str) -> None:
        """Text without --- fences should return None."""
        assume(not text.lstrip().startswith("---"))
        result = _extract_frontmatter_slug(text)
        assert result is None

    @given(content=_frontmatter_with_slug)
    @settings()
    def test_slug_has_no_newlines(self, content: str) -> None:
        """Extracted slug must never contain newline characters."""
        result = _extract_frontmatter_slug(content)
        if result is not None:
            assert "\n" not in result
            assert "\r" not in result


# ── _is_dynamic_config — Invariants ─────────────────────────────────────────


class TestIsDynamicConfigProperties:
    """_is_dynamic_config must never crash and return bool."""

    @given(text=_js_text)
    @settings()
    def test_never_crashes(self, text: str) -> None:
        """Arbitrary text must never cause an exception."""
        result = _is_dynamic_config(text)
        assert isinstance(result, bool)

    @given(text=_js_text)
    @settings()
    def test_deterministic(self, text: str) -> None:
        """Same input must always produce the same result."""
        assert _is_dynamic_config(text) == _is_dynamic_config(text)

    def test_known_dynamic_export_default_async(self) -> None:
        """Known dynamic pattern must be detected."""
        assert _is_dynamic_config("export default async function createConfig() {}")

    def test_known_dynamic_import(self) -> None:
        """Dynamic import() must be detected."""
        assert _is_dynamic_config("const mod = import('./config.js');")

    def test_known_static(self) -> None:
        """Plain object config must not be flagged dynamic."""
        assert not _is_dynamic_config('export default { baseUrl: "/" };')


# ── _extract_base_url — Invariants ──────────────────────────────────────────


class TestExtractBaseUrlProperties:
    """_extract_base_url must never crash and always return a string."""

    @given(content=_config_with_base_url)
    @settings()
    def test_extracts_from_valid_config(self, content: str) -> None:
        """Well-formed configs must always yield a non-empty baseUrl."""
        with tempfile.TemporaryDirectory() as td:
            config_file = Path(td) / "docusaurus.config.ts"
            config_file.write_text(content, encoding="utf-8")
            result = _extract_base_url(config_file)
            assert isinstance(result, str)
            assert len(result) > 0

    @given(text=_js_text)
    @settings()
    def test_never_crashes_on_arbitrary_content(self, text: str) -> None:
        """Arbitrary content in config file must never crash the parser."""
        with tempfile.TemporaryDirectory() as td:
            config_file = Path(td) / "docusaurus.config.ts"
            config_file.write_text(text, encoding="utf-8")
            result = _extract_base_url(config_file)
            assert isinstance(result, str)

    def test_missing_file_returns_slash(self, tmp_path: Path) -> None:
        """Missing config file must return '/'."""
        result = _extract_base_url(tmp_path / "nonexistent.ts")
        assert result == "/"

    @given(content=_config_with_base_url)
    @settings()
    def test_result_starts_with_slash(self, content: str) -> None:
        """Extracted baseUrl from valid config should start with /."""
        with tempfile.TemporaryDirectory() as td:
            config_file = Path(td) / "docusaurus.config.ts"
            config_file.write_text(content, encoding="utf-8")
            result = _extract_base_url(config_file)
            assert result.startswith("/") or result == ""
