# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for the Zenzic Rule Engine: BaseRule, CustomRule, RuleEngine."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from zenzic.core.rules import (
    BaseRule,
    CustomRule,
    RuleEngine,
    RuleFinding,
    Violation,
    VSMBrokenLinkRule,
)
from zenzic.models.config import CustomRuleConfig, ZenzicConfig
from zenzic.models.vsm import Route


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


# ─── Violation dataclass ──────────────────────────────────────────────────────


class TestViolation:
    """🎨 Dev 2: verify the Violation contract (code, level, context)."""

    def test_violation_fields(self) -> None:
        v = Violation(
            file_path=_FILE,
            line_no=5,
            code="Z001",
            message="Broken link.",
            level="error",
            context="[bad link](missing.md)",
        )
        assert v.code == "Z001"
        assert v.level == "error"
        assert v.context == "[bad link](missing.md)"
        assert v.is_error

    def test_violation_warning_not_error(self) -> None:
        v = Violation(file_path=_FILE, line_no=1, code="Z002", message="hint", level="warning")
        assert not v.is_error

    def test_violation_as_finding_round_trip(self) -> None:
        v = Violation(
            file_path=_FILE,
            line_no=3,
            code="Z001",
            message="msg",
            level="error",
            context="src",
        )
        f = v.as_finding()
        assert isinstance(f, RuleFinding)
        assert f.rule_id == "Z001"
        assert f.line_no == 3
        assert f.matched_line == "src"
        assert f.severity == "error"


# ─── VSMBrokenLinkRule ────────────────────────────────────────────────────────


def _make_vsm(*urls: str, status: str = "REACHABLE") -> dict[str, Route]:
    """Build a minimal VSM dict with the given URL slugs."""
    return {
        url: Route(url=url, source=f"{url.strip('/')}.md", status=status)  # type: ignore[arg-type]
        for url in urls
    }


class TestVSMBrokenLinkRule:
    """🔌 Dev 3: VSM-aware link validation."""

    _RULE = VSMBrokenLinkRule()
    _EMPTY_ANCHORS: dict[Path, set[str]] = {}

    def _run(self, text: str, vsm: dict) -> list[Violation]:
        return self._RULE.check_vsm(_FILE, text, vsm, self._EMPTY_ANCHORS)

    # ── check() is a no-op ────────────────────────────────────────────────────

    def test_check_returns_empty(self) -> None:
        assert self._RULE.check(_FILE, "[link](page.md)") == []

    # ── REACHABLE link → no violation ─────────────────────────────────────────

    def test_reachable_link_passes(self) -> None:
        vsm = _make_vsm("/guide/")
        violations = self._run("[Guide](guide/index.md)", vsm)
        assert violations == []

    def test_reachable_page_without_md_suffix(self) -> None:
        vsm = _make_vsm("/guide/install/")
        violations = self._run("[Install](guide/install)", vsm)
        assert violations == []

    # ── Missing from VSM → violation ─────────────────────────────────────────

    def test_missing_url_emits_violation(self) -> None:
        violations = self._run("[Broken](missing.md)", {})
        assert len(violations) == 1
        assert violations[0].code == "Z001"
        assert "missing" in violations[0].message
        assert "missing.md" in violations[0].context

    # ── ORPHAN status → violation ─────────────────────────────────────────────

    def test_orphan_link_emits_violation(self) -> None:
        vsm = _make_vsm("/draft/", status="ORPHAN_BUT_EXISTING")
        violations = self._run("[Draft](draft.md)", vsm)
        assert len(violations) == 1
        assert "UNREACHABLE_LINK" in violations[0].message

    # ── External links are skipped ────────────────────────────────────────────

    def test_external_http_skipped(self) -> None:
        violations = self._run("[Ext](https://example.com)", {})
        assert violations == []

    def test_external_mailto_skipped(self) -> None:
        violations = self._run("[Mail](mailto:user@example.com)", {})
        assert violations == []

    # ── Bare fragment skipped ─────────────────────────────────────────────────

    def test_bare_fragment_skipped(self) -> None:
        violations = self._run("[Top](#top)", {})
        assert violations == []

    # ── Code blocks are skipped ───────────────────────────────────────────────

    def test_link_inside_fenced_block_skipped(self) -> None:
        text = "```\n[broken](totally-missing.md)\n```"
        violations = self._run(text, {})
        assert violations == []

    # ── Violation carries source context ──────────────────────────────────────

    def test_violation_context_is_source_line(self) -> None:
        violations = self._run("See [this](gone.md) for details.", {})
        assert len(violations) == 1
        assert "gone.md" in violations[0].context

    def test_violation_line_number_is_correct(self) -> None:
        text = "# Heading\n\nSome text.\n\n[Broken](ghost.md)\n"
        violations = self._run(text, {})
        assert len(violations) == 1
        assert violations[0].line_no == 5

    # ── RuleEngine.run_vsm integration ───────────────────────────────────────

    def test_run_vsm_converts_violations_to_findings(self) -> None:
        engine = RuleEngine([VSMBrokenLinkRule()])
        vsm = _make_vsm("/ok/")
        findings = engine.run_vsm(_FILE, "[OK](ok/index.md)\n[Bad](ghost.md)\n", vsm, {})
        assert len(findings) == 1
        assert findings[0].rule_id == "Z001"
        assert isinstance(findings[0], RuleFinding)


