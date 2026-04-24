# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for Zenzic CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import ANY, patch

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
    assert "Engine-agnostic linter" in result.stdout


# ---------------------------------------------------------------------------
# check links
# ---------------------------------------------------------------------------


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, False))
@patch("zenzic.cli._check.validate_links_structured", return_value=[])
def test_check_links_ok(_links, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "links"])
    assert result.exit_code == 0
    assert "ZENZIC SENTINEL" in result.stdout
    assert "No broken links found." in result.stdout


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, False))
@patch(
    "zenzic.cli._check.validate_links_structured",
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
    assert "ZENZIC SENTINEL" in result.stdout
    assert "FILE_NOT_FOUND" in result.stdout or "error" in result.stdout.lower()


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, False))
@patch("zenzic.cli._check.validate_links_structured", return_value=[])
def test_check_links_strict_passes_flag(mock_links, _cfg, _root) -> None:
    runner.invoke(app, ["check", "links", "--strict"])
    mock_links.assert_called_once_with(
        _ROOT / "docs",
        ANY,
        repo_root=_ROOT,
        config=_CFG,
        strict=True,
        locale_roots=None,
    )


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, False))
@patch(
    "zenzic.cli._check.validate_links_structured",
    return_value=[
        LinkError(
            file_path=_ROOT / "docs" / "index.md",
            line_no=2,
            message="index.md:2: '../../../../etc/passwd' resolves outside the docs directory",
            source_line="[escape](../../../../etc/passwd)",
            error_type="PATH_TRAVERSAL_SUSPICIOUS",
        )
    ],
)
def test_check_links_system_path_traversal_exits_3(_links, _cfg, _root) -> None:
    """check links exits with code 3 when a system-path traversal is found."""
    result = runner.invoke(app, ["check", "links"])
    assert result.exit_code == 3


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, False))
@patch(
    "zenzic.cli._check.validate_links_structured",
    return_value=[
        LinkError(
            file_path=_ROOT / "docs" / "index.md",
            line_no=2,
            message="index.md:2: '../../outside.md' resolves outside the docs directory",
            source_line="[escape](../../outside.md)",
            error_type="PATH_TRAVERSAL",
        )
    ],
)
def test_check_links_boundary_traversal_exits_1(_links, _cfg, _root) -> None:
    """check links exits with code 1 for a non-system path traversal (no regression)."""
    result = runner.invoke(app, ["check", "links"])
    assert result.exit_code == 1


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
    assert "ZENZIC SENTINEL" in result.stdout
    assert "No orphan pages found." in result.stdout


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, True))
@patch("zenzic.cli._check.find_orphans", return_value=[Path("orphan.md")])
def test_check_orphans_with_orphans(_orphans, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "orphans"])
    assert result.exit_code == 1
    assert "ZENZIC SENTINEL" in result.stdout
    assert "Z402" in result.stdout


# ---------------------------------------------------------------------------
# check snippets
# ---------------------------------------------------------------------------


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, True))
@patch("zenzic.cli._check.validate_snippets", return_value=[])
def test_check_snippets_ok(_snip, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "snippets"])
    assert result.exit_code == 0
    assert "ZENZIC SENTINEL" in result.stdout
    assert "All code snippets are syntactically valid." in result.stdout


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, True))
@patch(
    "zenzic.cli._check.validate_snippets",
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
    assert "ZENZIC SENTINEL" in result.stdout
    assert "Z503" in result.stdout


# ---------------------------------------------------------------------------
# check assets
# ---------------------------------------------------------------------------


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, True))
@patch("zenzic.cli._check.find_unused_assets", return_value=[])
def test_check_assets_ok(_assets, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "assets"])
    assert result.exit_code == 0
    assert "ZENZIC SENTINEL" in result.stdout
    assert "No unused assets found." in result.stdout


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, True))
@patch("zenzic.cli._check.find_unused_assets", return_value=[Path("assets/unused.png")])
def test_check_assets_with_unused(_assets, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "assets"])
    assert result.exit_code == 1
    assert "ZENZIC SENTINEL" in result.stdout
    assert "Z903" in result.stdout


