# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Integration tests for v0.5.0a1 Integration Finale sprint.

Covers:
- zenzic plugins list (PluginRuleInfo, list_plugin_rules)
- Performance telemetry (scan_docs_references verbose=True)
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from zenzic.core.rules import PluginRuleInfo, list_plugin_rules
from zenzic.core.scanner import ADAPTIVE_PARALLEL_THRESHOLD, scan_docs_references
from zenzic.models.config import ZenzicConfig


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _make_docs(tmp_path: Path, n_files: int = 3) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir()
    for i in range(n_files):
        (docs / f"page_{i:03d}.md").write_text(f"# Page {i}\n\nContent {i}.\n")
    return tmp_path


# ─── list_plugin_rules ────────────────────────────────────────────────────────


def test_list_plugin_rules_returns_list() -> None:
    """list_plugin_rules() returns a list (possibly empty if entry-points not installed)."""
    result = list_plugin_rules()
    assert isinstance(result, list)


def test_list_plugin_rules_sorted_by_source() -> None:
    """Results are sorted by entry-point source name."""
    result = list_plugin_rules()
    sources = [r.source for r in result]
    assert sources == sorted(sources)


def test_list_plugin_rules_contains_core_broken_links() -> None:
    """The built-in broken-links rule is present when the package is installed."""
    result = list_plugin_rules()
    sources = {r.source for r in result}
    # Core package registers 'broken-links' via entry-points
    assert "broken-links" in sources


def test_list_plugin_rules_broken_links_has_correct_id() -> None:
    """broken-links entry-point exposes rule_id 'Z001'."""
    result = list_plugin_rules()
    by_source = {r.source: r for r in result}
    assert "broken-links" in by_source
    assert by_source["broken-links"].rule_id == "Z001"


def test_list_plugin_rules_broken_links_origin_is_zenzic() -> None:
    """broken-links is registered by the 'zenzic' distribution."""
    result = list_plugin_rules()
    by_source = {r.source: r for r in result}
    assert by_source["broken-links"].origin == "zenzic"


def test_plugin_rule_info_fields() -> None:
    """PluginRuleInfo is a plain dataclass with the expected fields."""
    info = PluginRuleInfo(
        rule_id="TEST",
        class_name="my_pkg.rules.TestRule",
        source="test-rule",
        origin="my-pkg",
    )
    assert info.rule_id == "TEST"
    assert info.class_name == "my_pkg.rules.TestRule"
    assert info.source == "test-rule"
    assert info.origin == "my-pkg"


def test_list_plugin_rules_skips_unloadable_entry_point() -> None:
    """An entry-point that fails to load is silently skipped."""
    from importlib.metadata import EntryPoint

    bad_ep = EntryPoint(
        name="bad", value="nonexistent.module:NonExistentClass", group="zenzic.rules"
    )

    with patch("importlib.metadata.entry_points", return_value=[bad_ep]):
        result = list_plugin_rules()
    # Bad plugin is skipped; built-in core fallback is still present.
    assert all(info.source != "bad" for info in result)
    assert any(info.source == "broken-links" for info in result)


# ─── CLI: zenzic plugins list ────────────────────────────────────────────────


def test_cli_plugins_list_command_runs() -> None:
    """zenzic plugins list exits 0 and prints output."""
    from typer.testing import CliRunner

    from zenzic.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["plugins", "list"])
    assert result.exit_code == 0


def test_cli_plugins_list_shows_broken_links() -> None:
    """plugins list output mentions the broken-links core rule."""
    from typer.testing import CliRunner

    from zenzic.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["plugins", "list"])
    assert "broken-links" in result.output
    assert "Z001" in result.output


def test_cli_plugins_list_empty_when_no_rules(monkeypatch: pytest.MonkeyPatch) -> None:
    """When no rules are registered, prints an informational message without crashing."""
    from typer.testing import CliRunner

    from zenzic.main import app

    monkeypatch.setattr("zenzic.core.rules.list_plugin_rules", lambda: [])

    runner = CliRunner()
    result = runner.invoke(app, ["plugins", "list"])
    assert result.exit_code == 0
    assert "No rules found" in result.output


# ─── Telemetry ────────────────────────────────────────────────────────────────


def test_telemetry_sequential_writes_to_stderr(tmp_path: Path) -> None:
    """verbose=True emits a telemetry line to stderr for sequential scans."""
    repo = _make_docs(tmp_path, n_files=2)
    config = ZenzicConfig()

    captured = StringIO()
    with patch("sys.stderr", captured):
        scan_docs_references(repo, config, verbose=True)

    output = captured.getvalue()
    assert "[zenzic]" in output
    assert "Sequential" in output
    assert "Files: 2" in output
    assert "Execution time:" in output


def test_telemetry_disabled_by_default(tmp_path: Path) -> None:
    """verbose=False (default) produces no stderr telemetry line."""
    repo = _make_docs(tmp_path, n_files=2)
    config = ZenzicConfig()

    captured = StringIO()
    with patch("sys.stderr", captured):
        scan_docs_references(repo, config)

    assert "[zenzic]" not in captured.getvalue()


def test_telemetry_parallel_shows_workers(tmp_path: Path) -> None:
    """verbose=True in parallel mode mentions workers and speedup."""
    # Create enough files to trigger parallel mode
    repo = _make_docs(tmp_path, n_files=ADAPTIVE_PARALLEL_THRESHOLD)
    config = ZenzicConfig()

    captured = StringIO()
    with patch("sys.stderr", captured):
        scan_docs_references(repo, config, workers=2, verbose=True)

    output = captured.getvalue()
    assert "[zenzic]" in output
    # Either parallel triggered (if files >= threshold) or sequential fallback —
    # either way telemetry must be emitted.
    assert "Execution time:" in output


def test_telemetry_sequential_no_speedup_line(tmp_path: Path) -> None:
    """Sequential telemetry line does not contain a speedup estimate."""
    repo = _make_docs(tmp_path, n_files=2)
    config = ZenzicConfig()

    captured = StringIO()
    with patch("sys.stderr", captured):
        scan_docs_references(repo, config, verbose=True)

    assert "speedup" not in captured.getvalue().lower()
