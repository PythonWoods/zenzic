# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for the scoring engine and CLI score / diff commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from zenzic.core.exceptions import ConfigurationError
from zenzic.core.scorer import (
    ScoreReport,
    compute_score,
    load_snapshot,
    save_snapshot,
)
from zenzic.core.validator import LinkError
from zenzic.main import app
from zenzic.models.config import ZenzicConfig


runner = CliRunner()

_CFG = ZenzicConfig()


# ─── compute_score — pure unit tests (Quartz Penalty API, CEO-163) ─────────────


def test_perfect_score() -> None:
    report = compute_score({})
    assert report.score == 100


def test_score_drops_with_issues() -> None:
    # 5 broken links: 5 × 8.0 = 40 pts from structural cap (40) → structural=0; total=60
    report = compute_score({"Z101": 5})
    assert report.score < 100


def test_score_is_zero_with_many_issues() -> None:
    report = compute_score({"Z101": 10, "Z402": 10, "Z503": 10, "Z903": 10})
    assert report.score == 0


def test_score_is_bounded_0_to_100() -> None:
    report = compute_score({"Z101": 100, "Z402": 100, "Z503": 100, "Z903": 100})
    assert 0 <= report.score <= 100


def test_score_four_categories() -> None:
    report = compute_score({})
    names = {c.name for c in report.categories}
    assert names == {"structural", "content", "navigation", "brand"}


def test_weights_sum_to_one() -> None:
    report = compute_score({})
    total_weight = sum(c.weight for c in report.categories)
    assert abs(total_weight - 1.0) < 1e-9


def test_single_link_error_drops_structural_category() -> None:
    report = compute_score({"Z101": 1})
    structural_cat = next(c for c in report.categories if c.name == "structural")
    assert structural_cat.category_score < 1.0
    assert structural_cat.issues == 1


def test_circular_anchors_counted_in_structural() -> None:
    report = compute_score({"Z107": 2})
    structural_cat = next(c for c in report.categories if c.name == "structural")
    assert structural_cat.issues == 2
    assert structural_cat.category_score < 1.0


def test_untagged_blocks_counted_in_content() -> None:
    report = compute_score({"Z505": 3})
    content_cat = next(c for c in report.categories if c.name == "content")
    assert content_cat.issues == 3


def test_brand_violations_counted_in_brand() -> None:
    report = compute_score({"Z905": 2})
    brand_cat = next(c for c in report.categories if c.name == "brand")
    assert brand_cat.issues == 2
    assert brand_cat.category_score < 1.0


def test_nav_contract_errors_counted_in_brand() -> None:
    report = compute_score({"Z904": 1, "Z905": 1})
    brand_cat = next(c for c in report.categories if c.name == "brand")
    assert brand_cat.issues == 2


def test_security_override_collapses_score_to_zero() -> None:
    """Security violations override all other checks: score must be 0."""
    report = compute_score({"Z201": 1})
    assert report.score == 0
    assert report.security_override is True


def test_security_override_ignores_perfect_checks() -> None:
    """Even a perfectly clean project scores 0 when a credential is detected."""
    report = compute_score({"Z201": 1})
    assert report.score == 0
    assert report.security_override is True


def test_security_override_multiple_violations() -> None:
    report = compute_score({"Z201": 3})
    assert report.score == 0
    assert report.security_override is True


def test_no_security_override_when_zero_violations() -> None:
    report = compute_score({})
    assert report.security_override is False


# ─── Quartz Penalty Table invariants (CEO-163) ────────────────────────────────


def test_z505_category_cap_invariant() -> None:
    """CEO-163 invariant: 1000 Z505 caps content; structural+nav+brand intact → 70."""
    report = compute_score({"Z505": 1000})
    assert report.score == 70
    content_cat = next(c for c in report.categories if c.name == "content")
    assert content_cat.category_score == 0.0


def test_z503_single_snippet_error() -> None:
    """One snippet error = 10pt deduction from content cap (30 → 20)."""
    report = compute_score({"Z503": 1})
    assert report.score == 90
    content_cat = next(c for c in report.categories if c.name == "content")
    assert abs(content_cat.category_score - (20 / 30)) < 1e-3


