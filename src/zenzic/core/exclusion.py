# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Layered Exclusion system: VCS-aware file exclusion with 4-level hierarchy.

This module implements the core exclusion logic for the Obsidian Bastion
architecture.  All functions are **pure** — no I/O after construction except
for the ``VCSIgnoreParser.from_file()`` factory.

Exclusion Hierarchy (processed top-to-bottom, first match wins):

1. **System Guardrails (L1):** Hardcoded ``SYSTEM_EXCLUDED_DIRS`` — immutable.
2. **Forced Inclusions (L2):** ``included_dirs`` / ``included_file_patterns``
   from config — overrides VCS and Config exclusions (but NOT L1).
3. **CLI Overrides (L4):** ``--exclude-dir`` / ``--include-dir`` flags.
4. **VCS Discovery (L2-VCS):** ``.gitignore`` patterns when
   ``respect_vcs_ignore = true``.
5. **Config Overrides (L3):** ``excluded_dirs`` / ``excluded_file_patterns``
   from ``zenzic.toml``.
6. **Default:** Included.

Public API
----------
* :class:`VCSIgnoreParser` — pure-Python gitignore pattern engine.
* :class:`LayeredExclusionManager` — 4-level exclusion orchestrator.
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Self

from zenzic.models.config import (
    SYSTEM_EXCLUDED_DIRS,
    SYSTEM_EXCLUDED_FILE_NAMES,
    SYSTEM_EXCLUDED_FILE_PATTERNS,
)


if TYPE_CHECKING:
    from zenzic.models.config import ZenzicConfig


# ── VCS Ignore Parser ────────────────────────────────────────────────────────


def _gitignore_glob_to_regex(pattern: str) -> str:
    """Convert a single gitignore glob pattern to a regex string.

    Implements the gitignore pattern spec:
    - ``*`` matches anything except ``/``
    - ``**`` matches everything including ``/``
    - ``?`` matches any single character except ``/``
    - ``[...]`` character classes passed through
    - Leading ``/`` anchors to base dir
    - Trailing ``/`` means directory-only (handled by caller)
    """
    i = 0
    n = len(pattern)
    result: list[str] = []

    while i < n:
        c = pattern[i]
        if c == "*":
            if i + 1 < n and pattern[i + 1] == "*":
                # **
                if i + 2 < n and pattern[i + 2] == "/":
                    # **/ — match zero or more directories
                    result.append("(?:.*/)?")
                    i += 3
                    continue
                elif i == 0 or (i > 0 and pattern[i - 1] == "/"):
                    # Leading ** or /**/
                    result.append(".*")
                    i += 2
                    continue
                else:
                    # Trailing ** (e.g. abc/**)
                    result.append(".*")
                    i += 2
                    continue
            else:
                # Single * — match anything except /
                result.append("[^/]*")
                i += 1
        elif c == "?":
            result.append("[^/]")
            i += 1
        elif c == "[":
            # Character class — find closing ]
            j = i + 1
            if j < n and pattern[j] == "!":
                j += 1
            if j < n and pattern[j] == "]":
                j += 1
            while j < n and pattern[j] != "]":
                j += 1
            if j >= n:
                # No closing ] — treat [ as literal
                result.append(re.escape(c))
                i += 1
            else:
                # Convert [!...] to [^...]
                cls_content = pattern[i + 1 : j]
                if cls_content.startswith("!"):
                    cls_content = "^" + cls_content[1:]
                result.append(f"[{cls_content}]")
                i = j + 1
        elif c == "\\":
            # Escaped character
            if i + 1 < n:
                result.append(re.escape(pattern[i + 1]))
                i += 2
            else:
                result.append(re.escape(c))
                i += 1
        else:
            result.append(re.escape(c))
            i += 1

    return "".join(result)


@dataclass(slots=True, frozen=True)
class _GitignoreRule:
    """A single parsed gitignore rule."""

    pattern: re.Pattern[str]
    negated: bool
    dir_only: bool
    anchored: bool


