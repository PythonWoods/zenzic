# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for Suppression Debt scoring logic (Phase 26).

Validates that active suppressions (inline zenzic:ignore + per-file config)
deduct from the final quality score, with escalation beyond the cap.
"""

from __future__ import annotations

from zenzic.core.scorer import compute_score


# ─── Base: no suppressions ────────────────────────────────────────────────────


def test_zero_suppressions_no_debt() -> None:
    """Zero suppressions → suppression_debt_pts is 0, score unaffected."""
    report = compute_score({}, suppression_count=0)
    assert report.suppression_debt_pts == 0
    assert report.score == 100


# ─── Linear tier: 1 – suppression_cap ────────────────────────────────────────


def test_single_suppression_costs_one_point() -> None:
    """Each suppression within the cap costs exactly 1 pt."""
    report = compute_score({}, suppression_count=1)
    assert report.suppression_debt_pts == 1
    assert report.score == 99


def test_ten_suppressions_cost_ten_points() -> None:
    """10 suppressions (within cap=30) → -10 pts."""
    report = compute_score({}, suppression_count=10)
    assert report.suppression_debt_pts == 10
    assert report.score == 90


def test_at_cap_costs_exactly_cap_points() -> None:
    """30 suppressions at default cap → -30 pts, score = 70."""
    report = compute_score({}, suppression_count=30)
    assert report.suppression_debt_pts == 30
    assert report.score == 70


# ─── Escalation tier: beyond cap ─────────────────────────────────────────────


def test_one_suppression_beyond_cap_costs_two_extra() -> None:
    """31 suppressions: 30 × 1 + 1 × 2 = 32 pts debt."""
    report = compute_score({}, suppression_count=31)
    assert report.suppression_debt_pts == 32
    assert report.score == 68


def test_five_suppressions_beyond_cap() -> None:
    """35 suppressions: 30 × 1 + 5 × 2 = 40 pts debt → score capped at 0."""
    report = compute_score({}, suppression_count=35)
    assert report.suppression_debt_pts == 40
    assert report.score == 60


def test_excess_suppressions_cannot_go_below_zero() -> None:
    """Extreme suppression debt cannot make score negative."""
    report = compute_score({}, suppression_count=200)
    assert report.score == 0


# ─── Combined: violations + suppressions ─────────────────────────────────────


def test_violations_and_suppressions_stack() -> None:
    """Suppression debt is applied after bucket deductions.

    Z503 × 1 = 10 pts from content (cap 20) → score 90 before debt.
    5 suppressions = 5 pts debt → final score 85.
    """
    report = compute_score({"Z503": 1}, suppression_count=5)
    assert report.suppression_debt_pts == 5
    assert report.score == 85


def test_gravity_cap_then_debt_applied() -> None:
    """Gravity Cap fires first, then suppression debt reduces further.

    11 × Z601 → governance escalation → brand = 0 → Gravity Cap → max 70.
    Then 5 suppressions → -5 pts → score 65.
    """
    report = compute_score({"Z601": 11}, suppression_count=5)
    assert report.score == 65
    assert report.suppression_debt_pts == 5


# ─── Security override ────────────────────────────────────────────────────────


def test_security_override_ignores_suppression_debt() -> None:
    """Security Gate collapses score to 0 regardless of suppression debt field."""
    report = compute_score({"Z201": 1}, suppression_count=100)
    assert report.score == 0
    assert report.security_override is True
    # suppression_debt_pts is not computed when security override fires
    assert report.suppression_debt_pts == 0


# ─── Custom cap ──────────────────────────────────────────────────────────────


def test_custom_cap_changes_escalation_threshold() -> None:
    """A project with suppression_cap=10 escalates earlier."""
    # 15 suppressions: 10 × 1 + 5 × 2 = 20 pts
    report = compute_score({}, suppression_count=15, suppression_cap=10)
    assert report.suppression_debt_pts == 20
    assert report.score == 80


def test_zero_cap_all_suppressions_double_cost() -> None:
    """suppression_cap=0 → every suppression costs 2 pts (full escalation)."""
    # 5 suppressions: 0 × 1 + 5 × 2 = 10 pts
    report = compute_score({}, suppression_count=5, suppression_cap=0)
    assert report.suppression_debt_pts == 10
    assert report.score == 90


# ─── ScoreReport.to_dict() ───────────────────────────────────────────────────


def test_debt_pts_in_to_dict_when_nonzero() -> None:
    """suppression_debt_pts appears in to_dict() output when > 0."""
    report = compute_score({}, suppression_count=5)
    d = report.to_dict()
    assert "suppression_debt_pts" in d
    assert d["suppression_debt_pts"] == 5


def test_debt_pts_absent_from_to_dict_when_zero() -> None:
    """suppression_debt_pts is omitted from to_dict() when 0 (clean reports)."""
    report = compute_score({})
    d = report.to_dict()
    assert "suppression_debt_pts" not in d
