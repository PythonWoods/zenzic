# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for src/zenzic/core/cache.py — content-addressable finding cache."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from zenzic.core.cache import (
    CacheManager,
    make_config_hash,
    make_content_hash,
    make_file_key,
    make_vsm_snapshot_hash,
)
from zenzic.core.rules import RuleFinding
from zenzic.models.vsm import Route


# ─── Pure hash helpers ─────────────────────────────────────────────────────────


def test_make_content_hash_is_stable() -> None:
    """Same text → same hash on every call."""
    h = make_content_hash("hello world")
    assert h == make_content_hash("hello world")
    assert len(h) == 64  # SHA-256 hex


def test_make_content_hash_differs_on_different_input() -> None:
    assert make_content_hash("a") != make_content_hash("b")


def test_make_config_hash_is_stable() -> None:
    cfg = '{"engine":"standalone","strict":false}'
    assert make_config_hash(cfg) == make_config_hash(cfg)
    assert len(make_config_hash(cfg)) == 64


def test_make_config_hash_differs_on_different_input() -> None:
    assert make_config_hash('{"a":1}') != make_config_hash('{"a":2}')


def test_make_vsm_snapshot_hash_empty_vsm() -> None:
    h = make_vsm_snapshot_hash({})
    assert len(h) == 64
    assert h == make_vsm_snapshot_hash({})  # deterministic


def test_make_vsm_snapshot_hash_includes_anchors() -> None:
    """Hash must change when anchors change."""
    route_no_anchors = Route(url="/a/", source="a.md", status="REACHABLE")
    route_with_anchors = Route(url="/a/", source="a.md", status="REACHABLE", anchors={"intro"})
    vsm_a: dict[str, Route] = {"/a/": route_no_anchors}
    vsm_b: dict[str, Route] = {"/a/": route_with_anchors}
    assert make_vsm_snapshot_hash(vsm_a) != make_vsm_snapshot_hash(vsm_b)


def test_make_vsm_snapshot_hash_order_independent() -> None:
    """Routes sorted by URL → insertion order does not matter."""
    r1 = Route(url="/a/", source="a.md", status="REACHABLE")
    r2 = Route(url="/b/", source="b.md", status="REACHABLE")
    vsm_ab: dict[str, Route] = {"/a/": r1, "/b/": r2}
    vsm_ba: dict[str, Route] = {"/b/": r2, "/a/": r1}
    assert make_vsm_snapshot_hash(vsm_ab) == make_vsm_snapshot_hash(vsm_ba)


def test_make_file_key_atomic_two_components() -> None:
    key = make_file_key("aaa", "bbb")
    assert key == "aaa:bbb"


def test_make_file_key_global_three_components() -> None:
    key = make_file_key("aaa", "bbb", "ccc")
    assert key == "aaa:bbb:ccc"


def test_make_file_key_none_vsm_omits_third_component() -> None:
    key_none = make_file_key("x", "y", None)
    key_atomic = make_file_key("x", "y")
    assert key_none == key_atomic == "x:y"


# ─── CacheManager — in-memory operations ──────────────────────────────────────


def _make_finding(path: Path = Path("guide/a.md"), line: int = 1) -> RuleFinding:
    return RuleFinding(
        file_path=path,
        line_no=line,
        rule_id="Z101",
        message="broken link",
        severity="error",
    )


def test_cache_miss_returns_none() -> None:
    cache = CacheManager()
    assert cache.get("nonexistent-key") is None


def test_cache_put_then_get_roundtrip() -> None:
    cache = CacheManager()
    finding = _make_finding()
    cache.put("k1", [finding])
    result = cache.get("k1")
    assert result is not None
    assert len(result) == 1
    assert result[0].rule_id == "Z101"
    assert result[0].file_path == Path("guide/a.md")
    assert result[0].line_no == 1


def test_cache_put_empty_list() -> None:
    cache = CacheManager()
    cache.put("k_empty", [])
    result = cache.get("k_empty")
    assert result == []


def test_cache_preserves_matched_line() -> None:
    finding = RuleFinding(
        file_path=Path("x.md"),
        line_no=5,
        rule_id="Z201",
        message="secret",
        severity="security_breach",
        matched_line="aws_key = AKIA...",
    )
    cache = CacheManager()
    cache.put("k", [finding])
    result = cache.get("k")
    assert result is not None
    assert result[0].matched_line == "aws_key = AKIA..."


