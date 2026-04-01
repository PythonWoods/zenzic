# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Content-addressable cache for Zenzic rule results.

Architecture
------------
The cache maps a **deterministic key** to a list of serialised
:class:`~zenzic.core.rules.RuleFinding` objects.  The key is a SHA-256 digest
that encodes everything the Rule Engine depends on for a given file:

* **File content hash** — ``SHA256(raw_markdown)``
* **Config hash** — ``SHA256(canonical_config_json)`` — invalidated when any
  ``zenzic.toml`` option changes.
* **VSM snapshot hash** (optional) — ``SHA256(canonical_vsm_json)`` — only
  included for *global rules* (those that consult routing state).  Atomic
  rules (e.g. :class:`~zenzic.core.rules.CustomRule`) omit this component so
  their cache entries survive VSM changes caused by other files.

Cache invalidation model
------------------------
A cache hit requires an **exact key match**.  No TTL, no "close enough".  This
is intentional:

* If *only* a file's content changes, its own cache is invalidated; other
  files whose VSM-level keys still match are served from cache.
* If the VSM changes (because any file changed), all global-rule cache entries
  are invalidated automatically — without needing a file-to-file dependency
  graph.
* If ``zenzic.toml`` changes, all entries are invalidated regardless of rule
  type.

Cache persistence
-----------------
The cache is written to disk **only at the end of a run** — after all checks
complete — to preserve the I/O-boundary discipline.  The caller (CLI layer)
owns the load/save lifecycle.  The :class:`CacheManager` is pure in-memory
during validation; disk I/O is confined to :meth:`CacheManager.load` and
:meth:`CacheManager.save`.

Zenzic Way compliance
---------------------
* **Lint the Source:** the cache key is derived from source content, never
  from file timestamps (unreliable in CI where clones reset mtime).
* **No Subprocesses:** ``hashlib.sha256`` is pure C in CPython — no shell.
* **Pure Functions First:** :meth:`make_file_key` and
  :meth:`make_vsm_snapshot_hash` are pure; :meth:`get`/:meth:`put` are
  pure in-memory operations; I/O is confined to :meth:`load`/:meth:`save`.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from zenzic.core.rules import RuleFinding
    from zenzic.models.vsm import VSM


# ─── Cache key construction (pure) ───────────────────────────────────────────


