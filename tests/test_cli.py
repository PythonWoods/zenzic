# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for Zenzic CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from zenzic.core.scanner import PlaceholderFinding
from zenzic.core.validator import LinkError, SnippetError
from zenzic.main import app, cli_main
from zenzic.models.config import ZenzicConfig


runner = CliRunner()

_ROOT = Path("/fake/repo")
_CFG = ZenzicConfig()


# ---------------------------------------------------------------------------
# main entry point
# ---------------------------------------------------------------------------


def test_cli_main_calls_app() -> None:
    with patch("zenzic.main.app") as mock_app:
        cli_main()
        mock_app.assert_called_once()


# ---------------------------------------------------------------------------
# help
# ---------------------------------------------------------------------------


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Engineering-grade documentation linter" in result.stdout


# ---------------------------------------------------------------------------
# check links
# ---------------------------------------------------------------------------


@patch("zenzic.cli.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli.ZenzicConfig.load", return_value=(_CFG, False))
@patch("zenzic.cli.validate_links_structured", return_value=[])
def test_check_links_ok(_links, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "links"])
    assert result.exit_code == 0
    assert "OK" in result.stdout


@patch("zenzic.cli.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli.ZenzicConfig.load", return_value=(_CFG, False))
@patch(
    "zenzic.cli.validate_links_structured",
    return_value=[
        LinkError(
            file_path=_ROOT / "docs" / "index.md",
            line_no=1,
            message="index.md:1: broken link 'foo.md' (is not found)",
            source_line="[foo](foo.md)",
            error_type="FILE_NOT_FOUND",
        )
    ],
)
def test_check_links_with_errors(_links, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "links"])
    assert result.exit_code == 1
    assert "BROKEN LINKS" in result.stdout


@patch("zenzic.cli.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli.ZenzicConfig.load", return_value=(_CFG, False))
@patch("zenzic.cli.validate_links_structured", return_value=[])
def test_check_links_strict_passes_flag(mock_links, _cfg, _root) -> None:
    runner.invoke(app, ["check", "links", "--strict"])
    mock_links.assert_called_once_with(_ROOT, strict=True)


# ---------------------------------------------------------------------------
# check orphans
# ---------------------------------------------------------------------------


def test_cli_check_orphans_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "zenzic.toml").touch()  # engine-neutral root marker
    monkeypatch.chdir(repo)
    result = runner.invoke(app, ["check", "orphans"])
    assert result.exit_code == 0
    assert "OK: no orphan pages found." in result.stdout


@patch("zenzic.cli.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli.ZenzicConfig.load", return_value=(_CFG, True))
@patch("zenzic.cli.find_orphans", return_value=[Path("orphan.md")])
def test_check_orphans_with_orphans(_orphans, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "orphans"])
    assert result.exit_code == 1
    assert "ORPHANS" in result.stdout


# ---------------------------------------------------------------------------
# check snippets
# ---------------------------------------------------------------------------


@patch("zenzic.cli.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli.ZenzicConfig.load", return_value=(_CFG, True))
@patch("zenzic.cli.validate_snippets", return_value=[])
def test_check_snippets_ok(_snip, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "snippets"])
    assert result.exit_code == 0
    assert "OK" in result.stdout


@patch("zenzic.cli.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli.ZenzicConfig.load", return_value=(_CFG, True))
@patch(
    "zenzic.cli.validate_snippets",
    return_value=[
        SnippetError(
            file_path=Path("api.md"),
            line_no=5,
            message="SyntaxError in Python snippet — invalid syntax",
        )
    ],
)
def test_check_snippets_with_errors(_snip, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "snippets"])
    assert result.exit_code == 1
    assert "INVALID SNIPPETS" in result.stdout


# ---------------------------------------------------------------------------
# check assets
# ---------------------------------------------------------------------------


@patch("zenzic.cli.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli.ZenzicConfig.load", return_value=(_CFG, True))
@patch("zenzic.cli.find_unused_assets", return_value=[])
def test_check_assets_ok(_assets, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "assets"])
    assert result.exit_code == 0
    assert "OK" in result.stdout


@patch("zenzic.cli.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli.ZenzicConfig.load", return_value=(_CFG, True))
@patch("zenzic.cli.find_unused_assets", return_value=[Path("assets/unused.png")])
def test_check_assets_with_unused(_assets, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "assets"])
    assert result.exit_code == 1
    assert "UNUSED ASSETS" in result.stdout


# ---------------------------------------------------------------------------
# check placeholders
# ---------------------------------------------------------------------------


@patch("zenzic.cli.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli.ZenzicConfig.load", return_value=(_CFG, True))
@patch("zenzic.cli.find_placeholders", return_value=[])
def test_check_placeholders_ok(_ph, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "placeholders"])
    assert result.exit_code == 0
    assert "OK" in result.stdout


@patch("zenzic.cli.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli.ZenzicConfig.load", return_value=(_CFG, True))
@patch(
    "zenzic.cli.find_placeholders",
    return_value=[
        PlaceholderFinding(
            file_path=Path("stub.md"), line_no=1, issue="short-content", detail="5 words"
        )
    ],
)
def test_check_placeholders_with_findings(_ph, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "placeholders"])
    assert result.exit_code == 1
    assert "PLACEHOLDERS" in result.stdout