def test_cache_hit_rate_no_lookups() -> None:
    assert CacheManager().hit_rate == 0.0


def test_cache_hit_rate_all_misses() -> None:
    cache = CacheManager()
    cache.get("missing1")
    cache.get("missing2")
    assert cache.hit_rate == 0.0


def test_cache_hit_rate_mixed() -> None:
    cache = CacheManager()
    cache.put("k", [_make_finding()])
    cache.get("k")  # hit
    cache.get("missing")  # miss
    assert cache.hit_rate == pytest.approx(0.5)


def test_cache_size_empty() -> None:
    assert CacheManager().size == 0


def test_cache_size_after_puts() -> None:
    cache = CacheManager()
    cache.put("k1", [_make_finding()])
    cache.put("k2", [_make_finding()])
    assert cache.size == 2


def test_cache_overwrite_existing_key() -> None:
    cache = CacheManager()
    cache.put("k", [_make_finding(path=Path("old.md"))])
    cache.put("k", [_make_finding(path=Path("new.md"))])
    result = cache.get("k")
    assert result is not None
    assert result[0].file_path == Path("new.md")


def test_cache_initial_store_propagated() -> None:
    """CacheManager accepts a pre-populated store at construction."""
    store = {
        "k1": [
            {
                "file_path": "a.md",
                "line_no": 3,
                "rule_id": "Z104",
                "message": "not found",
                "severity": "error",
                "matched_line": "",
            }
        ]
    }
    cache = CacheManager(store=store)
    result = cache.get("k1")
    assert result is not None
    assert result[0].rule_id == "Z104"


# ─── CacheManager — I/O boundary ──────────────────────────────────────────────


def test_load_missing_file_returns_empty(tmp_path: Path) -> None:
    cache = CacheManager.load(tmp_path / "nonexistent.json")
    assert cache.size == 0
    assert cache.hit_rate == 0.0


def test_load_corrupt_json_returns_empty(tmp_path: Path) -> None:
    p = tmp_path / ".zenzic-cache.json"
    p.write_text("NOT VALID JSON", encoding="utf-8")
    cache = CacheManager.load(p)
    assert cache.size == 0


def test_load_non_dict_json_returns_empty(tmp_path: Path) -> None:
    p = tmp_path / ".zenzic-cache.json"
    p.write_text("[1, 2, 3]", encoding="utf-8")
    cache = CacheManager.load(p)
    assert cache.size == 0


def test_save_and_reload_roundtrip(tmp_path: Path) -> None:
    cache_path = tmp_path / ".zenzic-cache.json"
    cache = CacheManager()
    finding = _make_finding(path=Path("docs/guide.md"), line=42)
    cache.put("mykey", [finding])
    cache.save(cache_path)

    assert cache_path.is_file()

    reloaded = CacheManager.load(cache_path)
    result = reloaded.get("mykey")
    assert result is not None
    assert result[0].file_path == Path("docs/guide.md")
    assert result[0].line_no == 42


def test_save_creates_parent_dirs(tmp_path: Path) -> None:
    deep_path = tmp_path / "a" / "b" / "c" / ".zenzic-cache.json"
    cache = CacheManager()
    cache.save(deep_path)
    assert deep_path.is_file()


def test_save_writes_valid_json(tmp_path: Path) -> None:
    cache_path = tmp_path / ".zenzic-cache.json"
    cache = CacheManager()
    cache.put("k", [_make_finding()])
    cache.save(cache_path)
    data = json.loads(cache_path.read_text())
    assert isinstance(data, dict)
    assert "k" in data


def test_save_atomic_no_tmp_left_behind(tmp_path: Path) -> None:
    cache_path = tmp_path / ".zenzic-cache.json"
    cache = CacheManager()
    cache.save(cache_path)
    tmp = cache_path.with_suffix(".tmp")
    assert not tmp.exists()


def test_save_oserror_removes_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """OSError during write must clean up the .tmp file."""
    cache_path = tmp_path / ".zenzic-cache.json"
    cache = CacheManager()
    cache.put("k", [_make_finding()])

    def fail_dump(*args, **kwargs):  # noqa: ANN002, ANN003
        raise OSError("disk full")

    monkeypatch.setattr("zenzic.core.cache.json.dump", fail_dump)
    with pytest.raises(OSError, match="disk full"):
        cache.save(cache_path)
    assert not cache_path.with_suffix(".tmp").exists()
