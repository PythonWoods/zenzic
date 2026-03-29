# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Pure in-memory path resolver for Markdown documentation link validation.

Zero I/O guarantee: all file membership and anchor lookups are performed
against pre-built in-memory mappings passed at construction time.
No ``open()``, no ``Path.exists()``, no ``subprocess``.

The resolver is the engine-agnostic heart of Sprint 3.  It knows nothing
about MkDocs, Zensical, or any build system — only about paths, anchors,
and whether a link is resolvable within a given in-memory file tree.

Performance contract: 5 000 ``resolve()`` calls must complete in < 100 ms.
This is achieved by keeping the hot path free of ``pathlib.Path`` allocations:

- The Zenzic Shield uses a string prefix check (O(1), no Path decomposition).
- File lookup uses a flat pre-computed ``dict[str, Path]`` (one ``dict.get``
  replaces three ``Path`` constructions and three membership tests).
- ``_build_target`` returns a plain ``str`` via ``os.path.normpath`` (pure
  C string manipulation, no pathlib overhead).

Typical usage (caller owns I/O, resolver owns logic)::

    # I/O layer (CLI / plugin) builds the maps once
    md_contents: dict[Path, str] = {
        Path("/docs/index.md"): "# Home\\n",
        Path("/docs/guide/install.md"): "# Install\\n## Quick Start\\n",
    }
    anchors_cache = {p: anchors_in_file(c) for p, c in md_contents.items()}

    # Pure resolver — no further I/O
    resolver = InMemoryPathResolver(
        root_dir=Path("/docs"),
        md_contents=md_contents,
        anchors_cache=anchors_cache,
    )
    outcome = resolver.resolve(Path("/docs/index.md"), "guide/install.md#quick-start")
    assert isinstance(outcome, Resolved)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import NamedTuple
from urllib.parse import unquote, urlsplit


# ─── Outcome types (discriminated union) ──────────────────────────────────────


class PathTraversal(NamedTuple):
    """The resolved path escapes the documentation root — Shield rejection.

    This outcome is produced whenever ``..`` segments (or an absolute href)
    cause the normalised target to land outside ``root_dir``.

    Example trigger: ``[evil](../../../../etc/passwd)``

    Attributes:
        raw_href: The original href string exactly as it appeared in the source.
    """

    raw_href: str


class FileNotFound(NamedTuple):
    """No file matching the link target exists in ``md_contents``.

    Attributes:
        path_part: The decoded, normalised path component of the href
            (no fragment, no query string).
    """

    path_part: str


class AnchorMissing(NamedTuple):
    """The target file exists but the requested anchor slug is absent.

    Attributes:
        path_part: Decoded path component of the href.
        anchor: The fragment identifier that could not be found (without ``#``).
        resolved_file: The absolute path of the file that was found but whose
            heading set does not contain ``anchor``.
    """

    path_part: str
    anchor: str
    resolved_file: Path


class Resolved(NamedTuple):
    """Successful resolution: file exists and anchor (if any) is valid.

    Attributes:
        target: Absolute canonical path of the resolved target file.
    """

    target: Path


# Public union type — callers should pattern-match on the concrete type.
ResolveOutcome = PathTraversal | FileNotFound | AnchorMissing | Resolved


# ─── InMemoryPathResolver ──────────────────────────────────────────────────────