# ---------------------------------------------------------------------------
# check placeholders
# ---------------------------------------------------------------------------


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, True))
@patch("zenzic.cli._check.find_placeholders", return_value=[])
def test_check_placeholders_ok(_ph, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "placeholders"])
    assert result.exit_code == 0
    assert "ZENZIC SENTINEL" in result.stdout
    assert "No placeholder stubs found." in result.stdout


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, True))
@patch(
    "zenzic.cli._check.find_placeholders",
    return_value=[
        PlaceholderFinding(
            file_path=Path("stub.md"), line_no=1, issue="short-content", detail="5 words"
        )
    ],
)
def test_check_placeholders_with_findings(_ph, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "placeholders"])
    assert result.exit_code == 1
    assert "ZENZIC SENTINEL" in result.stdout
    assert "Z502" in result.stdout


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


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, True))
@patch(
    "zenzic.cli._check.validate_links_structured",
    return_value=[
        LinkError(
            file_path=_ROOT / "docs" / "index.md",
            line_no=1,
            message="index.md:1: broken link",
        )
    ],
)
@patch("zenzic.cli._check.find_orphans", return_value=[])
@patch("zenzic.cli._check.validate_snippets", return_value=[])
@patch("zenzic.cli._check.find_placeholders", return_value=[])
@patch("zenzic.cli._check.find_unused_assets", return_value=[])
@patch("zenzic.cli._check.check_nav_contract", return_value=[])
@patch("zenzic.cli._check.scan_docs_references", return_value=([], []))
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


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, True))
@patch("zenzic.cli._check.validate_links_structured", return_value=[])
@patch("zenzic.cli._check.find_orphans", return_value=[])
@patch("zenzic.cli._check.validate_snippets", return_value=[])
@patch("zenzic.cli._check.find_placeholders", return_value=[])
@patch("zenzic.cli._check.find_unused_assets", return_value=[])
@patch("zenzic.cli._check.check_nav_contract", return_value=[])
@patch("zenzic.cli._check.scan_docs_references", return_value=([], []))
def test_check_all_text_ok(_refs, _nav, _assets, _ph, _snip, _orphans, _links, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "all"])
    assert result.exit_code == 0
    assert "Obsidian Seal" in result.stdout or "SUCCESS" in result.stdout


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, True))
@patch(
    "zenzic.cli._check.validate_links_structured",
    return_value=[
        LinkError(
            file_path=_ROOT / "docs" / "index.md",
            line_no=1,
            message="index.md:1: broken link",
        )
    ],
)
@patch("zenzic.cli._check.find_orphans", return_value=[Path("orphan.md")])
@patch(
    "zenzic.cli._check.validate_snippets",
    return_value=[SnippetError(file_path=Path("api.md"), line_no=5, message="SyntaxError")],
)
@patch(
    "zenzic.cli._check.find_placeholders",
    return_value=[
        PlaceholderFinding(file_path=Path("stub.md"), line_no=1, issue="short-content", detail="x")
    ],
)
@patch("zenzic.cli._check.find_unused_assets", return_value=[Path("assets/unused.png")])
@patch("zenzic.cli._check.check_nav_contract", return_value=[])
@patch("zenzic.cli._check.scan_docs_references", return_value=([], []))
def test_check_all_text_with_all_errors(
    _refs, _nav, _assets, _ph, _snip, _orphans, _links, _cfg, _root
) -> None:
    result = runner.invoke(app, ["check", "all"])
    assert result.exit_code == 1
    assert "FAILED" in result.stdout
    assert "error" in result.stdout.lower()
    assert "orphan.md" in result.stdout
    assert "SyntaxError" in result.stdout
    assert "unused.png" in result.stdout or "ASSET" in result.stdout


# ---------------------------------------------------------------------------
# check all — quiet mode
# ---------------------------------------------------------------------------


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, True))
@patch("zenzic.cli._check.validate_links_structured", return_value=[])
@patch("zenzic.cli._check.find_orphans", return_value=[])
@patch("zenzic.cli._check.validate_snippets", return_value=[])
@patch("zenzic.cli._check.find_placeholders", return_value=[])
@patch("zenzic.cli._check.find_unused_assets", return_value=[])
@patch("zenzic.cli._check.check_nav_contract", return_value=[])
@patch("zenzic.cli._check.scan_docs_references", return_value=([], []))
def test_check_all_quiet_ok(
    _refs, _nav, _assets, _ph, _snip, _orphans, _links, _cfg, _root
) -> None:
    result = runner.invoke(app, ["check", "all", "--quiet"])
    assert result.exit_code == 0
    # Quiet mode produces no output when clean
    assert "zenzic" not in result.stdout.lower() or result.stdout.strip() == ""


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, True))
@patch(
    "zenzic.cli._check.validate_links_structured",
    return_value=[
        LinkError(
            file_path=_ROOT / "docs" / "index.md",
            line_no=1,
            message="broken link",
        )
    ],
)
@patch("zenzic.cli._check.find_orphans", return_value=[])
@patch("zenzic.cli._check.validate_snippets", return_value=[])
@patch("zenzic.cli._check.find_placeholders", return_value=[])
@patch("zenzic.cli._check.find_unused_assets", return_value=[])
@patch("zenzic.cli._check.check_nav_contract", return_value=[])
@patch("zenzic.cli._check.scan_docs_references", return_value=([], []))
def test_check_all_quiet_with_errors(
    _refs, _nav, _assets, _ph, _snip, _orphans, _links, _cfg, _root
) -> None:
    result = runner.invoke(app, ["check", "all", "--quiet"])
    assert result.exit_code == 1
    assert "error" in result.stdout.lower()