# ---------------------------------------------------------------------------
# check all — JSON
# ---------------------------------------------------------------------------


def test_cli_check_all_json_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "zenzic.toml").touch()  # engine-neutral root marker
    (repo / "docs").mkdir()
    monkeypatch.chdir(repo)
    result = runner.invoke(app, ["check", "all", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert set(data) == {
        "links",
        "orphans",
        "snippets",
        "placeholders",
        "unused_assets",
        "nav_contract",
        "references",
    }


@patch("zenzic.cli.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli.ZenzicConfig.load", return_value=(_CFG, True))
@patch("zenzic.cli.validate_links", return_value=["index.md: broken link"])
@patch("zenzic.cli.find_orphans", return_value=[])
@patch("zenzic.cli.validate_snippets", return_value=[])
@patch("zenzic.cli.find_placeholders", return_value=[])
@patch("zenzic.cli.find_unused_assets", return_value=[])
@patch("zenzic.cli.check_nav_contract", return_value=[])
@patch("zenzic.cli.scan_docs_references_with_links", return_value=([], []))
def test_check_all_json_with_errors(
    _refs, _nav, _assets, _ph, _snip, _orphans, _links, _cfg, _root
) -> None:
    result = runner.invoke(app, ["check", "all", "--format", "json"])
    assert result.exit_code == 1
    data = json.loads(result.stdout)
    assert len(data["links"]) == 1


# ---------------------------------------------------------------------------
# check all — text mode
# ---------------------------------------------------------------------------


@patch("zenzic.cli.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli.ZenzicConfig.load", return_value=(_CFG, True))
@patch("zenzic.cli.validate_links", return_value=[])
@patch("zenzic.cli.find_orphans", return_value=[])
@patch("zenzic.cli.validate_snippets", return_value=[])
@patch("zenzic.cli.find_placeholders", return_value=[])
@patch("zenzic.cli.find_unused_assets", return_value=[])
@patch("zenzic.cli.check_nav_contract", return_value=[])
@patch("zenzic.cli.scan_docs_references_with_links", return_value=([], []))
def test_check_all_text_ok(_refs, _nav, _assets, _ph, _snip, _orphans, _links, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "all"])
    assert result.exit_code == 0
    assert "SUCCESS" in result.stdout


@patch("zenzic.cli.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli.ZenzicConfig.load", return_value=(_CFG, True))
@patch("zenzic.cli.validate_links", return_value=["index.md: broken link"])
@patch("zenzic.cli.find_orphans", return_value=[Path("orphan.md")])
@patch(
    "zenzic.cli.validate_snippets",
    return_value=[SnippetError(file_path=Path("api.md"), line_no=5, message="SyntaxError")],
)
@patch(
    "zenzic.cli.find_placeholders",
    return_value=[
        PlaceholderFinding(file_path=Path("stub.md"), line_no=1, issue="short-content", detail="x")
    ],
)
@patch("zenzic.cli.find_unused_assets", return_value=[Path("assets/unused.png")])
@patch("zenzic.cli.check_nav_contract", return_value=[])
@patch("zenzic.cli.scan_docs_references_with_links", return_value=([], []))
def test_check_all_text_with_all_errors(
    _refs, _nav, _assets, _ph, _snip, _orphans, _links, _cfg, _root
) -> None:
    result = runner.invoke(app, ["check", "all"])
    assert result.exit_code == 1
    assert "FAILED" in result.stdout
    assert "BROKEN LINKS" in result.stdout
    assert "ORPHANS" in result.stdout
    assert "INVALID SNIPPETS" in result.stdout
    assert "PLACEHOLDERS" in result.stdout
    assert "UNUSED ASSETS" in result.stdout


# ---------------------------------------------------------------------------
# check references — rule_findings surfaced in CLI output
# ---------------------------------------------------------------------------


@patch("zenzic.cli.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli.ZenzicConfig.load", return_value=(_CFG, True))
@patch(
    "zenzic.cli.scan_docs_references_with_links",
    return_value=([], []),
)
def test_check_references_ok(_scan, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "references"])
    assert result.exit_code == 0
    assert "OK" in result.stdout


@patch("zenzic.cli.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli.ZenzicConfig.load", return_value=(_CFG, True))
@patch("zenzic.cli.scan_docs_references_with_links")
def test_check_references_rule_findings_surfaced(mock_scan, _cfg, _root) -> None:
    """rule_findings on IntegrityReport must appear in check references output."""
    from zenzic.core.rules import RuleFinding
    from zenzic.models.references import IntegrityReport

    rf = RuleFinding(
        file_path=Path("docs/guide.md"),
        line_no=12,
        rule_id="ZZ-NOCLICKHERE",
        message="Avoid generic link text.",
        severity="error",
    )
    report = IntegrityReport(file_path=Path("docs/guide.md"), score=100.0)
    report.rule_findings = [rf]
    mock_scan.return_value = ([report], [])

    result = runner.invoke(app, ["check", "references"])
    assert result.exit_code == 1
    assert "ZZ-NOCLICKHERE" in result.stdout
    assert "REFERENCE ERRORS" in result.stdout
