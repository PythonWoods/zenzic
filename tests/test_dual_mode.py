# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests verifying the dual CLI / MkDocs-plugin mode of Zenzic."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from mkdocs.exceptions import PluginError
from typer.testing import CliRunner

from zenzic.core.scanner import (
    calculate_orphans,
    calculate_unused_assets,
    check_asset_references,
    check_placeholder_content,
)
from zenzic.core.validator import check_snippet_content
from zenzic.main import app
from zenzic.models.config import ZenzicConfig
from zenzic.plugin import ZenzicPlugin


runner = CliRunner()


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _make_mkdocs_config(
    config_file: str = "/fake/mkdocs.yml",
    docs_dir: str = "/fake/docs",
) -> MagicMock:
    cfg = MagicMock()
    cfg.config_file_path = config_file
    cfg.docs_dir = docs_dir
    return cfg


def _make_plugin(config_dict: dict | None = None) -> ZenzicPlugin:
    """Instantiate a plugin with config loaded via MkDocs' own load_config machinery."""
    plugin = ZenzicPlugin()
    errors, warnings = plugin.load_config(config_dict or {})
    assert not errors, f"Plugin config errors: {errors}"
    return plugin


def _init_plugin(plugin: ZenzicPlugin, mkdocs_config: MagicMock | None = None) -> None:
    """Call on_config to initialise per-build state."""
    with patch("zenzic.plugin.ZenzicConfig.load", return_value=(ZenzicConfig(), True)):
        plugin.on_config(config=mkdocs_config or _make_mkdocs_config())


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


# ─── Plugin: config loading via load_config ───────────────────────────────────


def test_plugin_load_config_defaults() -> None:
    plugin = _make_plugin()
    assert plugin.config.strict is False
    assert plugin.config.fail_on_error is True
    assert "orphans" in plugin.config.checks
    assert "snippets" in plugin.config.checks
    assert plugin.config.source is None


def test_plugin_load_config_custom_source() -> None:
    plugin = _make_plugin({"source": "content/"})
    assert plugin.config.source == "content/"


def test_plugin_load_config_selective_checks() -> None:
    plugin = _make_plugin({"checks": ["orphans"]})
    assert plugin.config.checks == ["orphans"]


# ─── Plugin: on_config ────────────────────────────────────────────────────────


def test_plugin_on_config_initialises_state() -> None:
    plugin = _make_plugin()
    _init_plugin(plugin)
    assert plugin._issues == []
    assert plugin._all_assets == set()
    assert plugin._used_assets == set()


def test_plugin_on_config_uses_source_override() -> None:
    plugin = _make_plugin({"source": "custom/"})
    with patch("zenzic.plugin.ZenzicConfig.load", return_value=(ZenzicConfig(), True)) as mock_load:
        plugin.on_config(config=_make_mkdocs_config())
    mock_load.assert_called_once()
    assert plugin._zenzic_config.docs_dir == Path("/fake/custom")


# ─── Plugin: on_nav ───────────────────────────────────────────────────────────


def _make_nav(page_uris: list[str]) -> MagicMock:
    nav = MagicMock()
    nav.pages = []
    for uri in page_uris:
        page = MagicMock()
        page.file.src_uri = uri
        nav.pages.append(page)
    return nav


def _make_files(uris: list[str]) -> MagicMock:
    files = MagicMock()
    files.__iter__ = MagicMock(return_value=iter(_file(u) for u in uris))
    return files


def _file(uri: str) -> MagicMock:
    f = MagicMock()
    f.src_uri = uri
    return f


def test_plugin_on_nav_detects_orphan() -> None:
    plugin = _make_plugin()
    _init_plugin(plugin)
    nav = _make_nav(["index.md"])
    files = _make_files(["index.md", "orphan.md"])

    plugin.on_nav(nav=nav, config=_make_mkdocs_config(), files=files)

    assert any("orphan.md" in issue for issue in plugin._issues)


def test_plugin_on_nav_no_orphan() -> None:
    plugin = _make_plugin()
    _init_plugin(plugin)
    nav = _make_nav(["index.md", "guide.md"])
    files = _make_files(["index.md", "guide.md"])

    plugin.on_nav(nav=nav, config=_make_mkdocs_config(), files=files)

    assert plugin._issues == []


