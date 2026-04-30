# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Documentation quality scoring engine.

Computes a deterministic 0–100 score from the results of all Zenzic checks.
Each category carries a fixed weight; per-code penalties are deducted up to a
category cap so that minor issues never collapse the entire score.

Quartz Weight Matrix (CEO-149/163)
-----------------------------------
- structural:   40 pts   Z101, Z102, Z104, Z105, Z106, Z107 — Structural Integrity
- content:      30 pts   Z501, Z502, Z503, Z505 — Content Excellence
- navigation:   20 pts   Z402 (Z401 is INFO — immune) — Navigation & SEO
- brand:        10 pts   Z903, Z904, Z905 — Brand & Assets

Scoring formula: total = Σ max(0, cap_i − Σ penalty_code × count_code)

Category Cap Invariant (CEO-163):
  1000 × Z505 (1.0 pt each) caps the content category at 30 pts deducted,
  leaving structural (40) + navigation (20) + brand (10) = 70 / 100.

Security Override (Zero-Tolerance Floor)
-----------------------------------------
If any Z2xx finding is present, the score collapses to 0 unconditionally.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from zenzic.core.exceptions import ConfigurationError


# ─── Weights ──────────────────────────────────────────────────────────────────

_WEIGHTS: dict[str, float] = {
    "structural": 0.40,  # Z101, Z102, Z104, Z105, Z107 — Structural Integrity
    "content": 0.30,  # Z501, Z502, Z503, Z505 — Content Excellence
    "navigation": 0.20,  # Z402 (Z401 is INFO — immune) — Navigation & SEO
    "brand": 0.10,  # Z903, Z904, Z905 — Brand & Assets
}

# ─── Quartz Penalty Table (CEO-163/170) ─────────────────────────────────────
# Points deducted per occurrence of each finding code.
# Category cap = weight × 100  (e.g. structural cap = 40 pts).
# Formula per category:  max(0, cap − Σ penalty_i × count_i)
_CODE_PENALTY: dict[str, float] = {
    # Structural Integrity (cap = 40 pts)
    "Z101": 8.0,  # LINK_BROKEN
    "Z102": 5.0,  # ANCHOR_MISSING
    "Z104": 8.0,  # FILE_NOT_FOUND
    "Z105": 2.0,  # ABSOLUTE_PATH
    "Z106": 1.0,  # CIRCULAR_LINK (validator-level)
    "Z107": 1.0,  # CIRCULAR_ANCHOR (rule-engine level)
    # Content Excellence (cap = 30 pts)
    "Z501": 2.0,  # PLACEHOLDER — TODO / stub patterns
    "Z502": 1.0,  # SHORT_CONTENT — below minimum word count
    "Z503": 10.0,  # SNIPPET_ERROR — syntax error in code block
    "Z505": 1.0,  # UNTAGGED_CODE_BLOCK
    # Navigation & SEO (cap = 20 pts)
    "Z402": 4.0,  # ORPHAN_PAGE
    # Brand & Assets (cap = 10 pts)
    "Z903": 3.0,  # UNUSED_ASSET
    "Z904": 2.0,  # DISCOVERY_ERROR (nav contract violation)
    "Z905": 3.0,  # BRAND_OBSOLESCENCE
}

_CODE_CATEGORY: dict[str, str] = {
    "Z101": "structural",
    "Z102": "structural",
    "Z104": "structural",
    "Z105": "structural",
    "Z106": "structural",
    "Z107": "structural",
    "Z501": "content",
    "Z502": "content",
    "Z503": "content",
    "Z505": "content",
    "Z402": "navigation",
    "Z903": "brand",
    "Z904": "brand",
    "Z905": "brand",
}

# Z2xx codes trigger the Security Override — score collapses to 0.
_SECURITY_CODES: frozenset[str] = frozenset({"Z201", "Z202", "Z203"})


# ─── Data structures ──────────────────────────────────────────────────────────


@dataclass
class CategoryScore:
    """Score and issue count for a single check category."""

    name: str
    weight: float
    issues: int
    category_score: float  # 0.0–1.0 before weight is applied
    contribution: float  # category_score * weight