class InMemoryPathResolver:
    """Engine-agnostic, pure in-memory resolver for Markdown internal links.

    Resolves ``[text](href)`` link targets against a pre-built snapshot of the
    documentation tree.  The same instance is safe to call repeatedly because
    it holds no mutable state after construction.

    The resolver enforces three invariants:

    1. **Zero I/O** — no filesystem calls after construction.
    2. **Windows normalisation** — backslash separators in hrefs are
       converted to ``/`` before any processing.
    3. **Zenzic Shield** — any href whose normalised path resolves outside
       ``root_dir`` produces :class:`PathTraversal`.

    **Performance design:** the ``resolve()`` hot path allocates zero
    ``pathlib.Path`` objects after construction.  Containment is checked via
    a pre-computed string prefix; file lookup is a single ``dict.get()`` on a
    flat map built once in ``__init__``.

    Args:
        root_dir: Absolute, canonical root of the documentation tree.
            Must contain no ``..`` segments and must not be a symlink —
            the Shield relies on this boundary being trustworthy.
        md_contents: Mapping of absolute resolved ``Path`` → raw Markdown text.
        anchors_cache: Mapping of absolute resolved ``Path`` → set of anchor
            slugs pre-computed from headings.
    """

    __slots__ = (
        "_root_dir",
        "_root_str",
        "_root_prefix",
        "_md_contents",
        "_anchors_cache",
        "_lookup_map",
    )

    def __init__(
        self,
        root_dir: Path,
        md_contents: dict[Path, str],
        anchors_cache: dict[Path, set[str]],
    ) -> None:
        self._root_dir: Path = self._coerce_path(root_dir)

        # Pre-compute string forms of root_dir once so the hot path never
        # touches pathlib during the Shield check.
        self._root_str: str = str(self._root_dir)
        self._root_prefix: str = self._root_str + os.sep

        # Store coerced maps for anchor validation (Path keys needed there).
        self._md_contents: dict[Path, str] = {
            self._coerce_path(k): v for k, v in md_contents.items()
        }
        self._anchors_cache: dict[Path, set[str]] = {
            self._coerce_path(k): v for k, v in anchors_cache.items()
        }

        # ── Flat lookup map: str(variant) → canonical Path ────────────────────
        # For every file in md_contents, pre-register three lookup keys:
        #   1. str(file)                — exact match          (guide/install.md)
        #   2. str(file.with_suffix("")) — implicit .md suffix  (guide/install)
        #   3. str(file.parent)          — directory index       (guide/)
        #      (only when file.name == "index.md")
        #
        # Result: _lookup(target_str) is a single O(1) dict.get() with zero
        # Path allocations, replacing three Path constructions + three lookups.
        lookup_map: dict[str, Path] = {}
        for canonical in self._md_contents:
            key = str(canonical)
            lookup_map[key] = canonical
            if canonical.suffix:
                lookup_map[str(canonical.with_suffix(""))] = canonical
            if canonical.name == "index.md":
                lookup_map[str(canonical.parent)] = canonical
        self._lookup_map: dict[str, Path] = lookup_map

    # ── Public API ────────────────────────────────────────────────────────────

    def resolve(self, source_file: Path, href: str) -> ResolveOutcome:
        """Resolve *href* as seen from *source_file*.

        The hot path is allocation-free: all intermediate representations are
        plain strings until the final ``Resolved(target=...)`` NamedTuple.

        Args:
            source_file: Absolute path of the file that contains the link.
            href: Raw link target string as extracted from the Markdown source.
                May contain percent-encoding, a fragment, and/or Windows
                backslashes — all are normalised internally.

        Returns:
            :class:`Resolved` when the target exists and any anchor is valid.
            :class:`FileNotFound` when the target path is not in ``md_contents``.
            :class:`AnchorMissing` when the file exists but the anchor does not.
            :class:`PathTraversal` when the path escapes ``root_dir``.
        """
        source_file = self._coerce_path(source_file)

        parsed = urlsplit(href)
        path_part = unquote(self._normalize_href(parsed.path))
        fragment = parsed.fragment

        # _build_target returns a str — no Path allocation in the hot path.
        target_str = self._build_target(source_file, path_part)

        # ── Shield: O(1) string prefix check ─────────────────────────────────
        # os.path.normpath already collapsed ../../../../etc/passwd into
        # /etc/passwd inside _build_target.  We then verify containment with
        # two string comparisons instead of pathlib's segment-by-segment walk.
        if not (target_str == self._root_str or target_str.startswith(self._root_prefix)):
            return PathTraversal(raw_href=href)

        # ── Lookup: single dict.get() — O(1), zero Path constructions ────────
        resolved = self._lookup_map.get(target_str)
        if resolved is None:
            return FileNotFound(path_part=path_part)

        # ── Anchor validation ─────────────────────────────────────────────────
        if fragment:
            anchors = self._anchors_cache.get(resolved, set())
            if fragment.lower() not in anchors:
                return AnchorMissing(
                    path_part=path_part,
                    anchor=fragment,
                    resolved_file=resolved,
                )

        return Resolved(target=resolved)

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _coerce_path(p: object) -> Path:
        """Force-cast any incoming value to ``pathlib.Path``.

        Called on every path arriving from an external mapping.  A ``str``,
        a ``PurePosixPath``, or any other object with a meaningful ``__str__``
        is coerced silently rather than raising an ``AttributeError`` deep in
        the resolution pipeline.

        Args:
            p: Any object that should represent a filesystem path.

        Returns:
            A ``pathlib.Path`` wrapping the canonical string form of *p*.
        """
        if isinstance(p, Path):
            return p
        return Path(str(p))

    @staticmethod
    def _normalize_href(href: str) -> str:
        """Replace Windows backslash separators with forward slashes.

        Authors on Windows may write ``..\\guide.md`` or ``sub\\page.md``.
        Normalising to ``/`` ensures identical resolution on POSIX hosts.

        Args:
            href: Raw href string from the Markdown source.

        Returns:
            Equivalent href using only ``/`` as path separator.
        """
        return href.replace("\\", "/")

    def _build_target(self, source_file: Path, path_part: str) -> str:
        """Compute the normalised absolute target path as a plain string.

        Returns a ``str`` (not a ``Path``) so the caller can use it directly
        in string comparisons and dict lookups without any further allocation.

        ``os.path.normpath`` is pure C string arithmetic — no ``stat()``,
        no ``readlink()``, no kernel calls.  It collapses all ``.`` and ``..``
        segments, which is what makes the Shield work: ``../../../../etc/passwd``
        is reduced to ``/etc/passwd`` before the prefix check, so the traversal
        is always caught.

        Args:
            source_file: The absolute path of the file containing the link.
            path_part: Decoded, backslash-normalised path component of the href.

        Returns:
            Normalised absolute path string with all ``.`` and ``..`` resolved.
        """
        if path_part.startswith("/"):
            raw = self._root_str + os.sep + path_part.lstrip("/")
        else:
            raw = str(source_file.parent) + os.sep + path_part
        return os.path.normpath(raw)