def test_z101_penalty_five_broken_links() -> None:
    """5 broken links: 5 × 8 = 40 → structural zeroed, total = 60."""
    report = compute_score({"Z101": 5})
    assert report.score == 60
    structural_cat = next(c for c in report.categories if c.name == "structural")
    assert structural_cat.category_score == 0.0


def test_z501_z502_split_penalty() -> None:
    """Z501 (2.0pt) and Z502 (1.0pt) have distinct weights (CEO-171)."""
    r_z501 = compute_score({"Z501": 1})
    r_z502 = compute_score({"Z502": 1})
    assert r_z501.score < r_z502.score


def test_z402_orphan_navigation_penalty() -> None:
    """Z402 deducts from navigation (cap=20). 5 orphans × 4.0 = 20 → nav zeroed."""
    report = compute_score({"Z402": 5})
    nav_cat = next(c for c in report.categories if c.name == "navigation")
    assert nav_cat.category_score == 0.0
    assert report.score == 80  # structural(40) + content(30) + brand(10) = 80


def test_unknown_code_contributes_zero_deduction() -> None:
    """Unknown Zxxx codes are silently ignored (no deduction)."""
    report = compute_score({"Z999": 100})
    assert report.score == 100


def test_to_dict_structure() -> None:
    # Z101:1 → struct 32; Z503:2 → content 10; Z903:1 → brand 7; nav 20 → total 69
    report = compute_score({"Z101": 1, "Z503": 2, "Z903": 1})
    d = report.to_dict()
    assert d["project"] == "zenzic"
    assert "score" in d
    assert "threshold" in d
    assert d["status"] in ("success", "failing", "security_breach")
    assert "timestamp" in d
    assert "categories" in d
    assert len(d["categories"]) == 4
    for cat in d["categories"]:
        assert "name" in cat
        assert "issues" in cat
        assert "weight" in cat
        assert "category_score" in cat
        assert "contribution" in cat


def test_to_dict_security_override_status() -> None:
    report = compute_score({"Z201": 1})
    d = report.to_dict()
    assert d["status"] == "security_breach"
    assert d["security_override"] is True
    assert d["score"] == 0


# ─── Snapshot persistence ─────────────────────────────────────────────────────


def test_save_and_load_snapshot(tmp_path: Path) -> None:
    report = compute_score({"Z402": 1, "Z501": 2})
    saved_path = save_snapshot(tmp_path, report)
    assert saved_path.exists()

    loaded = load_snapshot(tmp_path)
    assert loaded is not None
    assert loaded.score == report.score
    assert len(loaded.categories) == len(report.categories)


def test_load_snapshot_returns_none_when_missing(tmp_path: Path) -> None:
    assert load_snapshot(tmp_path) is None


def test_load_snapshot_returns_none_on_corrupt_file(tmp_path: Path) -> None:
    (tmp_path / ".zenzic-score.json").write_text("not json", encoding="utf-8")
    assert load_snapshot(tmp_path) is None


def test_load_snapshot_raises_on_legacy_schema(tmp_path: Path) -> None:
    """A v0.6.x snapshot (schema_version absent → 1) must raise ConfigurationError.

    Protects against silently loading an incompatible decay-model baseline and
    producing a meaningless diff result.
    """
    legacy = {"score": 85, "threshold": 70, "categories": [], "status": "success"}
    (tmp_path / ".zenzic-score.json").write_text(json.dumps(legacy), encoding="utf-8")
    import pytest

    with pytest.raises(ConfigurationError, match="Incompatible baseline"):
        load_snapshot(tmp_path)


def test_save_snapshot_writes_schema_version(tmp_path: Path) -> None:
    """save_snapshot must stamp schema_version=2 so future guards can detect mismatches."""
    report = compute_score({"Z101": 1})
    save_snapshot(tmp_path, report)
    data = json.loads((tmp_path / ".zenzic-score.json").read_text(encoding="utf-8"))
    assert data.get("schema_version") == 2


def test_snapshot_roundtrip_preserves_categories(tmp_path: Path) -> None:
    report = compute_score({"Z101": 2, "Z402": 1, "Z501": 3, "Z903": 1})
    save_snapshot(tmp_path, report)
    loaded = load_snapshot(tmp_path)
    assert loaded is not None
    original_names = [c.name for c in report.categories]
    loaded_names = [c.name for c in loaded.categories]
    assert original_names == loaded_names


