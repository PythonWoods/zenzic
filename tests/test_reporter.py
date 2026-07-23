# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for src/zenzic/core/reporter.py — snippet reader and string helpers."""

from __future__ import annotations

from pathlib import Path

from rich.text import Text

from zenzic.core.reporter import _read_snippet, _render_snippet, _strip_prefix


# ─── _read_snippet ────────────────────────────────────────────────────────────


def test_read_snippet_returns_none_for_missing_file(tmp_path: Path) -> None:
    """OSError path → None."""
    result = _read_snippet(tmp_path / "nonexistent.md", line_no=1)
    assert result is None


def test_read_snippet_returns_none_for_empty_file(tmp_path: Path) -> None:
    """Empty file → all_lines is [] → None.
    Kills 'not all_lines and line_no < 1' mutant: even with line_no=1 this returns None."""
    p = tmp_path / "empty.md"
    p.write_text("", encoding="utf-8")
    result = _read_snippet(p, line_no=1)
    assert result is None


def test_read_snippet_returns_none_for_line_no_zero(tmp_path: Path) -> None:
    """line_no=0 → None.
    Kills 'not all_lines and line_no < 1' mutant: file not empty but line_no invalid."""
    p = tmp_path / "file.md"
    p.write_text("line one\nline two\n", encoding="utf-8")
    result = _read_snippet(p, line_no=0)
    assert result is None


def test_read_snippet_returns_none_for_negative_line_no(tmp_path: Path) -> None:
    """line_no=-1 → None."""
    p = tmp_path / "file.md"
    p.write_text("line one\n", encoding="utf-8")
    result = _read_snippet(p, line_no=-1)
    assert result is None


def test_read_snippet_basic_line(tmp_path: Path) -> None:
    """Returns correct lines and start line number."""
    p = tmp_path / "file.md"
    content = "\n".join(f"line {i}" for i in range(1, 11))
    p.write_text(content, encoding="utf-8")
    result = _read_snippet(p, line_no=5)
    assert result is not None
    lines, start = result
    # Context = 2 lines; line 5 → start at line 3, end at line 7 (0-indexed: 2..6)
    assert start == 3
    assert len(lines) == 5
    assert "line 5" in lines[2]  # middle is the target line


def test_read_snippet_clamps_at_file_start(tmp_path: Path) -> None:
    """line_no=1 with context=2 → start is 0-indexed 0, start_line=1."""
    p = tmp_path / "file.md"
    p.write_text("first\nsecond\nthird\n", encoding="utf-8")
    result = _read_snippet(p, line_no=1)
    assert result is not None
    lines, start = result
    assert start == 1
    assert "first" in lines[0]


def test_read_snippet_clamps_at_file_end(tmp_path: Path) -> None:
    """line_no at last line → end is clamped to len(all_lines)."""
    p = tmp_path / "file.md"
    content = "a\nb\nc\n"
    p.write_text(content, encoding="utf-8")
    result = _read_snippet(p, line_no=3)
    assert result is not None
    lines, start = result
    assert "c" in lines[-1]


def test_read_snippet_returns_tuple_structure(tmp_path: Path) -> None:
    """Return value is (list[str], int)."""
    p = tmp_path / "file.md"
    p.write_text("only line\n", encoding="utf-8")
    result = _read_snippet(p, line_no=1)
    assert result is not None
    lines, start = result
    assert isinstance(lines, list)
    assert isinstance(start, int)
    assert all(isinstance(ln, str) for ln in lines)


# ─── _strip_prefix ────────────────────────────────────────────────────────────


def test_strip_prefix_removes_matching_prefix() -> None:
    """Standard case: 'file.md:5: message' → 'message'."""
    result = _strip_prefix("file.md", 5, "file.md:5: actual message")
    assert result == "actual message"


def test_strip_prefix_no_match_returns_original() -> None:
    """Non-matching prefix → message unchanged."""
    result = _strip_prefix("file.md", 5, "something else entirely")
    assert result == "something else entirely"


def test_strip_prefix_line_no_zero_skips(self=None) -> None:
    """line_no=0 means file-level — no prefix stripped."""
    result = _strip_prefix("file.md", 0, "file.md:0: message")
    # line_no=0 → condition 'if line_no > 0' is False → message returned as-is
    assert result == "file.md:0: message"


def test_strip_prefix_partial_match_not_stripped() -> None:
    """Prefix must match exactly including the trailing space."""
    result = _strip_prefix("file.md", 5, "file.md:5:no-space-after-colon")
    assert result == "file.md:5:no-space-after-colon"


# ─── _render_snippet — caret alignment ───────────────────────────────────────


def test_render_snippet_long_line_truncated(tmp_path: Path) -> None:
    """Very long source lines must be truncated to prevent terminal wrap.

    Regression (D048 Bug 3): carets were rendered based on the original string
    length, ignoring how ``rich`` wraps long lines visually.  A caret at col 80
    on a 200-char line appeared on the wrong visual row after wrapping.

    Fix: source line is truncated to (terminal_width - gutter_overhead) chars
    and the caret is only rendered when col_start falls within that visible range.
    """
    long_line = "x" * 200  # well beyond any terminal width
    p = tmp_path / "file.md"
    p.write_text(long_line + "\n", encoding="utf-8")

    result = _render_snippet(p, line_no=1, col_start=0, match_text="x" * 5)
    assert result, "Should produce at least one Text object"

    # Find the error row (the Text object that contains "❱").
    error_texts = [t for t in result if isinstance(t, Text) and "❱" in t.plain]
    assert error_texts, "Should have an error row with ❱"

    # The plain content of the error row must be shorter than the raw 200-char line,
    # proving the source was truncated (prefix "    1  ❱  " + truncated source).
    error_plain = error_texts[0].plain
    assert len(error_plain) < 200, (
        f"Error row plain text is {len(error_plain)} chars — "
        "long source line was not truncated, carets will misalign after terminal wrap"
    )
    # The truncation marker must be present.
    assert error_plain.endswith("…"), (
        f"Expected truncation ellipsis '…' at end of error row, got: {error_plain[-5:]!r}"
    )


def test_render_snippet_caret_suppressed_when_beyond_visible(tmp_path: Path) -> None:
    """Carets must not render when col_start falls in the truncated portion of the line.

    If the match is beyond the visible truncation point, rendering carets would
    point at an empty space (or the ``…`` ellipsis), which is worse than no caret.
    """
    long_line = "a" * 200
    p = tmp_path / "file.md"
    p.write_text(long_line + "\n", encoding="utf-8")

    # col_start=190 — deep in the truncated portion for any sane terminal width.
    result = _render_snippet(p, line_no=1, col_start=190, match_text="aaa")

    assert result, "Should produce at least one Text object (the source row)"
    # None of the returned Text objects should contain "^" (the caret character).
    caret_texts = [t for t in result if isinstance(t, Text) and "^" in t.plain]
    assert not caret_texts, (
        "Carets must not appear when col_start is beyond the truncated visible region"
    )