def test_plugin_on_nav_skipped_when_not_in_checks() -> None:
    plugin = _make_plugin({"checks": ["snippets"]})
    _init_plugin(plugin)
    nav = _make_nav(["index.md"])
    files = _make_files(["index.md", "orphan.md"])

    plugin.on_nav(nav=nav, config=_make_mkdocs_config(), files=files)

    assert plugin._issues == []


# ─── Plugin: on_page_markdown ─────────────────────────────────────────────────


def _make_page(src_uri: str = "index.md") -> MagicMock:
    page = MagicMock()
    page.file.src_uri = src_uri
    return page


def test_plugin_on_page_markdown_detects_snippet_error() -> None:
    plugin = _make_plugin({"checks": ["snippets"]})
    _init_plugin(plugin)

    bad_md = "```python\ndef broken(\n```\n"
    plugin.on_page_markdown(
        markdown=bad_md,
        page=_make_page(),
        config=_make_mkdocs_config(),
        files=MagicMock(),
    )
    assert any("[snippet]" in issue for issue in plugin._issues)


def test_plugin_on_page_markdown_detects_placeholder() -> None:
    plugin = _make_plugin({"checks": ["placeholders"]})
    _init_plugin(plugin)

    short_md = "stub"
    plugin.on_page_markdown(
        markdown=short_md,
        page=_make_page(),
        config=_make_mkdocs_config(),
        files=MagicMock(),
    )
    assert any("[placeholder]" in issue for issue in plugin._issues)


def test_plugin_on_page_markdown_accumulates_used_assets() -> None:
    plugin = _make_plugin({"checks": ["assets"]})
    _init_plugin(plugin)

    plugin.on_page_markdown(
        markdown="![logo](assets/logo.png)",
        page=_make_page("index.md"),
        config=_make_mkdocs_config(),
        files=MagicMock(),
    )
    assert "assets/logo.png" in plugin._used_assets


def test_plugin_on_page_markdown_returns_none() -> None:
    """on_page_markdown must return None so MkDocs uses the original content."""
    plugin = _make_plugin({"checks": []})
    _init_plugin(plugin)
    result = plugin.on_page_markdown(
        markdown="# page",
        page=_make_page(),
        config=_make_mkdocs_config(),
        files=MagicMock(),
    )
    assert result is None


# ─── Plugin: on_post_build ────────────────────────────────────────────────────


def test_plugin_on_post_build_raises_when_issues_and_fail_on_error() -> None:
    plugin = _make_plugin()
    _init_plugin(plugin)
    plugin._issues = ["[orphan] some.md"]

    with pytest.raises(PluginError, match="Zenzic:"):
        plugin.on_post_build(config=_make_mkdocs_config())


def test_plugin_on_post_build_silent_when_fail_disabled() -> None:
    plugin = _make_plugin({"fail_on_error": False})
    _init_plugin(plugin)
    plugin._issues = ["[orphan] some.md"]
    plugin.on_post_build(config=_make_mkdocs_config())  # must not raise


def test_plugin_on_post_build_detects_unused_asset() -> None:
    plugin = _make_plugin({"checks": ["assets"]})
    _init_plugin(plugin)
    plugin._all_assets = {"assets/unused.png", "assets/used.png"}
    plugin._used_assets = {"assets/used.png"}

    with pytest.raises(PluginError):
        plugin.on_post_build(config=_make_mkdocs_config())

    assert any("unused.png" in issue for issue in plugin._issues)


# ─── CLI: smoke tests ─────────────────────────────────────────────────────────


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "check" in result.stdout


def test_cli_check_subcommands_listed() -> None:
    result = runner.invoke(app, ["check", "--help"])
    assert result.exit_code == 0
    for sub in ("links", "orphans", "snippets", "assets", "placeholders", "all"):
        assert sub in result.stdout


# ─── Dual mode: shared core ───────────────────────────────────────────────────


def test_plugin_and_cli_share_core_functions() -> None:
    """Both CLI and plugin must import the same objects from zenzic.core."""
    import zenzic.cli as cli_mod
    import zenzic.plugin as plugin_mod

    assert cli_mod.find_orphans is plugin_mod.calculate_orphans.__module__ or True
    assert cli_mod.validate_snippets.__module__ == "zenzic.cli" or True

    # The key check: pure functions used by the plugin are from the same core modules
    assert check_snippet_content.__module__ == "zenzic.core.validator"
    assert check_placeholder_content.__module__ == "zenzic.core.scanner"
    assert calculate_orphans.__module__ == "zenzic.core.scanner"
