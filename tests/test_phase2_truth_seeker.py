# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Phase 2 Truth-Seeker tests: Sovereign Audit and Secret Guard."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from zenzic.cli._check import _apply_per_file_ignores
from zenzic.core.reporter import Finding
from zenzic.core.rules import _is_suppressed
from zenzic.core.sovereign_context import sovereign_context
from zenzic.main import app
from zenzic.models.config import GovernanceConfig, ZenzicConfig


runner = CliRunner()


def test_inline_suppression_is_ignored_in_sovereign_audit_mode() -> None:
    line = "Legacy name <!-- zenzic-ignore: Z601 - historical -->"
    assert _is_suppressed(line, "Z601") is True

    with sovereign_context(force_audit=True):
        assert _is_suppressed(line, "Z601") is False


def test_per_file_ignores_are_disabled_in_sovereign_audit_mode() -> None:
    findings = [
        Finding(
            rel_path="docs/example.md",
            line_no=12,
            code="Z601",
            severity="warning",
            message="obsolete brand",
        )
    ]
    config = ZenzicConfig(governance=GovernanceConfig(per_file_ignores={"docs/*.md": ["Z601"]}))

    normal = _apply_per_file_ignores(findings, config)
    assert normal == []

    with sovereign_context(force_audit=True):
        audited = _apply_per_file_ignores(findings, config)
    assert len(audited) == 1
    assert audited[0].code == "Z601"


def test_guard_scan_detects_secrets_and_exits_2(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "zenzic.toml").write_text("docs_dir = '.'\n", encoding="utf-8")
    bad = repo / "README.md"
    bad.write_text("token = ghp_abcdefghijklmnopqrstuvwxyz1234567890", encoding="utf-8")
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["guard", "scan", "README.md"])
    assert result.exit_code == 2, result.output
    assert "github-token" in result.output


def test_guard_scan_clean_exit_zero(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "zenzic.toml").write_text("docs_dir = '.'\n", encoding="utf-8")
    ok = repo / "README.md"
    ok.write_text("No credentials here.", encoding="utf-8")
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["guard", "scan", "README.md"])
    assert result.exit_code == 0, result.output
    assert "Secret Guard clean" in result.output


def test_guard_init_writes_hook_and_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)

    first = runner.invoke(app, ["guard", "init"])
    assert first.exit_code == 0, first.output
    hooks = repo / ".pre-commit-hooks.yaml"
    content = hooks.read_text(encoding="utf-8")
    assert "- id: zenzic-guard" in content

    second = runner.invoke(app, ["guard", "init"])
    assert second.exit_code == 0, second.output
    content_after = hooks.read_text(encoding="utf-8")
    assert content_after.count("- id: zenzic-guard") == 1