@dataclass
class ScoreReport:
    """Full scoring report produced by :func:`compute_score`."""

    score: int  # 0–100 (rounded)
    threshold: int = 0  # fail_under value at save time; 0 means no threshold
    security_override: bool = False  # True when score collapsed to 0 by a security violation
    categories: list[CategoryScore] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        if self.security_override:
            status = "security_breach"
        elif self.score >= self.threshold:
            status = "success"
        else:
            status = "failing"
        d: dict[str, object] = {
            "project": "zenzic",
            "score": self.score,
            "threshold": self.threshold,
            "status": status,
            "timestamp": datetime.now(tz=UTC).isoformat(timespec="seconds"),
            "categories": [asdict(c) for c in self.categories],
        }
        if self.security_override:
            d["security_override"] = True
        return d


# ─── Pure scoring logic ───────────────────────────────────────────────────────


def compute_score(findings_counts: dict[str, int]) -> ScoreReport:
    """Compute a 0–100 documentation quality score using the Quartz Penalty Table.

    Each finding code carries a per-occurrence point deduction.  Deductions are
    accumulated per category and capped at the category's maximum contribution
    (Structural 40, Content 30, Navigation 20, Brand 10).  Total score is the
    sum of remaining category points (0–100).

    Security Override: any Z2xx finding collapses the score to 0 unconditionally.

    Category Cap Invariant (CEO-163): 1 000 occurrences of Z505 (1.0 pt each)
    cap out the content category at 30 pts deducted, leaving structural (40)
    + navigation (20) + brand (10) = **70 / 100**.

    Args:
        findings_counts: Mapping of ``Zxxx`` code → occurrence count.
            Unknown codes contribute zero deduction.

    Returns:
        A :class:`ScoreReport` with the total 0–100 score and per-category breakdown.
    """
    # Security override: any Z2xx finding collapses the score to 0.
    if any(findings_counts.get(code, 0) > 0 for code in _SECURITY_CODES):
        categories = [
            CategoryScore(name=n, weight=w, issues=0, category_score=0.0, contribution=0.0)
            for n, w in _WEIGHTS.items()
        ]
        return ScoreReport(score=0, security_override=True, categories=categories)

    categories: list[CategoryScore] = []  # type: ignore[no-redef]
    total_pts = 0.0

    for name, weight in _WEIGHTS.items():
        cap_pts = weight * 100  # e.g. structural: 40.0
        deduction = sum(
            _CODE_PENALTY.get(code, 0.0) * count
            for code, count in findings_counts.items()
            if _CODE_CATEGORY.get(code) == name and count > 0
        )
        cat_pts = max(0.0, cap_pts - deduction)
        cat_score_norm = cat_pts / cap_pts  # 0.0–1.0
        issues = sum(
            count
            for code, count in findings_counts.items()
            if _CODE_CATEGORY.get(code) == name and count > 0
        )
        total_pts += cat_pts
        categories.append(
            CategoryScore(
                name=name,
                weight=weight,
                issues=issues,
                category_score=round(cat_score_norm, 4),
                contribution=round(cat_pts / 100, 4),
            )
        )

    return ScoreReport(score=round(total_pts), categories=categories)


# ─── Snapshot persistence ─────────────────────────────────────────────────────

_SNAPSHOT_FILENAME = ".zenzic-score.json"


def save_snapshot(repo_root: Path, report: ScoreReport) -> Path:
    """Write the score report to ``.zenzic-score.json`` in *repo_root*.

    Returns the path to the written file.
    """
    snapshot_path = repo_root / _SNAPSHOT_FILENAME
    data = report.to_dict()
    data["schema_version"] = 2  # D092 — Quartz Penalty Scorer
    snapshot_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return snapshot_path


def load_snapshot(repo_root: Path) -> ScoreReport | None:
    """Read the last saved score report from *repo_root*.

    Returns ``None`` if no snapshot file is present or the file cannot be parsed.
    Raises ``ConfigurationError`` if the snapshot was written by Zenzic v0.6.x
    (decay model, schema_version < 2) and is incompatible with the Quartz scorer.
    """
    snapshot_path = repo_root / _SNAPSHOT_FILENAME
    if not snapshot_path.is_file():
        return None
    try:
        data = json.loads(snapshot_path.read_text(encoding="utf-8"))
        if data.get("schema_version", 1) < 2:
            raise ConfigurationError(
                "Incompatible baseline (v0.6.x decay model). "
                "Run 'zenzic score --save' to create a Quartz Maturity baseline."
            )
        categories = [CategoryScore(**c) for c in data.get("categories", [])]
        score = int(data.get("score", 0))
        threshold = int(data.get("threshold", 0))
        return ScoreReport(score=score, threshold=threshold, categories=categories)
    except ConfigurationError:
        raise
    except Exception:
        return None