# ─── CLI: zenzic score ────────────────────────────────────────────────────────


def _mock_all_checks_empty(
    repo_root: Path,
    docs_root: Path,
    config: object,
    exclusion_mgr: object,
    strict: bool,
) -> ScoreReport:
    return compute_score({})


def _mock_all_checks_with_issues(
    repo_root: Path,
    docs_root: Path,
    config: object,
    exclusion_mgr: object,
    strict: bool,
) -> ScoreReport:
    # structural: 2×8=16 → 24pts; content: 1×10+3×2=16 → 14pts; nav: 1×4=4 → 16pts; brand: 1×3=3 → 7pts → score=61
    return compute_score({"Z101": 2, "Z402": 1, "Z503": 1, "Z501": 3, "Z903": 1})


@patch("zenzic.cli._standalone.find_repo_root")
@patch("zenzic.cli._standalone.ZenzicConfig.load")
@patch("zenzic.cli._standalone._run_all_checks", side_effect=_mock_all_checks_empty)
def test_score_text_perfect(mock_run, mock_load, mock_root, tmp_path: Path) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    result = runner.invoke(app, ["score"])
    assert result.exit_code == 0
    assert "100/100" in result.stdout


@patch("zenzic.cli._standalone.find_repo_root")
@patch("zenzic.cli._standalone.ZenzicConfig.load")
@patch("zenzic.cli._standalone._run_all_checks", side_effect=_mock_all_checks_empty)
def test_score_json_output(mock_run, mock_load, mock_root, tmp_path: Path) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    result = runner.invoke(app, ["score", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["score"] == 100
    assert data["project"] == "zenzic"
    assert data["status"] == "success"
    assert "timestamp" in data
    assert len(data["categories"]) == 4


@patch("zenzic.cli._standalone.find_repo_root")
@patch("zenzic.cli._standalone.ZenzicConfig.load")
@patch("zenzic.cli._standalone._run_all_checks", side_effect=_mock_all_checks_empty)
def test_score_save_creates_snapshot(mock_run, mock_load, mock_root, tmp_path: Path) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    result = runner.invoke(app, ["score", "--save"])
    assert result.exit_code == 0
    assert (tmp_path / ".zenzic-score.json").exists()


@patch("zenzic.cli._standalone.find_repo_root")
@patch("zenzic.cli._standalone.ZenzicConfig.load")
@patch("zenzic.cli._standalone._run_all_checks", side_effect=_mock_all_checks_with_issues)
def test_score_fail_under_triggers(mock_run, mock_load, mock_root, tmp_path: Path) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    result = runner.invoke(app, ["score", "--fail-under", "90"])
    assert result.exit_code == 1


@patch("zenzic.cli._standalone.find_repo_root")
@patch("zenzic.cli._standalone.ZenzicConfig.load")
@patch("zenzic.cli._standalone._run_all_checks", side_effect=_mock_all_checks_empty)
def test_score_fail_under_passes_when_above(mock_run, mock_load, mock_root, tmp_path: Path) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    result = runner.invoke(app, ["score", "--fail-under", "50"])
    assert result.exit_code == 0


# ─── CLI: zenzic diff ─────────────────────────────────────────────────────────


@patch("zenzic.cli._standalone.find_repo_root")
@patch("zenzic.cli._standalone.ZenzicConfig.load")
def test_diff_no_snapshot_exits_1(mock_load, mock_root, tmp_path: Path) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    result = runner.invoke(app, ["diff"])
    assert result.exit_code == 1
    assert "no snapshot" in result.stdout.lower()


@patch("zenzic.cli._standalone.find_repo_root")
@patch("zenzic.cli._standalone.ZenzicConfig.load")
@patch("zenzic.cli._standalone._run_all_checks", side_effect=_mock_all_checks_empty)
def test_diff_no_regression(mock_run, mock_load, mock_root, tmp_path: Path) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    # Save a baseline identical to what _run_all_checks returns
    baseline = compute_score({})
    save_snapshot(tmp_path, baseline)

    result = runner.invoke(app, ["diff"])
    assert result.exit_code == 0
    assert "100" in result.stdout


@patch("zenzic.cli._standalone.find_repo_root")
@patch("zenzic.cli._standalone.ZenzicConfig.load")
@patch("zenzic.cli._standalone._run_all_checks", side_effect=_mock_all_checks_with_issues)
def test_diff_regression_detected(mock_run, mock_load, mock_root, tmp_path: Path) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    # Baseline is perfect, current has issues → regression
    baseline = compute_score({})
    save_snapshot(tmp_path, baseline)

    result = runner.invoke(app, ["diff"])
    assert result.exit_code == 1
    assert "REGRESSION" in result.stdout


@patch("zenzic.cli._standalone.find_repo_root")
@patch("zenzic.cli._standalone.ZenzicConfig.load")
@patch("zenzic.cli._standalone._run_all_checks", side_effect=_mock_all_checks_with_issues)
def test_diff_threshold_suppresses_exit(mock_run, mock_load, mock_root, tmp_path: Path) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    baseline = compute_score({})
    save_snapshot(tmp_path, baseline)

    # With a very high threshold, no regression is flagged
    result = runner.invoke(app, ["diff", "--threshold", "100"])
    assert result.exit_code == 0


@patch("zenzic.cli._standalone.find_repo_root")
@patch("zenzic.cli._standalone.ZenzicConfig.load")
@patch("zenzic.cli._standalone._run_all_checks", side_effect=_mock_all_checks_with_issues)
def test_diff_json_output(mock_run, mock_load, mock_root, tmp_path: Path) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    baseline = compute_score({})
    save_snapshot(tmp_path, baseline)

    result = runner.invoke(app, ["diff", "--format", "json", "--threshold", "100"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "baseline" in data
    assert "current" in data
    assert "delta" in data
    assert data["delta"] < 0  # score went down


# ─── CLI: check all --exit-zero ───────────────────────────────────────────────


@patch("zenzic.cli._shared._count_docs_assets", return_value=(5, 0))
@patch("zenzic.cli._check.find_repo_root")
@patch("zenzic.cli._check.ZenzicConfig.load")
@patch(
    "zenzic.cli._check.validate_links_structured",
    return_value=[LinkError(file_path=Path("docs/x.md"), line_no=1, message="broken link")],
)
@patch("zenzic.cli._check.find_orphans", return_value=[])
@patch("zenzic.cli._check.validate_snippets", return_value=[])
@patch("zenzic.cli._check.find_placeholders", return_value=[])
@patch("zenzic.cli._check.find_unused_assets", return_value=[])
@patch("zenzic.cli._check.check_nav_contract", return_value=[])
@patch("zenzic.cli._check.scan_docs_references", return_value=([], []))
def test_check_all_exit_zero_with_failures(
    _refs,
    _nav,
    mock_assets,
    mock_placeholders,
    mock_snippets,
    mock_orphans,
    mock_links,
    mock_load,
    mock_root,
    _count,
    tmp_path: Path,
) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    result = runner.invoke(app, ["check", "all", "--exit-zero"])
    assert result.exit_code == 0
    assert "FAILED" in result.stdout  # report is printed but exit is 0


@patch("zenzic.cli._check.find_repo_root")
@patch("zenzic.cli._check.ZenzicConfig.load")
@patch(
    "zenzic.cli._check.validate_links_structured",
    return_value=[LinkError(file_path=Path("docs/x.md"), line_no=1, message="broken link")],
)
@patch("zenzic.cli._check.find_orphans", return_value=[])
@patch("zenzic.cli._check.validate_snippets", return_value=[])
@patch("zenzic.cli._check.find_placeholders", return_value=[])
@patch("zenzic.cli._check.find_unused_assets", return_value=[])
@patch("zenzic.cli._check.check_nav_contract", return_value=[])
@patch("zenzic.cli._check.scan_docs_references", return_value=([], []))
def test_check_all_exit_zero_json(
    _refs,
    _nav,
    mock_assets,
    mock_placeholders,
    mock_snippets,
    mock_orphans,
    mock_links,
    mock_load,
    mock_root,
    tmp_path: Path,
) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    result = runner.invoke(app, ["check", "all", "--exit-zero", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert len(data["links"]) == 1