# ---------------------------------------------------------------------------
# check all — strict gate on warnings
# ---------------------------------------------------------------------------


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, True))
@patch("zenzic.cli._check.validate_links_structured", return_value=[])
@patch("zenzic.cli._check.find_orphans", return_value=[])
@patch("zenzic.cli._check.validate_snippets", return_value=[])
@patch("zenzic.cli._check.find_placeholders", return_value=[])
@patch("zenzic.cli._check.find_unused_assets", return_value=[])
@patch("zenzic.cli._check.check_nav_contract", return_value=[])
@patch("zenzic.cli._check.scan_docs_references")
def test_check_all_strict_fails_on_warnings_only(
    mock_refs, _nav, _assets, _ph, _snip, _orphans, _links, _cfg, _root
) -> None:
    """--strict must exit 1 even when only warnings (no hard errors) exist."""
    from zenzic.models.references import IntegrityReport, ReferenceFinding

    finding = ReferenceFinding(
        file_path=Path("docs/guide.md"),
        line_no=10,
        issue="DEAD_DEF",
        detail="[unused]: never referenced",
        is_warning=True,
    )
    report = IntegrityReport(file_path=Path("docs/guide.md"), score=90.0)
    report.findings = [finding]
    mock_refs.return_value = ([report], [])

    result = runner.invoke(app, ["check", "all", "--strict"])
    assert result.exit_code == 1


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, True))
@patch("zenzic.cli._check.validate_links_structured", return_value=[])
@patch("zenzic.cli._check.find_orphans", return_value=[])
@patch("zenzic.cli._check.validate_snippets", return_value=[])
@patch("zenzic.cli._check.find_placeholders", return_value=[])
@patch("zenzic.cli._check.find_unused_assets", return_value=[])
@patch("zenzic.cli._check.check_nav_contract", return_value=[])
@patch("zenzic.cli._check.scan_docs_references")
def test_check_all_no_strict_passes_on_warnings_only(
    mock_refs, _nav, _assets, _ph, _snip, _orphans, _links, _cfg, _root
) -> None:
    """Without --strict, warnings alone must NOT trigger exit 1."""
    from zenzic.models.references import IntegrityReport, ReferenceFinding

    finding = ReferenceFinding(
        file_path=Path("docs/guide.md"),
        line_no=10,
        issue="DEAD_DEF",
        detail="[unused]: never referenced",
        is_warning=True,
    )
    report = IntegrityReport(file_path=Path("docs/guide.md"), score=90.0)
    report.findings = [finding]
    mock_refs.return_value = ([report], [])

    result = runner.invoke(app, ["check", "all"])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# check all — target argument (file and directory mode)
# ---------------------------------------------------------------------------


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, True))
def test_check_all_target_not_found(_cfg, _root) -> None:
    """Non-existent target must exit 1 with an error message."""
    result = runner.invoke(app, ["check", "all", "nonexistent.md"])
    assert result.exit_code == 1
    assert "not found" in result.stdout.lower()
    assert "nonexistent.md" in result.stdout


