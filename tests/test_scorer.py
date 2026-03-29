# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for the scoring engine and CLI score / diff commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from zenzic.core.scorer import (
    ScoreReport,
    compute_score,
    load_snapshot,
    save_snapshot,
)
from zenzic.main import app
from zenzic.models.config import ZenzicConfig


runner = CliRunner()

_CFG = ZenzicConfig()


# ─── compute_score — pure unit tests ──────────────────────────────────────────


def test_perfect_score() -> None:
    report = compute_score(
        link_errors=0, orphans=0, snippet_errors=0, placeholders=0, unused_assets=0
    )
    assert report.score == 100


def test_score_drops_with_issues() -> None:
    report = compute_score(
        link_errors=5, orphans=0, snippet_errors=0, placeholders=0, unused_assets=0
    )
    assert report.score < 100


def test_score_is_zero_with_many_issues() -> None:
    report = compute_score(
        link_errors=10, orphans=10, snippet_errors=10, placeholders=10, unused_assets=10
    )
    assert report.score == 0


def test_score_is_bounded_0_to_100() -> None:
    report = compute_score(
        link_errors=100, orphans=100, snippet_errors=100, placeholders=100, unused_assets=100
    )
    assert 0 <= report.score <= 100


def test_score_five_categories() -> None:
    report = compute_score(
        link_errors=0, orphans=0, snippet_errors=0, placeholders=0, unused_assets=0
    )
    names = {c.name for c in report.categories}
    assert names == {"links", "orphans", "snippets", "placeholders", "assets"}


def test_weights_sum_to_one() -> None:
    report = compute_score(
        link_errors=0, orphans=0, snippet_errors=0, placeholders=0, unused_assets=0
    )
    total_weight = sum(c.weight for c in report.categories)
    assert abs(total_weight - 1.0) < 1e-9


def test_single_link_error_drops_links_category() -> None:
    report = compute_score(
        link_errors=1, orphans=0, snippet_errors=0, placeholders=0, unused_assets=0
    )
    links_cat = next(c for c in report.categories if c.name == "links")
    assert links_cat.category_score < 1.0
    assert links_cat.issues == 1


def test_to_dict_structure() -> None:
    report = compute_score(
        link_errors=1, orphans=0, snippet_errors=2, placeholders=0, unused_assets=1
    )
    d = report.to_dict()
    assert d["project"] == "zenzic"
    assert "score" in d
    assert "threshold" in d
    assert d["status"] in ("success", "failing")
    assert "timestamp" in d
    assert "categories" in d
    assert len(d["categories"]) == 5
    for cat in d["categories"]:
        assert "name" in cat
        assert "issues" in cat
        assert "weight" in cat
        assert "category_score" in cat
        assert "contribution" in cat


# ─── Snapshot persistence ─────────────────────────────────────────────────────


def test_save_and_load_snapshot(tmp_path: Path) -> None:
    report = compute_score(
        link_errors=0, orphans=1, snippet_errors=0, placeholders=2, unused_assets=0
    )
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


def test_snapshot_roundtrip_preserves_categories(tmp_path: Path) -> None:
    report = compute_score(
        link_errors=2, orphans=1, snippet_errors=0, placeholders=3, unused_assets=1
    )
    save_snapshot(tmp_path, report)
    loaded = load_snapshot(tmp_path)
    assert loaded is not None
    original_names = [c.name for c in report.categories]
    loaded_names = [c.name for c in loaded.categories]
    assert original_names == loaded_names


# ─── CLI: zenzic score ────────────────────────────────────────────────────────


def _mock_all_checks_empty(repo_root: Path, config: object, strict: bool) -> ScoreReport:
    return compute_score(
        link_errors=0, orphans=0, snippet_errors=0, placeholders=0, unused_assets=0
    )


def _mock_all_checks_with_issues(repo_root: Path, config: object, strict: bool) -> ScoreReport:
    return compute_score(
        link_errors=2, orphans=1, snippet_errors=1, placeholders=3, unused_assets=1
    )


@patch("zenzic.cli.find_repo_root")
@patch("zenzic.cli.ZenzicConfig.load")
@patch("zenzic.cli._run_all_checks", side_effect=_mock_all_checks_empty)
def test_score_text_perfect(mock_run, mock_load, mock_root, tmp_path: Path) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    result = runner.invoke(app, ["score"])
    assert result.exit_code == 0
    assert "100/100" in result.stdout


@patch("zenzic.cli.find_repo_root")
@patch("zenzic.cli.ZenzicConfig.load")
@patch("zenzic.cli._run_all_checks", side_effect=_mock_all_checks_empty)
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
    assert len(data["categories"]) == 5


@patch("zenzic.cli.find_repo_root")
@patch("zenzic.cli.ZenzicConfig.load")
@patch("zenzic.cli._run_all_checks", side_effect=_mock_all_checks_empty)
def test_score_save_creates_snapshot(mock_run, mock_load, mock_root, tmp_path: Path) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    result = runner.invoke(app, ["score", "--save"])
    assert result.exit_code == 0
    assert (tmp_path / ".zenzic-score.json").exists()


