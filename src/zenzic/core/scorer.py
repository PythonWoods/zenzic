# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Documentation quality scoring engine.

Computes a deterministic 0–100 score from the results of all five Zenzic checks.
Each category carries a fixed weight; issues are penalised with a graduated decay
function so that a single issue never drops the score to zero.

Weights
-------
- links:        35 %
- orphans:      20 %
- snippets:     20 %
- placeholders: 15 %
- assets:       10 %
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path


# ─── Weights ──────────────────────────────────────────────────────────────────

_WEIGHTS: dict[str, float] = {
    "links": 0.35,
    "orphans": 0.20,
    "snippets": 0.20,
    "placeholders": 0.15,
    "assets": 0.10,
}

# How fast the per-category score decays as issues accumulate.
# score_k(n) = max(0.0, 1.0 - n * _DECAY_RATE)  [linear decay, floor at 0]
_DECAY_RATE = 0.20


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
    categories: list[CategoryScore] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        status = "success" if self.score >= self.threshold else "failing"
        return {
            "project": "zenzic",
            "score": self.score,
            "threshold": self.threshold,
            "status": status,
            "timestamp": datetime.now(tz=UTC).isoformat(timespec="seconds"),
            "categories": [asdict(c) for c in self.categories],
        }


# ─── Pure scoring logic ───────────────────────────────────────────────────────


def _category_score(issue_count: int) -> float:
    """Return a 0.0–1.0 score for a category given its issue count.

    Uses a linear decay: each issue reduces the score by ``_DECAY_RATE``.
    The floor is 0.0 — a category cannot go negative.
    """
    return max(0.0, 1.0 - issue_count * _DECAY_RATE)


def compute_score(
    *,
    link_errors: int,
    orphans: int,
    snippet_errors: int,
    placeholders: int,
    unused_assets: int,
) -> ScoreReport:
    """Compute a weighted documentation quality score.

    All parameters are issue *counts* (non-negative integers).  The function is
    pure — it performs no I/O and has no side effects.

    Returns:
        A :class:`ScoreReport` with the total 0–100 score and per-category breakdown.
    """
    counts = {
        "links": link_errors,
        "orphans": orphans,
        "snippets": snippet_errors,
        "placeholders": placeholders,
        "assets": unused_assets,
    }

    categories: list[CategoryScore] = []
    weighted_sum = 0.0

    for name, weight in _WEIGHTS.items():
        cat_score = _category_score(counts[name])
        contribution = cat_score * weight
        weighted_sum += contribution
        categories.append(
            CategoryScore(
                name=name,
                weight=weight,
                issues=counts[name],
                category_score=round(cat_score, 4),
                contribution=round(contribution, 4),
            )
        )

    score = round(weighted_sum * 100)
    return ScoreReport(score=score, categories=categories)


# ─── Snapshot persistence ─────────────────────────────────────────────────────

_SNAPSHOT_FILENAME = ".zenzic-score.json"


def save_snapshot(repo_root: Path, report: ScoreReport) -> Path:
    """Write the score report to ``.zenzic-score.json`` in *repo_root*.

    Returns the path to the written file.
    """
    snapshot_path = repo_root / _SNAPSHOT_FILENAME
    snapshot_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return snapshot_path


def load_snapshot(repo_root: Path) -> ScoreReport | None:
    """Read the last saved score report from *repo_root*.

    Returns ``None`` if no snapshot file is present or the file cannot be parsed.
    """
    snapshot_path = repo_root / _SNAPSHOT_FILENAME
    if not snapshot_path.is_file():
        return None
    try:
        data = json.loads(snapshot_path.read_text(encoding="utf-8"))
        categories = [CategoryScore(**c) for c in data.get("categories", [])]
        # Support both the new "score" key and the legacy "total" key.
        score = int(data.get("score", data.get("total", 0)))
        threshold = int(data.get("threshold", 0))
        return ScoreReport(score=score, threshold=threshold, categories=categories)
    except Exception:
        return None