def test_check_all_target_single_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Single .md file target: findings filtered, banner shows 1 file."""
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "zenzic.toml").touch()
    _body = "word " * 60
    (repo / "docs" / "index.md").write_text(f"# Hello\n\n{_body}\n")
    (repo / "docs" / "other.md").write_text(f"# Other\n\n{_body}\n")
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["check", "all", "docs/index.md"])
    assert result.exit_code == 0
    assert "1 file" in result.stdout
    assert "other.md" not in result.stdout


def test_check_all_target_file_outside_docs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """File outside docs_dir (e.g. README.md): config patched, exit 0."""
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "zenzic.toml").touch()
    _body = "word " * 60
    (repo / "docs" / "index.md").write_text(f"# Hello\n\n{_body}\n")
    (repo / "README.md").write_text(f"# Project\n\n{_body}\n")
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["check", "all", "README.md"])
    assert result.exit_code == 0
    assert "1 file" in result.stdout
    assert "README.md" in result.stdout
    assert "index.md" not in result.stdout


def test_check_all_target_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Directory target: config patched to that dir, full scan within it."""
    repo = tmp_path / "repo"
    (repo / "content").mkdir(parents=True)
    (repo / "docs").mkdir()
    (repo / "zenzic.toml").touch()
    _body = "word " * 60
    (repo / "content" / "page.md").write_text(f"# Page\n\n{_body}\n")
    (repo / "docs" / "other.md").write_text(f"# Other\n\n{_body}\n")
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["check", "all", "content"])
    assert result.exit_code == 0
    assert "./content/" in result.stdout
    assert "other.md" not in result.stdout


# ---------------------------------------------------------------------------
# SentinelReporter unit tests
# ---------------------------------------------------------------------------


class TestSentinelReporter:
    """Unit tests for the Sentinel Report Engine."""

    def test_render_no_findings(self) -> None:
        from io import StringIO

        from rich.console import Console

        from zenzic.core.reporter import SentinelReporter

        buf = StringIO()
        con = Console(file=buf, highlight=False, no_color=True)
        reporter = SentinelReporter(con, Path("/fake/docs"))
        errors, warnings = reporter.render(
            [], version="0.5.0a3", elapsed=1.0, docs_count=6, assets_count=4
        )
        assert errors == 0
        assert warnings == 0
        output = buf.getvalue()
        assert "auto" in output  # telemetry engine field
        assert "Obsidian Seal" in output

    def test_render_grouped_findings(self) -> None:
        from io import StringIO

        from rich.console import Console

        from zenzic.core.reporter import Finding, SentinelReporter

        findings = [
            Finding("guide/index.md", 10, "LINK_ERROR", "error", "broken link"),
            Finding("guide/index.md", 20, "SNIPPET", "error", "syntax error"),
            Finding("about.md", 5, "ORPHAN", "warning", "not in nav"),
        ]
        buf = StringIO()
        con = Console(file=buf, highlight=False, no_color=True)
        reporter = SentinelReporter(con, Path("/fake/docs"))
        errors, warnings = reporter.render(
            findings, version="0.5.0a3", elapsed=0.5, docs_count=5, assets_count=0
        )
        assert errors == 2
        assert warnings == 1
        output = buf.getvalue()
        assert "guide/index.md" in output
        assert "about.md" in output
        assert "2 errors" in output
        assert "1 warning" in output

    def test_render_quiet_no_findings(self) -> None:
        from io import StringIO

        from rich.console import Console

        from zenzic.core.reporter import SentinelReporter

        buf = StringIO()
        con = Console(file=buf, highlight=False, no_color=True)
        reporter = SentinelReporter(con, Path("/fake/docs"))
        errors, warnings = reporter.render_quiet([])
        assert errors == 0
        assert warnings == 0
        assert buf.getvalue().strip() == ""

    def test_render_quiet_with_findings(self) -> None:
        from io import StringIO

        from rich.console import Console

        from zenzic.core.reporter import Finding, SentinelReporter

        findings = [
            Finding("x.md", 1, "E001", "error", "bad"),
            Finding("y.md", 2, "W001", "warning", "meh"),
        ]
        buf = StringIO()
        con = Console(file=buf, highlight=False, no_color=True)
        reporter = SentinelReporter(con, Path("/fake/docs"))
        errors, warnings = reporter.render_quiet(findings)
        assert errors == 1
        assert warnings == 1
        assert "1 error" in buf.getvalue()
        assert "1 warning" in buf.getvalue()


# ---------------------------------------------------------------------------
# check references — rule_findings surfaced in CLI output
# ---------------------------------------------------------------------------


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, True))
@patch(
    "zenzic.cli._check.scan_docs_references",
    return_value=([], []),
)
def test_check_references_ok(_scan, _cfg, _root) -> None:
    result = runner.invoke(app, ["check", "references"])
    assert result.exit_code == 0
    assert "ZENZIC SENTINEL" in result.stdout
    assert "All references resolved." in result.stdout


@patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
@patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, True))
@patch("zenzic.cli._check.scan_docs_references")
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
    assert "error" in result.stdout.lower()


# ---------------------------------------------------------------------------
# init --plugin
# ---------------------------------------------------------------------------


def test_init_plugin_scaffold_creates_expected_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["init", "--plugin", "plugin-scaffold-demo"])
    assert result.exit_code == 0

    root = repo / "plugin-scaffold-demo"
    assert (root / "pyproject.toml").is_file()
    assert (root / "src" / "plugin_scaffold_demo" / "rules.py").is_file()
    assert (root / "docs" / "index.md").is_file()

    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert '[project.entry-points."zenzic.rules"]' in pyproject
    assert 'plugin-scaffold-demo = "plugin_scaffold_demo.rules:PluginScaffoldDemoRule"' in pyproject

    rules_py = (root / "src" / "plugin_scaffold_demo" / "rules.py").read_text(encoding="utf-8")
    assert "class PluginScaffoldDemoRule(BaseRule):" in rules_py


def test_init_plugin_scaffold_existing_dir_requires_force(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "plugin-scaffold-demo").mkdir()
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["init", "--plugin", "plugin-scaffold-demo"])
    assert result.exit_code == 1
    assert "already exists" in result.stdout


# ---------------------------------------------------------------------------
# init — Smart Initialization (standalone vs pyproject.toml)
# ---------------------------------------------------------------------------


def test_init_standalone_creates_zenzic_toml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Default init (no pyproject.toml present) creates zenzic.toml."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0

    cfg = repo / "zenzic.toml"
    assert cfg.is_file()
    content = cfg.read_text(encoding="utf-8")
    assert "docs_dir" in content
    assert "fail_under" in content


def test_init_standalone_detects_mkdocs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Engine auto-detection writes [build_context] when mkdocs.yml exists."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "mkdocs.yml").write_text("site_name: test\n", encoding="utf-8")
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0

    content = (repo / "zenzic.toml").read_text(encoding="utf-8")
    assert 'engine = "mkdocs"' in content


def test_init_standalone_warns_if_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Refuse to overwrite existing zenzic.toml without --force."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "zenzic.toml").write_text("# existing\n", encoding="utf-8")
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["init"])
    assert result.exit_code == 1
    assert "already exists" in result.stdout


def test_init_standalone_force_overwrites(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--force overwrites an existing zenzic.toml."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "zenzic.toml").write_text("# old\n", encoding="utf-8")
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["init", "--force"])
    assert result.exit_code == 0

    content = (repo / "zenzic.toml").read_text(encoding="utf-8")
    assert "zenzic.dev/docs/reference/configuration/" in content
    assert "# old" not in content


def test_init_pyproject_flag_appends_tool_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--pyproject appends [tool.zenzic] to an existing pyproject.toml."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "pyproject.toml").write_text('[project]\nname = "myapp"\n', encoding="utf-8")
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["init", "--pyproject"])
    assert result.exit_code == 0

    content = (repo / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.zenzic]" in content
    assert 'name = "myapp"' in content  # original content preserved


def test_init_pyproject_with_mkdocs_engine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--pyproject detects mkdocs and writes [tool.zenzic.build_context]."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    (repo / "mkdocs.yml").write_text("site_name: x\n", encoding="utf-8")
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["init", "--pyproject"])
    assert result.exit_code == 0

    content = (repo / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.zenzic.build_context]" in content
    assert 'engine = "mkdocs"' in content


def test_init_pyproject_warns_if_section_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Refuse to overwrite existing [tool.zenzic] without --force."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "x"\n\n[tool.zenzic]\nfail_under = 80\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["init", "--pyproject"])
    assert result.exit_code == 1
    assert "already exists" in result.stdout


def test_init_pyproject_force_replaces_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--pyproject --force replaces an existing [tool.zenzic] section."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "x"\n\n[tool.zenzic]\nfail_under = 80\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["init", "--pyproject", "--force"])
    assert result.exit_code == 0

    content = (repo / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.zenzic]" in content
    assert "fail_under = 80" not in content  # old section removed
    assert 'name = "x"' in content  # project section preserved


def test_init_pyproject_no_file_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--pyproject without a pyproject.toml file exits with error."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["init", "--pyproject"])
    assert result.exit_code == 1
    assert "No" in result.stdout and "pyproject.toml" in result.stdout


