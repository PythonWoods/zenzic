# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for the Zenzic Rule Engine: BaseRule, CustomRule, RuleEngine."""

from __future__ import annotations

from pathlib import Path

import pytest

from zenzic.core.rules import BaseRule, CustomRule, RuleEngine, RuleFinding
from zenzic.models.config import CustomRuleConfig, ZenzicConfig


_FILE = Path("docs/guide.md")


# ─── CustomRule ───────────────────────────────────────────────────────────────


def test_custom_rule_single_match() -> None:
    rule = CustomRule(id="ZZ001", pattern=r"TODO", message="Remove TODO.", severity="warning")
    findings = rule.check(_FILE, "Line one.\nTODO: fix this.\nLine three.\n")
    assert len(findings) == 1
    assert findings[0].line_no == 2
    assert findings[0].rule_id == "ZZ001"
    assert findings[0].severity == "warning"
    assert not findings[0].is_error


def test_custom_rule_multiple_matches() -> None:
    rule = CustomRule(id="ZZ002", pattern=r"(?i)\bDRAFT\b", message="Draft.", severity="error")
    text = "DRAFT intro.\nNormal line.\ndraft section.\n"
    findings = rule.check(_FILE, text)
    assert len(findings) == 2
    assert {f.line_no for f in findings} == {1, 3}


def test_custom_rule_no_match() -> None:
    rule = CustomRule(id="ZZ003", pattern=r"SECRET", message="Secret.", severity="error")
    findings = rule.check(_FILE, "This text is clean.\nNo issues here.\n")
    assert findings == []


def test_custom_rule_invalid_regex_raises() -> None:
    with pytest.raises(ValueError, match="invalid regex"):
        CustomRule(id="ZZ004", pattern=r"[unclosed", message="Bad pattern.", severity="error")


def test_custom_rule_is_error_severity() -> None:
    rule = CustomRule(id="ZZ005", pattern=r"x", message="x found.", severity="error")
    findings = rule.check(_FILE, "x\n")
    assert findings[0].is_error


def test_custom_rule_info_severity_not_error() -> None:
    rule = CustomRule(id="ZZ006", pattern=r"x", message="x found.", severity="info")
    findings = rule.check(_FILE, "x\n")
    assert not findings[0].is_error


# ─── RuleEngine ───────────────────────────────────────────────────────────────


def test_rule_engine_empty_no_findings() -> None:
    engine = RuleEngine([])
    assert not engine
    assert engine.run(_FILE, "any text") == []


def test_rule_engine_bool_true_when_rules_present() -> None:
    rule = CustomRule(id="ZZ007", pattern=r"x", message="x", severity="error")
    engine = RuleEngine([rule])
    assert engine


def test_rule_engine_multiple_rules_combined() -> None:
    r1 = CustomRule(id="ZZ008", pattern=r"TODO", message="todo found", severity="error")
    r2 = CustomRule(id="ZZ009", pattern=r"FIXME", message="fixme found", severity="warning")
    engine = RuleEngine([r1, r2])
    text = "Line with TODO here.\nAnother FIXME line.\n"
    findings = engine.run(_FILE, text)
    assert len(findings) == 2
    rule_ids = {f.rule_id for f in findings}
    assert rule_ids == {"ZZ008", "ZZ009"}


def test_rule_engine_isolates_exception() -> None:
    """A rule that raises must not abort the entire engine run."""

    class BrokenRule(BaseRule):
        @property
        def rule_id(self) -> str:
            return "ZZ-BROKEN"

        def check(self, file_path: Path, text: str) -> list[RuleFinding]:
            raise RuntimeError("rule internal error")

    good_rule = CustomRule(id="ZZ010", pattern=r"x", message="x found", severity="info")
    engine = RuleEngine([BrokenRule(), good_rule])
    findings = engine.run(_FILE, "x line\n")

    # One error from the broken rule, one info from the good rule
    assert len(findings) == 2
    engine_err = next(f for f in findings if f.rule_id == "RULE-ENGINE-ERROR")
    assert "BrokenRule" in engine_err.message or "rule internal error" in engine_err.message
    assert engine_err.severity == "error"

    good_finding = next(f for f in findings if f.rule_id == "ZZ010")
    assert good_finding.severity == "info"


