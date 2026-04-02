# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for the parallel scanner and idempotency guarantees.

Dev 4 mandate: running the scan 100 times in parallel must produce
bit-identical output every time.
"""

from __future__ import annotations

import concurrent.futures
from pathlib import Path

import pytest

from zenzic.core.rules import AdaptiveRuleEngine, BaseRule, RuleFinding
from zenzic.core.scanner import scan_docs_references
from zenzic.models.config import ZenzicConfig
from zenzic.models.references import IntegrityReport


# Module-level BoomRule: pickleable (defined at module level) but raises
# during check().  Used to test that the engine isolates runtime exceptions.
class _BoomRule(BaseRule):
    @property
    def rule_id(self) -> str:
        return "BOOM"

    def check(self, file_path: Path, text: str) -> list[RuleFinding]:
        raise RuntimeError("intentional failure")


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _make_docs(tmp_path: Path, n_files: int = 5) -> Path:
    """Create a docs tree with *n_files* Markdown files."""
    docs = tmp_path / "docs"
    docs.mkdir()
    for i in range(n_files):
        (docs / f"page_{i:03d}.md").write_text(
            f"# Page {i}\n\nThis is page {i}.\n\n[link][ref]\n\n[ref]: https://example.com\n"
        )
    return tmp_path


def _report_fingerprint(reports: list[IntegrityReport]) -> list[tuple[str, float, int]]:
    """Return a canonical fingerprint for a list of reports (path, score, n_findings)."""
    return sorted((str(r.file_path), round(r.score, 6), len(r.findings)) for r in reports)


# ─── Correctness ──────────────────────────────────────────────────────────────


def test_parallel_matches_sequential(tmp_path: Path) -> None:
    """Parallel scan produces the same reports as the sequential scan."""
    repo = _make_docs(tmp_path, n_files=10)
    config = ZenzicConfig()

    sequential, _ = scan_docs_references(repo, config)
    parallel, _ = scan_docs_references(repo, config, workers=2)

    assert _report_fingerprint(sequential) == _report_fingerprint(parallel)


def test_parallel_empty_docs(tmp_path: Path) -> None:
    """Parallel scan on a repo with no docs returns empty results."""
    (tmp_path / "docs").mkdir()
    config = ZenzicConfig()
    reports, _ = scan_docs_references(tmp_path, config, workers=2)
    assert reports == []


def test_parallel_docs_not_exist(tmp_path: Path) -> None:
    """Parallel scan returns empty results when docs_dir does not exist."""
    config = ZenzicConfig()
    reports, _ = scan_docs_references(tmp_path, config, workers=2)
    assert reports == []


def test_parallel_single_worker_is_sequential(tmp_path: Path) -> None:
    """workers=1 disables parallelism but still returns correct results."""
    repo = _make_docs(tmp_path, n_files=4)
    config = ZenzicConfig()
    result, _ = scan_docs_references(repo, config, workers=1)
    assert len(result) == 4
    # All refs should resolve (we defined [ref] in every file)
    for report in result:
        assert report.score == 100.0


@pytest.mark.parametrize("workers", [0, -1, -8])
def test_parallel_invalid_workers_raise_clear_error(tmp_path: Path, workers: int) -> None:
    """workers must be None or >= 1 to avoid opaque executor errors."""
    repo = _make_docs(tmp_path, n_files=2)
    config = ZenzicConfig()

    with pytest.raises(ValueError, match="workers must be None or an integer >= 1"):
        scan_docs_references(repo, config, workers=workers)


def test_parallel_sorted_output(tmp_path: Path) -> None:
    """Output is sorted by file_path regardless of worker scheduling order."""
    repo = _make_docs(tmp_path, n_files=8)
    config = ZenzicConfig()
    result, _ = scan_docs_references(repo, config, workers=4)
    paths = [r.file_path for r in result]
    assert paths == sorted(paths)


# ─── Idempotency (Dev 4 mandate) ──────────────────────────────────────────────


@pytest.mark.slow
def test_idempotency_sequential_100_runs(tmp_path: Path) -> None:
    """Sequential scan: 100 identical runs produce bit-identical fingerprints."""
    repo = _make_docs(tmp_path, n_files=10)
    config = ZenzicConfig()

    baseline = _report_fingerprint(scan_docs_references(repo, config)[0])
    for _ in range(99):
        result = _report_fingerprint(scan_docs_references(repo, config)[0])
        assert result == baseline, "Sequential scan is not deterministic"


def test_idempotency_parallel_10_runs(tmp_path: Path) -> None:
    """Parallel scan: 10 runs produce identical fingerprints (fast, not marked slow)."""
    repo = _make_docs(tmp_path, n_files=5)
    config = ZenzicConfig()

    baseline = _report_fingerprint(scan_docs_references(repo, config, workers=2)[0])
    for _ in range(9):
        result = _report_fingerprint(scan_docs_references(repo, config, workers=2)[0])
        assert result == baseline, "Parallel scan is not deterministic"


def test_idempotency_concurrent_invocations(tmp_path: Path) -> None:
    """Launching multiple scans concurrently from threads produces identical results.

    Simulates the scenario where two CI jobs trigger Zenzic simultaneously
    on the same repo (read-only access, different processes).
    """
    repo = _make_docs(tmp_path, n_files=6)
    config = ZenzicConfig()

    baseline = _report_fingerprint(scan_docs_references(repo, config)[0])

    def run_scan() -> list[tuple[str, float, int]]:
        return _report_fingerprint(scan_docs_references(repo, config)[0])

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(run_scan) for _ in range(8)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    for result in results:
        assert result == baseline, "Concurrent invocations produce different results"


# ─── Plugin exception isolation (Dev 4 mandate) ──────────────────────────────


def test_parallel_rule_exception_isolated(tmp_path: Path) -> None:
    """A module-level rule that raises at runtime does not abort other files."""
    from zenzic.core.scanner import _scan_single_file

    docs = tmp_path / "docs"
    docs.mkdir()
    files = [docs / f"p{i}.md" for i in range(3)]
    for f in files:
        f.write_text("# page\n")

    config = ZenzicConfig()
    engine = AdaptiveRuleEngine([_BoomRule()])

    # All files should produce a report with one RULE-ENGINE-ERROR finding
    for f in files:
        report, _ = _scan_single_file(f, config, engine)
        assert len(report.rule_findings) == 1
        assert report.rule_findings[0].rule_id == "RULE-ENGINE-ERROR"
        assert report.rule_findings[0].is_error