class VCSIgnoreParser:
    """Pure-Python parser for ``.gitignore``-style pattern files.

    All patterns are pre-compiled to ``re.Pattern`` at construction time.
    Pattern matching is O(N) per path where N = number of rules.

    The parser follows the gitignore specification:
    - Last matching rule wins (negation via ``!`` can re-include).
    - Trailing ``/`` restricts a rule to directories only.
    - Leading ``/`` anchors a rule to the base directory.
    - A pattern containing a ``/`` (except trailing) is implicitly anchored.
    - ``*`` matches everything except ``/``.
    - ``**`` matches everything including ``/``.
    """

    __slots__ = ("_rules", "_has_negation", "_positive_combined", "_all_dir_only")

    def __init__(self, patterns: list[str], base_dir: Path | None) -> None:
        self._rules: list[_GitignoreRule] = []
        for raw_line in patterns:
            rule = self._parse_line(raw_line)
            if rule is not None:
                self._rules.append(rule)
        self._has_negation = any(r.negated for r in self._rules)
        self._all_dir_only = all(r.dir_only for r in self._rules)
        # Fast path: if no negation, combine all file-applicable rules into one regex
        self._positive_combined: re.Pattern[str] | None = None
        if not self._has_negation and self._rules:
            file_patterns = [r.pattern.pattern for r in self._rules if not r.dir_only]
            if file_patterns:
                try:
                    self._positive_combined = re.compile(
                        "|".join(f"(?:{p})" for p in file_patterns)
                    )
                except re.error:
                    self._positive_combined = None

    @classmethod
    def from_file(cls, path: Path) -> Self:
        """Load patterns from a file.  Returns empty parser if file is missing."""
        if not path.is_file():
            return cls([], base_dir=path.parent if path.parent.exists() else None)
        try:
            text = path.read_text(encoding="utf-8-sig")  # handles BOM
        except (OSError, UnicodeDecodeError):
            return cls([], base_dir=path.parent)
        lines = text.splitlines()
        return cls(lines, base_dir=path.parent)

    def is_excluded(self, rel_path: str, *, is_dir: bool = False) -> bool:
        """Return True if *rel_path* is excluded by the loaded rules.

        Uses last-matching-rule-wins semantics (gitignore spec).
        Paths containing ``..`` are always treated as non-matching (safety).
        """
        # Safety: reject paths with .. components
        if ".." in rel_path.split("/"):
            return False

        # Reject absolute paths (rel_path should always be relative)
        if rel_path.startswith("/"):
            return False

        # Fast path: no negation and checking files — use combined regex
        if not self._has_negation and not is_dir and self._positive_combined is not None:
            return self._positive_combined.search(rel_path) is not None

        excluded = False
        for rule in self._rules:
            if rule.dir_only and not is_dir:
                continue
            if rule.pattern.search(rel_path):
                excluded = not rule.negated
        return excluded

    @staticmethod
    def _parse_line(line: str) -> _GitignoreRule | None:
        """Parse a single gitignore line into a rule, or None if blank/comment."""
        # Strip trailing whitespace (but not escaped trailing space)
        stripped = line.rstrip()
        if not stripped:
            return None

        # Handle escaped trailing spaces: if line ends with '\ ', keep the space
        if line.rstrip("\n\r").endswith("\\ "):
            # Preserve one trailing space
            stripped = line.rstrip("\n\r")
            # Remove non-escaped trailing spaces, keep escaped ones
            while stripped.endswith("\\ "):
                break

        # Comments
        if stripped.startswith("#"):
            return None

        # Negation
        negated = False
        pattern = stripped
        if pattern.startswith("!"):
            negated = True
            pattern = pattern[1:]
            if not pattern:
                return None

        # Dir-only
        dir_only = pattern.endswith("/")
        if dir_only:
            pattern = pattern.rstrip("/")
            if not pattern:
                return None

        # Anchored: leading / or pattern contains /
        anchored = False
        if pattern.startswith("/"):
            anchored = True
            pattern = pattern[1:]
        elif "/" in pattern:
            anchored = True

        # Convert to regex
        regex_str = _gitignore_glob_to_regex(pattern)

        if anchored:
            # Must match from start of path
            full_regex = f"^{regex_str}"
            if dir_only:
                full_regex += "$"
            else:
                full_regex += "$"
        else:
            # Floating: can match anywhere in the path
            full_regex = f"(?:^|/){regex_str}"
            if dir_only:
                full_regex += "$"
            else:
                full_regex += "(?:/|$)"

        try:
            compiled = re.compile(full_regex)
        except re.error:
            return None

        return _GitignoreRule(
            pattern=compiled,
            negated=negated,
            dir_only=dir_only,
            anchored=anchored,
        )