def make_content_hash(text: str) -> str:
    """Return the SHA-256 hex digest of *text* (UTF-8 encoded).

    Pure: no I/O.

    Args:
        text: Raw file content.

    Returns:
        64-character lowercase hex string.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_config_hash(config_json: str) -> str:
    """Return the SHA-256 hex digest of a canonical config representation.

    The caller is responsible for producing a **stable, canonical** JSON
    string (sorted keys, no whitespace variance) so that semantically
    identical configs always produce the same hash.

    Pure: no I/O.

    Args:
        config_json: Canonical JSON representation of the active config.

    Returns:
        64-character lowercase hex string.
    """
    return hashlib.sha256(config_json.encode("utf-8")).hexdigest()


def make_vsm_snapshot_hash(vsm: VSM) -> str:
    """Return the SHA-256 hex digest of the VSM's routing state.

    Serialises only the fields that affect link validation:
    ``url``, ``source``, and ``status`` of every route.  The ``anchors``
    set is **included** because anchor changes affect anchor-link validation.
    The ``aliases`` set is excluded — it is reserved for future use and not
    yet consumed by any rule.

    The serialisation is deterministic: routes are sorted by URL, anchor
    sets are sorted lists.

    Pure: no I/O.

    Args:
        vsm: Pre-built Virtual Site Map (canonical URL → Route).

    Returns:
        64-character lowercase hex string.
    """
    snapshot = [
        {
            "url": route.url,
            "source": route.source,
            "status": route.status,
            "anchors": sorted(route.anchors),
        }
        for route in sorted(vsm.values(), key=lambda r: r.url)
    ]
    canonical = json.dumps(snapshot, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def make_file_key(
    content_hash: str,
    config_hash: str,
    vsm_hash: str | None = None,
) -> str:
    """Compose the cache lookup key for one file's rule results.

    Three-component key: ``content:config[:vsm]``.

    * Atomic rules (no VSM dependency) — pass ``vsm_hash=None``.  The key
      is stable across VSM changes caused by other files.
    * Global rules (VSM-aware) — pass the current ``vsm_hash``.  The key
      changes whenever any file's routing state changes.

    Pure: no I/O.

    Args:
        content_hash: ``make_content_hash()`` output for this file.
        config_hash:  ``make_config_hash()`` output for the active config.
        vsm_hash:     ``make_vsm_snapshot_hash()`` output, or ``None`` for
                      atomic rules.

    Returns:
        Composite key string (not a path — used as a dict key).
    """
    parts = [content_hash, config_hash]
    if vsm_hash is not None:
        parts.append(vsm_hash)
    return ":".join(parts)


# ─── CacheManager ─────────────────────────────────────────────────────────────


@dataclass
class _CachedEntry:
    """On-disk representation of one cached finding list."""

    file_path: str
    line_no: int
    rule_id: str
    message: str
    severity: str
    matched_line: str


class CacheManager:
    """In-memory content-addressable cache for rule findings.

    Keyed by :func:`make_file_key`.  All mutations are in-memory; persistence
    is opt-in via :meth:`save` (called by the CLI layer at the end of a run).

    Usage::

        # I/O boundary — load once at startup
        cache = CacheManager.load(repo_root / ".zenzic-cache.json")

        content_hash = make_content_hash(text)
        config_hash  = make_config_hash(config_json)
        vsm_hash     = make_vsm_snapshot_hash(vsm)

        # Atomic rule: VSM-independent key
        key_atomic = make_file_key(content_hash, config_hash)
        if (cached := cache.get(key_atomic)) is not None:
            findings = cached          # cache hit
        else:
            findings = engine.run(file_path, text)
            cache.put(key_atomic, findings)

        # Global rule: VSM-aware key
        key_global = make_file_key(content_hash, config_hash, vsm_hash)
        if (cached := cache.get(key_global)) is not None:
            vsm_findings = cached
        else:
            vsm_findings = engine.run_vsm(file_path, text, vsm, anchors_cache)
            cache.put(key_global, vsm_findings)

        # I/O boundary — save once at the end
        cache.save(repo_root / ".zenzic-cache.json")

    Args:
        store: Initial key → findings mapping (empty by default).
    """

    def __init__(self, store: dict[str, list[dict[str, Any]]] | None = None) -> None:
        self._store: dict[str, list[dict[str, Any]]] = store if store is not None else {}
        self._hits: int = 0
        self._misses: int = 0

    # ── Pure in-memory operations ─────────────────────────────────────────────

    def get(self, key: str) -> list[RuleFinding] | None:
        """Return cached findings for *key*, or ``None`` on a miss.

        Pure: no I/O after construction.

        Args:
            key: Composite cache key from :func:`make_file_key`.

        Returns:
            List of :class:`~zenzic.core.rules.RuleFinding`, or ``None``.
        """
        from zenzic.core.rules import RuleFinding

        raw = self._store.get(key)
        if raw is None:
            self._misses += 1
            return None
        self._hits += 1
        return [
            RuleFinding(
                file_path=Path(r["file_path"]),
                line_no=r["line_no"],
                rule_id=r["rule_id"],
                message=r["message"],
                severity=r["severity"],
                matched_line=r.get("matched_line", ""),
            )
            for r in raw
        ]

    def put(self, key: str, findings: list[RuleFinding]) -> None:
        """Store *findings* under *key*.

        Pure: mutates only the in-memory store.

        Args:
            key:      Composite cache key from :func:`make_file_key`.
            findings: Rule findings to store.
        """
        self._store[key] = [
            {
                "file_path": str(f.file_path),
                "line_no": f.line_no,
                "rule_id": f.rule_id,
                "message": f.message,
                "severity": f.severity,
                "matched_line": f.matched_line,
            }
            for f in findings
        ]

    @property
    def hit_rate(self) -> float:
        """Cache hit rate in [0.0, 1.0].  Returns 0.0 when no lookups made."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def size(self) -> int:
        """Number of entries currently in the cache."""
        return len(self._store)

    # ── I/O boundary ──────────────────────────────────────────────────────────

    @classmethod
    def load(cls, cache_path: Path) -> CacheManager:
        """Load a previously saved cache from disk.

        Returns an empty :class:`CacheManager` when the file does not exist
        or cannot be parsed (corrupt JSON, schema change) — silently degrading
        to a cold start rather than raising an error.  This is intentional:
        a missing or stale cache is never a fatal condition.

        Args:
            cache_path: Path to the ``.zenzic-cache.json`` file.

        Returns:
            Populated :class:`CacheManager` (or empty on any failure).
        """
        if not cache_path.is_file():
            return cls()
        try:
            with cache_path.open(encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return cls()
            return cls(store=data)
        except (json.JSONDecodeError, OSError, KeyError):
            return cls()

    def save(self, cache_path: Path) -> None:
        """Persist the in-memory cache to *cache_path* as JSON.

        Creates parent directories if needed.  Writes atomically by first
        writing to a ``.tmp`` sibling and then renaming — preventing a
        partial write from corrupting the cache file.

        This is the **only** I/O operation in this module.  It must be called
        by the CLI layer at the end of a run, never from inside the Core.

        Args:
            cache_path: Destination path for the cache JSON file.
        """
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = cache_path.with_suffix(".tmp")
        try:
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(self._store, f, separators=(",", ":"))
            tmp.replace(cache_path)
        except OSError:
            tmp.unlink(missing_ok=True)
            raise
