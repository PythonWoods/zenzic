# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for core check functions and CLI smoke tests.

The MkDocs plugin integration has been removed in v0.7.0. Zenzic is a
sovereign CLI. These tests verify that the underlying pure-Python core
functions are correct, and that the CLI exposes the expected sub-commands.
"""

from __future__ import annotations

from typer.testing import CliRunner

from zenzic.core.scanner import (
    calculate_orphans,
    calculate_unused_assets,
    check_asset_references,
    check_placeholder_content,
)
from zenzic.core.validator import check_snippet_content
from zenzic.main import app


runner = CliRunner()


# ─── Pure core: calculate_orphans ─────────────────────────────────────────────


def test_calculate_orphans_returns_diff() -> None:
    all_md = {"index.md", "guide.md", "orphan.md"}
    nav = {"index.md", "guide.md"}
    assert calculate_orphans(all_md, nav) == ["orphan.md"]


def test_calculate_orphans_empty_when_all_mapped() -> None:
    pages = {"index.md", "api.md"}
    assert calculate_orphans(pages, pages) == []


def test_calculate_orphans_sorted() -> None:
    result = calculate_orphans({"z.md", "a.md", "m.md"}, set())
    assert result == ["a.md", "m.md", "z.md"]


# ─── Pure core: check_placeholder_content ─────────────────────────────────────


def test_check_placeholder_short_content() -> None:
    findings = check_placeholder_content("too short", "page.md")
    assert any(f.issue == "short-content" for f in findings)


def test_check_placeholder_pattern_match() -> None:
    findings = check_placeholder_content(
        "# Title\n\nThis is a TODO section that needs more content.\n" * 5,
        "page.md",
    )
    assert any(f.issue == "placeholder-text" for f in findings)


def test_check_placeholder_clean_page() -> None:
    content = "# Complete Page\n\n" + "Real content here. " * 60
    assert check_placeholder_content(content, "page.md") == []


# ─── Pure core: check_snippet_content ─────────────────────────────────────────


def test_check_snippet_valid_python() -> None:
    md = "```python\nprint('hello')\n```\n"
    assert check_snippet_content(md, "page.md") == []


def test_check_snippet_invalid_python() -> None:
    md = "```python\ndef broken(\n```\n"
    errors = check_snippet_content(md, "page.md")
    assert errors
    assert "SyntaxError" in errors[0].message


def test_check_snippet_non_python_ignored() -> None:
    md = "```bash\nrm -rf /\n```\n"
    assert check_snippet_content(md, "page.md") == []


# ─── Pure core: check_asset_references ────────────────────────────────────────


def test_check_asset_references_markdown_image() -> None:
    refs = check_asset_references("![logo](assets/logo.png)", "")
    assert "assets/logo.png" in refs


def test_check_asset_references_relative_path() -> None:
    refs = check_asset_references("![img](../assets/logo.png)", "guide")
    assert "assets/logo.png" in refs


def test_check_asset_references_ignores_http() -> None:
    refs = check_asset_references("![img](https://example.com/logo.png)", "")
    assert not refs


def test_check_asset_references_ignores_escape() -> None:
    """Paths that escape docs root (../../) are not tracked."""
    refs = check_asset_references("![img](../../outside.png)", "")
    assert not refs


# ─── Pure core: calculate_unused_assets ───────────────────────────────────────


def test_calculate_unused_assets() -> None:
    all_a = {"assets/logo.png", "assets/unused.png"}
    used = {"assets/logo.png"}
    assert calculate_unused_assets(all_a, used) == ["assets/unused.png"]


def test_calculate_unused_assets_none_unused() -> None:
    assets = {"assets/logo.png"}
    assert calculate_unused_assets(assets, assets) == []


# ─── CLI smoke tests ──────────────────────────────────────────────────────────


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "check" in result.stdout


def test_cli_check_subcommands_listed() -> None:
    result = runner.invoke(app, ["check", "--help"])
    assert result.exit_code == 0
    for sub in ("links", "orphans", "snippets", "assets", "placeholders", "all"):
        assert sub in result.stdout