# ── Layered Exclusion Manager ────────────────────────────────────────────────


class LayeredExclusionManager:
    """Orchestrates 4-level exclusion with pre-compiled patterns.

    Resolution order per directory (``should_exclude_dir``):
    1. System Guardrails → excluded (immutable)
    2. ``included_dirs`` (config) → included
    3. CLI ``--exclude-dir`` → excluded
    4. CLI ``--include-dir`` → included
    5. VCS ignore → excluded (if ``respect_vcs_ignore``)
    6. ``excluded_dirs`` (config) → excluded
    7. Default → included

    File-level checks (``should_exclude_file``) additionally evaluate
    ``included_file_patterns``, ``excluded_file_patterns``, and VCS patterns
    against the filename.
    """

    __slots__ = (
        "_system_dirs",
        "_adapter_metadata_files",
        "_config_excluded_dirs",
        "_config_included_dirs",
        "_cli_exclude_dirs",
        "_cli_include_dirs",
        "_config_excluded_patterns",
        "_config_included_patterns",
        "_vcs_parser",
        "_respect_vcs",
    )

    def __init__(
        self,
        config: ZenzicConfig,
        *,
        repo_root: Path | None = None,
        docs_root: Path | None = None,
        cli_exclude: list[str] | None = None,
        cli_include: list[str] | None = None,
        adapter_metadata_files: frozenset[str] = frozenset(),
    ) -> None:
        self._system_dirs: frozenset[str] = SYSTEM_EXCLUDED_DIRS
        self._adapter_metadata_files: frozenset[str] = adapter_metadata_files

        # Config-level dirs — strip system guardrails to keep layers clean
        raw_excluded = getattr(config, "excluded_dirs", []) or []
        raw_included = getattr(config, "included_dirs", []) or []
        # When config comes from normal ZenzicConfig(), model_post_init merges
        # SYSTEM_EXCLUDED_DIRS into excluded_dirs. Strip them to avoid L1/L3 confusion.
        self._config_excluded_dirs: frozenset[str] = frozenset(raw_excluded) - self._system_dirs
        self._config_included_dirs: frozenset[str] = frozenset(raw_included) - self._system_dirs

        # CLI overrides
        self._cli_exclude_dirs: frozenset[str] = frozenset(cli_exclude or [])
        self._cli_include_dirs: frozenset[str] = frozenset(cli_include or []) - self._system_dirs

        # File patterns — pre-compiled for performance
        raw_excl_patterns = getattr(config, "excluded_file_patterns", []) or []
        raw_incl_patterns = getattr(config, "included_file_patterns", []) or []
        self._config_excluded_patterns: list[re.Pattern[str]] = [
            re.compile(fnmatch.translate(p)) for p in raw_excl_patterns
        ]
        self._config_included_patterns: list[re.Pattern[str]] = [
            re.compile(fnmatch.translate(p)) for p in raw_incl_patterns
        ]

        # VCS
        self._respect_vcs: bool = getattr(config, "respect_vcs_ignore", False)
        self._vcs_parser: VCSIgnoreParser | None = None
        if self._respect_vcs:
            parsers: list[VCSIgnoreParser] = []
            if repo_root is not None:
                parsers.append(VCSIgnoreParser.from_file(repo_root / ".gitignore"))
            if docs_root is not None and docs_root != repo_root:
                parsers.append(VCSIgnoreParser.from_file(docs_root / ".gitignore"))
            if parsers:
                # Merge rules from all parsers into a single parser
                all_rules: list[_GitignoreRule] = []
                for p in parsers:
                    all_rules.extend(p._rules)
                merged = VCSIgnoreParser([], base_dir=None)
                merged._rules = all_rules
                # Rebuild fast-path caches
                merged._has_negation = any(r.negated for r in all_rules)
                merged._all_dir_only = all(r.dir_only for r in all_rules)
                merged._positive_combined = None
                if not merged._has_negation and all_rules:
                    file_patterns = [r.pattern.pattern for r in all_rules if not r.dir_only]
                    if file_patterns:
                        try:
                            merged._positive_combined = re.compile(
                                "|".join(f"(?:{p})" for p in file_patterns)
                            )
                        except re.error:
                            pass
                self._vcs_parser = merged

    def should_exclude_dir(self, dir_name: str, rel_path: str | None = None) -> bool:
        """Return True if a directory should be excluded during walk.

        Fast path: checks directory name against all layers.
        """
        # L1: System guardrails — immutable, absolute priority
        if dir_name in self._system_dirs:
            return True

        # L2 forced: Config included_dirs override config exclusions
        if dir_name in self._config_included_dirs:
            return False

        # L4: CLI --exclude-dir
        if dir_name in self._cli_exclude_dirs:
            return True

        # L4: CLI --include-dir
        if dir_name in self._cli_include_dirs:
            return False

        # L2 VCS: VCS ignore (for directories)
        if self._vcs_parser is not None:
            check_path = rel_path if rel_path else dir_name
            if self._vcs_parser.is_excluded(check_path, is_dir=True):
                return True

        # L3: Config excluded_dirs
        if dir_name in self._config_excluded_dirs:
            return True

        # L7: Default — included
        return False

    def should_exclude_file(self, file_path: Path, docs_root: Path) -> bool:
        """Return True if a file should be excluded from scanning.

        Full 5-layer evaluation for individual files.
        """
        filename = file_path.name
        try:
            rel_path = file_path.relative_to(docs_root).as_posix()
        except ValueError:
            rel_path = filename

        # L1a: System file guardrails — immutable (infrastructure + adapter metadata)
        if (
            filename in SYSTEM_EXCLUDED_FILE_NAMES
            or any(fnmatch.fnmatch(filename, p) for p in SYSTEM_EXCLUDED_FILE_PATTERNS)
            or filename in self._adapter_metadata_files
        ):
            return True

        # L1: System guardrails — check path components
        for part in Path(rel_path).parts[:-1]:  # directories only, not filename
            if part in self._system_dirs:
                return True

        # L2 forced: included_file_patterns (override everything except L1)
        if self._config_included_patterns:
            if any(p.match(filename) for p in self._config_included_patterns):
                return False

        # L2 forced: included_dirs
        for part in Path(rel_path).parts[:-1]:
            if part in self._config_included_dirs:
                return False

        # L4: CLI --exclude-dir (check path components)
        for part in Path(rel_path).parts[:-1]:
            if part in self._cli_exclude_dirs:
                return True

        # L4: CLI --include-dir (check path components)
        for part in Path(rel_path).parts[:-1]:
            if part in self._cli_include_dirs:
                return False

        # L2 VCS: .gitignore patterns
        if self._vcs_parser is not None:
            if self._vcs_parser.is_excluded(rel_path, is_dir=False):
                return True

        # L3: Config excluded_file_patterns
        if self._config_excluded_patterns:
            if any(p.match(filename) for p in self._config_excluded_patterns):
                return True

        # L3: Config excluded_dirs (check path components)
        for part in Path(rel_path).parts[:-1]:
            if part in self._config_excluded_dirs:
                return True

        # L7: Default — included
        return False

    @property
    def excluded_dirs(self) -> frozenset[str]:
        """Backward-compatible property: all excluded directory names.

        Returns the union of system guardrails, config exclusions, and CLI
        exclusions.  Used by callers that need a flat set (e.g. ``walk_files``
        fallback path).
        """
        return self._system_dirs | self._config_excluded_dirs | self._cli_exclude_dirs