# ─── Integration with scanner ──────────────────────────────────────────────────


def test_scan_single_file_with_rule_engine(tmp_path: Path) -> None:
    """_scan_single_file applies the rule engine and stores findings in the report."""
    from zenzic.core.scanner import _scan_single_file

    md = tmp_path / "guide.md"
    md.write_text("# Guide\n\nThis is TODO content.\n")
    config = ZenzicConfig()
    rule = CustomRule(id="ZZ-TODO", pattern=r"TODO", message="Remove TODO.", severity="warning")
    engine = RuleEngine([rule])

    report, _ = _scan_single_file(md, config, engine)
    assert len(report.rule_findings) == 1
    assert report.rule_findings[0].rule_id == "ZZ-TODO"
    assert report.rule_findings[0].line_no == 3


def test_scan_single_file_no_rule_engine(tmp_path: Path) -> None:
    """Without a rule engine, rule_findings is empty."""
    from zenzic.core.scanner import _scan_single_file

    md = tmp_path / "guide.md"
    md.write_text("# Guide\n\nTODO: fix\n")
    config = ZenzicConfig()

    report, _ = _scan_single_file(md, config, None)
    assert report.rule_findings == []


def test_scan_docs_with_custom_rules_from_config(tmp_path: Path) -> None:
    """scan_docs_references picks up [[custom_rules]] from config."""
    from zenzic.core.scanner import scan_docs_references

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "page.md").write_text("# Page\n\nPlease remove DRAFT marker.\n")

    config = ZenzicConfig(
        custom_rules=[
            CustomRuleConfig(
                id="ZZ-DRAFT",
                pattern=r"(?i)\bDRAFT\b",
                message="Remove DRAFT.",
                severity="error",
            )
        ]
    )
    reports = scan_docs_references(tmp_path, config)
    assert len(reports) == 1
    assert len(reports[0].rule_findings) == 1
    assert reports[0].rule_findings[0].rule_id == "ZZ-DRAFT"


# ─── Cross-adapter custom rules (Dev 4 mandate) ───────────────────────────────


def _make_repo_with_draft(tmp_path: Path) -> Path:
    """Create a minimal repo with a single docs/page.md containing 'DRAFT'."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "page.md").write_text("# Page\n\nThis is a DRAFT page.\n")
    return tmp_path


def _draft_rule_config() -> ZenzicConfig:
    return ZenzicConfig(
        custom_rules=[
            CustomRuleConfig(
                id="ZZ-DRAFT",
                pattern=r"(?i)\bDRAFT\b",
                message="Remove DRAFT marker before publishing.",
                severity="error",
            )
        ]
    )


@pytest.mark.parametrize("engine", ["mkdocs", "zensical", "auto"])
def test_custom_rules_fire_regardless_of_engine(
    tmp_path: Path,
    engine: str,
) -> None:
    """Dev 4 mandate: [[custom_rules]] must fire identically for every adapter.

    The rule engine operates on raw Markdown text — it has no knowledge of the
    build engine.  This test verifies that the DRAFT rule is triggered whether
    the adapter is MkDocs, Zensical, or VanillaAdapter (auto-detected).
    """
    from zenzic.core.scanner import scan_docs_references

    repo = _make_repo_with_draft(tmp_path)

    # Build a config that selects the requested adapter via build_context.engine.
    # For "auto" no engine override is needed — VanillaAdapter will be selected
    # because no mkdocs.yml or zensical.toml is present.
    base_config = _draft_rule_config()
    if engine != "auto":
        new_context = base_config.build_context.model_copy(update={"engine": engine})
        config: ZenzicConfig = base_config.model_copy(update={"build_context": new_context})
    else:
        config = base_config

    # For zensical engine, a zensical.toml must exist (factory enforcement contract).
    if engine == "zensical":
        (repo / "zensical.toml").write_text("[site]\nname = 'Test'\n")

    reports = scan_docs_references(repo, config)
    assert len(reports) == 1, f"Expected 1 report for engine={engine!r}"
    rule_findings = reports[0].rule_findings
    assert len(rule_findings) == 1, (
        f"Expected 1 rule finding for engine={engine!r}, got {rule_findings}"
    )
    assert rule_findings[0].rule_id == "ZZ-DRAFT"
    assert rule_findings[0].is_error