def test_init_interactive_prompt_chooses_pyproject(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When pyproject.toml exists and user answers 'y', config goes into pyproject."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["init"], input="y\n")
    assert result.exit_code == 0

    content = (repo / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.zenzic]" in content
    assert not (repo / "zenzic.toml").is_file()


def test_init_interactive_prompt_chooses_standalone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When pyproject.toml exists and user answers 'n', creates zenzic.toml."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["init"], input="n\n")
    assert result.exit_code == 0
    assert (repo / "zenzic.toml").is_file()

    # pyproject.toml must NOT have [tool.zenzic]
    content = (repo / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.zenzic]" not in content


def test_init_standalone_no_engine_detected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without mkdocs.yml or zensical.toml, standalone feedback is shown."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0

    assert "standalone" in result.stdout.lower() or "engine-agnostic" in result.stdout.lower()


# ---------------------------------------------------------------------------
# init — ZRT-005 Bootstrap Paradox (Genesis Fallback)
# ---------------------------------------------------------------------------


def test_init_in_fresh_directory_no_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ZRT-005: zenzic init must succeed in a brand-new directory with no .git."""
    fresh = tmp_path / "brand_new_project"
    fresh.mkdir()
    monkeypatch.chdir(fresh)

    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0, result.stdout
    assert (fresh / "zenzic.toml").is_file()


# ---------------------------------------------------------------------------
# Signal-to-Noise: --show-info / reporter show_info filter
# ---------------------------------------------------------------------------


class TestShowInfoFilter:
    """Verify that info-severity findings are suppressed by default and shown with --show-info."""

    @staticmethod
    def _make_reporter(buf):  # type: ignore[no-untyped-def]
        from rich.console import Console

        from zenzic.core.reporter import SentinelReporter

        con = Console(file=buf, highlight=False, markup=True)
        return SentinelReporter(con, Path("/fake/docs"), docs_dir="docs")

    @staticmethod
    def _info_finding():  # type: ignore[no-untyped-def]
        from zenzic.core.reporter import Finding

        return Finding(
            rel_path="guide/nav.md",
            line_no=5,
            code="CIRCULAR_LINK",
            severity="info",
            message="guide/nav.md:5: 'index.md' is part of a circular link cycle",
            source_line="[Home](index.md)",
        )

    def test_info_finding_suppressed_by_default(self) -> None:
        """With show_info=False (default), info findings must not appear in output."""
        import io

        buf = io.StringIO()
        reporter = self._make_reporter(buf)
        errors, warnings = reporter.render(
            [self._info_finding()],
            version="0.5.0a4",
            elapsed=0.0,
            show_info=False,
        )
        out = buf.getvalue()
        assert "CIRCULAR_LINK" not in out
        assert "suppressed" in out
        assert errors == 0
        assert warnings == 0

    def test_info_finding_shown_with_show_info_true(self) -> None:
        """With show_info=True, info findings must appear in output and no suppression note."""
        import io

        buf = io.StringIO()
        reporter = self._make_reporter(buf)
        errors, warnings = reporter.render(
            [self._info_finding()],
            version="0.5.0a4",
            elapsed=0.0,
            show_info=True,
        )
        out = buf.getvalue()
        assert "CIRCULAR_LINK" in out
        assert "suppressed" not in out
        assert errors == 0
        assert warnings == 0

    @patch("zenzic.cli._check.find_repo_root", return_value=_ROOT)
    @patch("zenzic.cli._check.ZenzicConfig.load", return_value=(_CFG, True))
    @patch("zenzic.cli._check.validate_links_structured", return_value=[])
    @patch("zenzic.cli._check.find_orphans", return_value=[])
    @patch("zenzic.cli._check.validate_snippets", return_value=[])
    @patch("zenzic.cli._check.find_placeholders", return_value=[])
    @patch("zenzic.cli._check.find_unused_assets", return_value=[])
    @patch("zenzic.cli._check.check_nav_contract", return_value=[])
    @patch("zenzic.cli._check.scan_docs_references", return_value=([], []))
    def test_check_all_show_info_flag_accepted(
        self, _refs, _nav, _assets, _ph, _snip, _orphans, _links, _cfg, _root
    ) -> None:
        """--show-info flag must be accepted by check all without crashing."""
        result = runner.invoke(app, ["check", "all", "--show-info"])
        assert result.exit_code == 0, result.stdout
