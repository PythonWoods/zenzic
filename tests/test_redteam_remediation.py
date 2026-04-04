# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for ZRT Red-Team remediation (v0.5.0a4 hotfix).

Covers:
- ZRT-001: Shield must detect secrets in YAML frontmatter
- ZRT-002: _assert_regex_canary must reject ReDoS patterns at engine construction
- ZRT-003: Shield normalizer must catch split-token obfuscation in tables
- ZRT-004: VSMBrokenLinkRule must resolve relative links with source-file context
"""

from __future__ import annotations

import platform
from pathlib import Path

import pytest

from zenzic.core.exceptions import PluginContractError
from zenzic.core.rules import (
    AdaptiveRuleEngine,
    CustomRule,
    ResolutionContext,
    Violation,
    VSMBrokenLinkRule,
    _assert_regex_canary,
)
from zenzic.models.vsm import Route


# Shield/Scanner symbols are committed in Commit 2 (shield.py + scanner.py).
# Guard the import so that Commit 1 alone remains test-runnable: the two
# shield-dependent test classes are skipped until Commit 2 is applied.
try:
    from zenzic.core.scanner import ReferenceScanner
    from zenzic.core.shield import _normalize_line_for_shield, scan_line_for_secrets

    _SHIELD_AVAILABLE = True
except ImportError:
    _normalize_line_for_shield = None  # type: ignore[assignment]
    scan_line_for_secrets = None  # type: ignore[assignment]
    ReferenceScanner = None  # type: ignore[assignment]
    _SHIELD_AVAILABLE = False

_shield_skip = pytest.mark.skipif(
    not _SHIELD_AVAILABLE,
    reason="shield.py normalizer and scanner.py dual-stream not yet committed (Commit 2)",
)


# ─── ZRT-001: Shield must detect secrets in YAML frontmatter ──────────────────


@_shield_skip
class TestShieldFrontmatterCoverage:
    """ZRT-001: The Shield stream must scan ALL lines including frontmatter."""

    def test_shield_catches_aws_key_in_yaml_frontmatter(self, tmp_path: Path) -> None:
        """AWS access key inside YAML frontmatter must trigger a SecurityFinding."""
        from zenzic.core.scanner import ReferenceScanner

        md = tmp_path / "secret.md"
        md.write_text(
            "---\n"
            "aws_key: AKIA1234567890ABCDEF\n"
            "title: API Guide\n"
            "---\n\n"
            "# Guide\n\nNormal content here.\n"
        )
        scanner = ReferenceScanner(md)
        secrets = [data for _, evt, data in scanner.harvest() if evt == "SECRET"]
        assert len(secrets) >= 1, "Shield must catch AWS key inside YAML frontmatter"
        secret_types = {s.secret_type for s in secrets}
        assert "aws-access-key" in secret_types

    def test_shield_catches_github_token_in_yaml_frontmatter(self, tmp_path: Path) -> None:
        """GitHub PAT inside YAML frontmatter must trigger a SecurityFinding."""
        from zenzic.core.scanner import ReferenceScanner

        md = tmp_path / "github_secret.md"
        md.write_text(
            "---\n"
            "author: John Doe\n"
            "github_token: ghp_1234567890123456789012345678901234567\n"
            "---\n\n"
            "# Guide\n\nNormal content.\n"
        )
        scanner = ReferenceScanner(md)
        secrets = [data for _, evt, data in scanner.harvest() if evt == "SECRET"]
        assert len(secrets) >= 1, "Shield must catch GitHub token inside YAML frontmatter"

    def test_shield_does_not_create_false_positive_on_clean_frontmatter(
        self, tmp_path: Path
    ) -> None:
        """A doc with only safe frontmatter metadata must emit zero secrets."""
        from zenzic.core.scanner import ReferenceScanner

        md = tmp_path / "clean.md"
        md.write_text(
            "---\n"
            "title: Clean Page\n"
            "author: Jane Doe\n"
            "tags: [docs, guide]\n"
            "---\n\n"
            "# Clean Page\n\nThis page has no secrets.\n"
        )
        scanner = ReferenceScanner(md)
        secrets = [data for _, evt, data in scanner.harvest() if evt == "SECRET"]
        assert secrets == [], f"Expected 0 secrets, got: {secrets}"

    def test_shield_secret_line_number_is_inside_frontmatter(self, tmp_path: Path) -> None:
        """The reported line number of a frontmatter secret must be correct."""
        from zenzic.core.scanner import ReferenceScanner

        md = tmp_path / "line_check.md"
        md.write_text(
            "---\n"  # line 1
            "title: Guide\n"  # line 2
            "aws_key: AKIA1234567890ABCDEF\n"  # line 3
            "---\n"  # line 4
        )
        scanner = ReferenceScanner(md)
        secrets = [data for _, evt, data in scanner.harvest() if evt == "SECRET"]
        assert len(secrets) >= 1
        # The secret is on line 3
        assert secrets[0].line_no == 3


# ─── ZRT-002: ReDoS canary must reject catastrophic patterns at construction ──


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="SIGALRM not available on Windows — canary is a no-op there",
)
class TestReDoSCanary:
    """ZRT-002: AdaptiveRuleEngine must reject ReDoS patterns before worker dispatch."""

    def test_canary_rejects_classic_redos_pattern(self) -> None:
        """Pattern (a+)+ must be caught by the canary before engine construction."""
        rule = CustomRule(
            id="ZZ-REDOS",
            pattern=r"^(a+)+$",
            message="ReDoS test.",
            severity="error",
        )
        with pytest.raises(PluginContractError, match="catastrophic backtracking"):
            _assert_regex_canary(rule)

    def test_canary_rejects_alternation_redos(self) -> None:
        """Alternation-based ReDoS (a|aa)+ also caught."""
        rule = CustomRule(
            id="ZZ-REDOS2",
            pattern=r"^(a|aa)+$",
            message="ReDoS alt test.",
            severity="error",
        )
        with pytest.raises(PluginContractError, match="catastrophic backtracking"):
            _assert_regex_canary(rule)

    def test_engine_construction_rejects_redos_custom_rule(self) -> None:
        """AdaptiveRuleEngine.__init__ must raise at construction for ReDoS rules."""
        rule = CustomRule(
            id="ZZ-DEADLOCK",
            pattern=r"^(a+)+$",
            message="Deadlock pattern.",
            severity="error",
        )
        with pytest.raises(PluginContractError, match="catastrophic backtracking"):
            AdaptiveRuleEngine([rule])

    def test_canary_passes_safe_pattern(self) -> None:
        """A simple, safe regex must pass the canary without raising."""
        rule = CustomRule(
            id="ZZ-SAFE",
            pattern=r"TODO",
            message="TODO found.",
            severity="warning",
        )
        # Must not raise
        _assert_regex_canary(rule)

    def test_canary_passes_anchored_safe_pattern(self) -> None:
        """A more complex but safe anchored pattern must pass the canary."""
        rule = CustomRule(
            id="ZZ-SAFE2",
            pattern=r"^(DRAFT|WIP|TODO):?\s",
            message="Status marker.",
            severity="info",
        )
        _assert_regex_canary(rule)

    def test_canary_skips_non_custom_rules(self) -> None:
        """BaseRule subclasses that are not CustomRule are not tested by the canary."""
        from zenzic.core.rules import BaseRule, RuleFinding

        class _TrustedRule(BaseRule):
            @property
            def rule_id(self) -> str:
                return "TRUSTED-001"

            def check(self, file_path: Path, text: str) -> list[RuleFinding]:
                return []

        # Must not raise even though _TrustedRule is not a CustomRule
        _assert_regex_canary(_TrustedRule())


# ─── ZRT-003: Split-token Shield bypass via Markdown table normalizer ──────────


@_shield_skip
class TestShieldNormalizer:
    """ZRT-003: The pre-scan normalizer must reconstruct split-token secrets."""

    def test_normalize_strips_backtick_spans(self) -> None:
        """`AKIA` → AKIA (unwrap inline code)."""
        result = _normalize_line_for_shield("`AKIA`1234567890ABCDEF")
        assert "AKIA1234567890ABCDEF" in result

    def test_normalize_removes_concat_operator(self) -> None:
        """`AKIA` + `1234567890ABCDEF` → AKIA1234567890ABCDEF."""
        result = _normalize_line_for_shield("`AKIA` + `1234567890ABCDEF`")
        assert "AKIA1234567890ABCDEF" in result

    def test_normalize_strips_table_pipes(self) -> None:
        """Pipes → spaces so table cells don't break token continuity."""
        result = _normalize_line_for_shield("| Key | AKIA1234567890ABCDEF |")
        assert "|" not in result
        assert "AKIA1234567890ABCDEF" in result

    def test_normalize_handles_combined_table_and_concat(self) -> None:
        """Full attack vector: table cell with split backtick-concat key."""
        line = "| Access Key | `AKIA` + `1234567890ABCDEF` |"
        result = _normalize_line_for_shield(line)
        assert "AKIA1234567890ABCDEF" in result

    def test_scan_line_catches_split_token_aws_key(self) -> None:
        """scan_line_for_secrets must catch an AWS key split across backtick spans."""
        line = "| Key | `AKIA` + `1234567890ABCDEF` |"
        findings = list(scan_line_for_secrets(line, Path("docs/config.md"), 7))
        assert len(findings) >= 1, f"Expected >=1 finding, got: {findings}"
        assert findings[0].secret_type == "aws-access-key"

    def test_scan_line_no_false_positive_on_clean_table(self) -> None:
        """Clean table rows must not trigger any findings."""
        line = "| API endpoint | https://api.example.com/v1/users |"
        findings = list(scan_line_for_secrets(line, Path("docs/api.md"), 3))
        assert findings == []

    def test_scan_line_still_catches_plain_aws_key(self) -> None:
        """Normalizer must not break detection of non-obfuscated secrets."""
        line = "aws_key = AKIA1234567890ABCDEF"
        findings = list(scan_line_for_secrets(line, Path("docs/config.md"), 1))
        assert len(findings) >= 1
        assert findings[0].secret_type == "aws-access-key"

    def test_no_duplicate_findings_for_same_secret(self) -> None:
        """If raw and normalised both match, only ONE finding is emitted per type."""
        # This line has the key both raw AND in a table — should only emit once
        line = "AKIA1234567890ABCDEF"
        findings = list(scan_line_for_secrets(line, Path("docs/x.md"), 1))
        types = [f.secret_type for f in findings]
        assert types.count("aws-access-key") == 1, "Deduplication must prevent double-emit"