@patch("zenzic.cli.find_repo_root")
@patch("zenzic.cli.ZenzicConfig.load")
@patch("zenzic.cli._run_all_checks", side_effect=_mock_all_checks_with_issues)
def test_score_fail_under_triggers(mock_run, mock_load, mock_root, tmp_path: Path) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    result = runner.invoke(app, ["score", "--fail-under", "90"])
    assert result.exit_code == 1


@patch("zenzic.cli.find_repo_root")
@patch("zenzic.cli.ZenzicConfig.load")
@patch("zenzic.cli._run_all_checks", side_effect=_mock_all_checks_empty)
def test_score_fail_under_passes_when_above(mock_run, mock_load, mock_root, tmp_path: Path) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    result = runner.invoke(app, ["score", "--fail-under", "50"])
    assert result.exit_code == 0


# ─── CLI: zenzic diff ─────────────────────────────────────────────────────────


@patch("zenzic.cli.find_repo_root")
@patch("zenzic.cli.ZenzicConfig.load")
def test_diff_no_snapshot_exits_1(mock_load, mock_root, tmp_path: Path) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    result = runner.invoke(app, ["diff"])
    assert result.exit_code == 1
    assert "no snapshot" in result.stdout.lower()


@patch("zenzic.cli.find_repo_root")
@patch("zenzic.cli.ZenzicConfig.load")
@patch("zenzic.cli._run_all_checks", side_effect=_mock_all_checks_empty)
def test_diff_no_regression(mock_run, mock_load, mock_root, tmp_path: Path) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    # Save a baseline identical to what _run_all_checks returns
    baseline = compute_score(
        link_errors=0, orphans=0, snippet_errors=0, placeholders=0, unused_assets=0
    )
    save_snapshot(tmp_path, baseline)

    result = runner.invoke(app, ["diff"])
    assert result.exit_code == 0
    assert "100" in result.stdout


@patch("zenzic.cli.find_repo_root")
@patch("zenzic.cli.ZenzicConfig.load")
@patch("zenzic.cli._run_all_checks", side_effect=_mock_all_checks_with_issues)
def test_diff_regression_detected(mock_run, mock_load, mock_root, tmp_path: Path) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    # Baseline is perfect, current has issues → regression
    baseline = compute_score(
        link_errors=0, orphans=0, snippet_errors=0, placeholders=0, unused_assets=0
    )
    save_snapshot(tmp_path, baseline)

    result = runner.invoke(app, ["diff"])
    assert result.exit_code == 1
    assert "REGRESSION" in result.stdout


@patch("zenzic.cli.find_repo_root")
@patch("zenzic.cli.ZenzicConfig.load")
@patch("zenzic.cli._run_all_checks", side_effect=_mock_all_checks_with_issues)
def test_diff_threshold_suppresses_exit(mock_run, mock_load, mock_root, tmp_path: Path) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    baseline = compute_score(
        link_errors=0, orphans=0, snippet_errors=0, placeholders=0, unused_assets=0
    )
    save_snapshot(tmp_path, baseline)

    # With a very high threshold, no regression is flagged
    result = runner.invoke(app, ["diff", "--threshold", "100"])
    assert result.exit_code == 0


@patch("zenzic.cli.find_repo_root")
@patch("zenzic.cli.ZenzicConfig.load")
@patch("zenzic.cli._run_all_checks", side_effect=_mock_all_checks_with_issues)
def test_diff_json_output(mock_run, mock_load, mock_root, tmp_path: Path) -> None:
    mock_root.return_value = tmp_path
    mock_load.return_value = (_CFG, True)
    baseline = compute_score(
        link_errors=0, orphans=0, snippet_errors=0, placeholders=0, unused_assets=0
    )
    save_snapshot(tmp_path, baseline)

    result = runner.invoke(app, ["diff", "--format", "json", "--threshold", "100"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "baseline" in data
    assert "current" in data
    assert "delta" in data
    assert data["delta"] < 0  # score went down


# ─── CLI: check all --exit-zero ───────────────────────────────────────────────


@patch("zenzic.cli.find_repo_root")
@patch("zenzic.cli.ZenzicConfig.load")
@patch("zenzic.cli.validate_links", return_value=["broken link"])
@patch("zenzic.cli.find_orphans", return_value=[])
@patch("zenzic.cli.validate_snippets", return_value=[])
@patch("zenzic.cli.find_placeholders", return_value=[])
@patch("zenzic.cli.find_unused_assets", return_value=[])
def test_check_all_exit_zero_with_failures(
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
    result = runner.invoke(app, ["check", "all", "--exit-zero"])
    assert result.exit_code == 0
    assert "FAILED" in result.stdout  # report is printed but exit is 0


@patch("zenzic.cli.find_repo_root")
@patch("zenzic.cli.ZenzicConfig.load")
@patch("zenzic.cli.validate_links", return_value=["broken link"])
@patch("zenzic.cli.find_orphans", return_value=[])
@patch("zenzic.cli.validate_snippets", return_value=[])
@patch("zenzic.cli.find_placeholders", return_value=[])
@patch("zenzic.cli.find_unused_assets", return_value=[])
def test_check_all_exit_zero_json(
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