# ─── Dev 4: O(N) Torture Test — Rule Engine scalability ──────────────────────
# Invariant: VSMBrokenLinkRule.check_vsm must complete in O(N) time where N
# is the number of VSM nodes.  The test builds a 10 000-node VSM and a file
# with 10 000 links and verifies the runtime is < 1 s (far below the O(N²)
# threshold, which would be ~100× slower on this data size).


class TestRuleEngineTortureTest:
    """🛡️ Dev 4: Performance and scalability invariants for the Rule Engine."""

    _N = 10_000

    def _make_large_vsm(self) -> dict[str, Route]:
        return {
            f"/page-{i}/": Route(
                url=f"/page-{i}/",
                source=f"page-{i}.md",
                status="REACHABLE",  # type: ignore[arg-type]
            )
            for i in range(self._N)
        }

    def _make_text_with_links(self, n: int, *, all_valid: bool) -> str:
        """Generate a Markdown file with *n* inline links.

        When *all_valid* is True, every link points to a known VSM page.
        When False, all links point to missing pages (worst-case violation path).
        """
        lines = []
        for i in range(n):
            if all_valid:
                lines.append(f"[Page {i}](page-{i}.md)")
            else:
                lines.append(f"[Page {i}](missing-{i}.md)")
        return "\n".join(lines)

    def test_check_vsm_scales_linearly_all_valid(self) -> None:
        """10 000 REACHABLE links must resolve in < 1 s (O(N) dict lookups)."""
        rule = VSMBrokenLinkRule()
        vsm = self._make_large_vsm()
        text = self._make_text_with_links(self._N, all_valid=True)

        start = time.monotonic()
        violations = rule.check_vsm(_FILE, text, vsm, {})
        elapsed = time.monotonic() - start

        assert violations == [], f"Expected 0 violations, got {len(violations)}"
        assert elapsed < 1.0, (
            f"check_vsm took {elapsed:.3f}s for {self._N} valid links — possible O(N²) regression"
        )

    def test_check_vsm_scales_linearly_all_missing(self) -> None:
        """10 000 missing links (worst-case violation path) must complete < 1 s."""
        rule = VSMBrokenLinkRule()
        vsm = self._make_large_vsm()
        text = self._make_text_with_links(self._N, all_valid=False)

        start = time.monotonic()
        violations = rule.check_vsm(_FILE, text, vsm, {})
        elapsed = time.monotonic() - start

        assert len(violations) == self._N, f"Expected {self._N} violations, got {len(violations)}"
        assert elapsed < 1.0, (
            f"check_vsm took {elapsed:.3f}s for {self._N} missing links — possible O(N²) regression"
        )

    def test_run_vsm_engine_scales_with_large_vsm(self) -> None:
        """RuleEngine.run_vsm with 10 000-node VSM must complete < 1 s."""
        engine = RuleEngine([VSMBrokenLinkRule()])
        vsm = self._make_large_vsm()
        # Small file — only the VSM lookup overhead is being measured here
        text = "\n".join(f"[P](page-{i}.md)" for i in range(100))

        start = time.monotonic()
        findings = engine.run_vsm(_FILE, text, vsm, {})
        elapsed = time.monotonic() - start

        assert findings == []
        assert elapsed < 0.5, f"run_vsm took {elapsed:.3f}s with {self._N}-node VSM — regression"