# ─── ZRT-004: VSMBrokenLinkRule context-aware URL resolution ──────────────────


def _make_vsm(*urls: str, status: str = "REACHABLE") -> dict[str, Route]:
    return {
        url: Route(url=url, source=f"{url.strip('/')}.md", status=status)  # type: ignore[arg-type]
        for url in urls
    }


class TestVSMContextAwareResolution:
    """ZRT-004: VSMBrokenLinkRule must resolve relative .. hrefs from the source dir."""

    _RULE = VSMBrokenLinkRule()
    _DOCS_ROOT = Path("/docs")

    def _ctx(self, source_rel: str) -> ResolutionContext:
        """Build a context for a source file inside /docs."""
        return ResolutionContext(
            docs_root=self._DOCS_ROOT,
            source_file=self._DOCS_ROOT / source_rel,
        )

    def _run_with_ctx(self, text: str, vsm: dict, source_rel: str) -> list[Violation]:
        ctx = self._ctx(source_rel)
        return self._RULE.check_vsm(self._DOCS_ROOT / source_rel, text, vsm, {}, ctx)

    def test_context_aware_resolves_dotdot_to_sibling(self) -> None:
        """../../c/target.md from docs/a/b/page.md → /c/target/."""
        vsm = _make_vsm("/c/target/")
        violations = self._run_with_ctx("[T](../../c/target.md)", vsm, "a/b/page.md")
        assert violations == [], "Link ../../c/target.md from docs/a/b/ must resolve to /c/target/"

    def test_context_aware_single_dotdot(self) -> None:
        """../sibling.md from docs/subdir/page.md → /sibling/."""
        vsm = _make_vsm("/sibling/")
        violations = self._run_with_ctx("[Sibling](../sibling.md)", vsm, "subdir/page.md")
        assert violations == [], "Link ../sibling.md from docs/subdir/ must resolve to /sibling/"

    def test_context_aware_dotdot_absent_from_vsm_emits_violation(self) -> None:
        """A context-resolved link to an absent URL must still emit Z001."""
        vsm = _make_vsm("/other/")  # /sibling/ is absent
        violations = self._run_with_ctx("[Broken](../sibling.md)", vsm, "subdir/page.md")
        assert len(violations) == 1
        assert violations[0].code == "Z001"

    def test_context_aware_traversal_escape_returns_none(self) -> None:
        """A path that escapes docs_root via .. must be silently skipped (no crash)."""
        vsm = _make_vsm("/etc/")
        violations = self._run_with_ctx("[Escape](../../../../etc/passwd)", vsm, "subdir/page.md")
        # The path escapes docs_root — must not emit a false Z001 nor crash
        assert violations == []

    def test_without_context_preserves_backward_compatibility(self) -> None:
        """Without context, behaviour is identical to the original @staticmethod."""
        vsm = _make_vsm("/guide/")
        # docs/guide.md with no context → should still work as before
        violations = self._RULE.check_vsm(
            Path("docs/index.md"),
            "[Guide](guide.md)",
            vsm,
            {},
            context=None,  # explicit None
        )
        assert violations == []

    def test_context_aware_index_md_resolves_to_dir(self) -> None:
        """../section/index.md from docs/a/page.md → /section/."""
        vsm = _make_vsm("/section/")
        violations = self._run_with_ctx("[Sec](../section/index.md)", vsm, "a/page.md")
        assert violations == []

    def test_run_vsm_passes_context_to_rule(self) -> None:
        """AdaptiveRuleEngine.run_vsm must forward the context to check_vsm."""
        engine = AdaptiveRuleEngine([VSMBrokenLinkRule()])
        vsm = _make_vsm("/sibling/")
        ctx = ResolutionContext(
            docs_root=Path("/docs"),
            source_file=Path("/docs/subdir/page.md"),
        )
        # ../sibling.md from /docs/subdir/page.md → /sibling/
        findings = engine.run_vsm(
            Path("/docs/subdir/page.md"),
            "[Sibling](../sibling.md)",
            vsm,
            {},
            context=ctx,
        )
        assert findings == [], f"Expected no findings with context, got: {findings}"
