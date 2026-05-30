# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for Suppression Debt scoring logic (ADR-061).

Validates the flat-cost debt model (ADR-031 breaking change): every suppression
deducts exactly 1 point from the DQS regardless of ``suppression_cap``.
``suppression_cap`` is a hard-fail threshold, not a free allowance.
"""

from __future__ import annotations

from zenzic.core.scorer import compute_score


# ─── Base: no suppressions ────────────────────────────────────────────────────


def test_zero_suppressions_no_debt() -> None:
    """Zero suppressions → suppression_debt_pts is 0, score unaffected."""
    report = compute_score({}, suppression_count=0)
    assert report.suppression_debt_pts == 0
    assert report.suppression_count == 0
    assert report.suppression_cap == 30
    assert report.debt_status == "CLEAN"
    assert report.score == 100


# ─── Flat-cost model: every suppression costs 1 pt ─────────────────────────


def test_single_suppression_within_cap_costs_one_point() -> None:
    """Each suppression costs 1 pt flat, even when below cap."""
    report = compute_score({}, suppression_count=1)
    assert report.suppression_debt_pts == 1
    assert report.debt_status == "MANAGED"
    assert report.score == 99


def test_ten_suppressions_within_cap_cost_ten_points() -> None:
    """10 suppressions (within cap=30) cost 10 pts flat."""
    report = compute_score({}, suppression_count=10)
    assert report.suppression_debt_pts == 10
    assert report.score == 90


def test_at_cap_costs_thirty_points() -> None:
    """Suppressions exactly at cap still cost 1 pt each (no free allowance)."""
    report = compute_score({}, suppression_count=30)
    assert report.suppression_debt_pts == 30
    assert report.score == 70


# ─── Beyond-cap still costs flat-rate (cap is a hard-fail threshold only) ─────


def test_one_suppression_beyond_cap_costs_thirty_one_points() -> None:
    """31 suppressions with cap=30 → 31 debt points (flat-cost, not excess-only)."""
    report = compute_score({}, suppression_count=31)
    assert report.suppression_debt_pts == 31
    assert report.debt_status == "CRITICAL"
    assert report.score == 69


def test_five_suppressions_beyond_cap() -> None:
    """35 suppressions with cap=30 → 35 debt points."""
    report = compute_score({}, suppression_count=35)
    assert report.suppression_debt_pts == 35
    assert report.score == 65


def test_excess_suppressions_cannot_go_below_zero() -> None:
    """Extreme suppression debt cannot make score negative."""
    report = compute_score({}, suppression_count=200)
    assert report.score == 0


# ─── Combined: violations + suppressions ─────────────────────────────────────


def test_violations_and_suppressions_stack() -> None:
    """Suppression debt is applied after bucket deductions.

    Z503 × 1 = 10 pts from content (cap 20) → score 90 before debt.
    5 suppressions cost 5 pts flat → final score 85.
    """
    report = compute_score({"Z503": 1}, suppression_count=5)
    assert report.suppression_debt_pts == 5
    assert report.score == 85


def test_gravity_cap_then_debt_applied() -> None:
    """Gravity Cap fires first, then suppression debt reduces further.

    11 × Z601 → governance escalation → brand = 0 → Gravity Cap → max 70.
    Then 5 suppressions cost 5 pts flat → final score 65.
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


def test_custom_cap_changes_debt_threshold() -> None:
    """A project with suppression_cap=10 still costs 1 pt per suppression (flat-cost)."""
    # 15 suppressions: flat-cost = 15 pts (cap only affects hard-fail threshold)
    report = compute_score({}, suppression_count=15, suppression_cap=10)
    assert report.suppression_debt_pts == 15
    assert report.debt_status == "CRITICAL"
    assert report.score == 85


def test_zero_cap_all_suppressions_cost_one_each() -> None:
    """suppression_cap=0 → every suppression costs 1 pt flat."""
    report = compute_score({}, suppression_count=5, suppression_cap=0)
    assert report.suppression_debt_pts == 5
    assert report.score == 95


def test_raised_cap_marks_extended_debt_status() -> None:
    """CAP above sovereign default marks debt posture as EXTENDED."""
    report = compute_score({}, suppression_count=5, suppression_cap=45)
    assert report.suppression_debt_pts == 5
    assert report.debt_status == "EXTENDED"
    assert report.score == 95


# ─── ScoreReport.to_dict() ───────────────────────────────────────────────────


def test_debt_pts_in_to_dict_when_nonzero() -> None:
    """suppression_debt_pts appears in to_dict() output when > 0."""
    report = compute_score({}, suppression_count=35)
    d = report.to_dict()
    assert "suppression_debt_pts" in d
    assert d["suppression_debt_pts"] == 35


def test_debt_pts_present_in_to_dict_when_zero() -> None:
    """suppression_debt_pts is always present for machine-contract stability."""
    report = compute_score({})
    d = report.to_dict()
    assert "suppression_debt_pts" in d
    assert d["suppression_debt_pts"] == 0
    assert d["suppression_count"] == 0
    assert d["suppression_cap"] == 30
    assert d["debt_status"] == "CLEAN"
