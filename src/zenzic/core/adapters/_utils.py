# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Shared utilities for Zenzic adapters.

- **i18n path remapping** — locale prefix stripping for ``fallback_to_default``.
- **Frontmatter extraction** — engine-agnostic YAML frontmatter parser.
- **Eager Metadata Cache** — single-pass extraction of slug, draft/unlisted
  flags, and tags from all loaded files.

All functions are **pure** — no I/O, no disk access.  Third-party adapters
may use or ignore them as needed.
"""

from __future__ import annotations

import re
from pathlib import Path


def remap_to_default_locale(
    abs_path: Path,
    docs_root: Path,
    locale_dirs: frozenset[str],
) -> Path | None:
    """Return the default-locale equivalent of a path inside a locale sub-tree.

    Strips the first path component when it is a known locale directory name,
    producing the canonical default-locale path.  Returns ``None`` when the
    path is not inside any known locale directory — the caller should not apply
    fallback logic in that case.

    This function is **pure** — no I/O, no disk access.  The caller decides
    what to do with the returned path (existence check, anchor lookup, etc.).

    Examples::

        remap_to_default_locale(
            Path("/docs/it/architecture.md"),
            Path("/docs"),
            frozenset({"it", "fr"}),
        )
        # → Path("/docs/architecture.md")

        remap_to_default_locale(
            Path("/docs/architecture.md"),
            Path("/docs"),
            frozenset({"it", "fr"}),
        )
        # → None  (not inside a locale directory)

    Args:
        abs_path: Absolute path to remap.  May be a ``.md`` file, an asset,
            or any path inside ``docs_root``.
        docs_root: Resolved absolute ``docs/`` root.
        locale_dirs: Frozenset of non-default locale directory names
            (e.g. ``frozenset({"it", "fr"})``).

    Returns:
        Absolute :class:`~pathlib.Path` of the default-locale equivalent, or
        ``None`` when *abs_path* is not inside a recognised locale directory.
    """
    try:
        rel = abs_path.relative_to(docs_root)
    except ValueError:
        return None
    if not rel.parts or rel.parts[0] not in locale_dirs:
        return None
    return docs_root.joinpath(*rel.parts[1:])


# ── Frontmatter extraction (engine-agnostic) ────────────────────────────────

# Matches leading YAML frontmatter block: --- ... ---
_FRONTMATTER_RE = re.compile(r"\A\s*---\s*\n(.*?)\n---", re.DOTALL)

# Individual field patterns inside frontmatter.
_SLUG_RE = re.compile(r"^slug\s*:\s*['\"]?([^'\"#\n]+?)['\"]?\s*$", re.MULTILINE)
_DRAFT_RE = re.compile(r"^draft\s*:\s*(true|false)\s*$", re.MULTILINE | re.IGNORECASE)
_UNLISTED_RE = re.compile(r"^unlisted\s*:\s*(true|false)\s*$", re.MULTILINE | re.IGNORECASE)
_TAGS_RE = re.compile(r"^tags\s*:\s*\[([^\]]*)\]\s*$", re.MULTILINE)
_TAGS_FLOW_RE = re.compile(r"^-\s+(.+)$", re.MULTILINE)


def extract_frontmatter_slug(content: str) -> str | None:
    """Extract ``slug`` from YAML frontmatter, or ``None`` if absent.

    Only looks in the leading ``---`` fenced block.  The slug value is
    returned as-is (may be absolute ``/custom`` or relative ``custom``).

    This function is **engine-agnostic** — it works identically for
    MkDocs, Docusaurus, Zensical, and Standalone.

    Args:
        content: Raw Markdown/MDX source text.

    Returns:
        The slug string, or ``None`` when no frontmatter slug is declared.
    """
    fm = _FRONTMATTER_RE.match(content)
    if fm is None:
        return None
    slug_match = _SLUG_RE.search(fm.group(1))
    if slug_match is None:
        return None
    return slug_match.group(1).strip()


def extract_frontmatter_draft(content: str) -> bool:
    """Return ``True`` when frontmatter declares ``draft: true``.

    Returns ``False`` when no frontmatter exists, when ``draft`` is absent,
    or when ``draft: false`` is declared.
    """
    fm = _FRONTMATTER_RE.match(content)
    if fm is None:
        return False
    m = _DRAFT_RE.search(fm.group(1))
    return m is not None and m.group(1).lower() == "true"


def extract_frontmatter_unlisted(content: str) -> bool:
    """Return ``True`` when frontmatter declares ``unlisted: true``.

    Returns ``False`` when no frontmatter exists, when ``unlisted`` is absent,
    or when ``unlisted: false`` is declared.
    """
    fm = _FRONTMATTER_RE.match(content)
    if fm is None:
        return False
    m = _UNLISTED_RE.search(fm.group(1))
    return m is not None and m.group(1).lower() == "true"


def extract_frontmatter_tags(content: str) -> list[str]:
    """Extract ``tags`` from YAML frontmatter as a list of strings.

    Supports both inline (``tags: [a, b]``) and flow (``tags:\\n- a\\n- b``)
    YAML syntax.  Returns an empty list when no tags are declared.
    """
    fm = _FRONTMATTER_RE.match(content)
    if fm is None:
        return []
    fm_text = fm.group(1)

    # Inline syntax: tags: [a, b, c]
    inline = _TAGS_RE.search(fm_text)
    if inline:
        raw = inline.group(1)
        return [t.strip().strip("'\"") for t in raw.split(",") if t.strip()]

    # Flow syntax: tags:\n- a\n- b
    tags_start = re.search(r"^tags\s*:\s*$", fm_text, re.MULTILINE)
    if tags_start:
        rest = fm_text[tags_start.end() :]
        return [m.group(1).strip() for m in _TAGS_FLOW_RE.finditer(rest)]

    return []


# ── Eager Metadata Cache ─────────────────────────────────────────────────────

from dataclasses import dataclass, field  # noqa: E402


@dataclass(slots=True)
class FileMetadata:
    """Metadata harvested from a single Markdown file's frontmatter.

    Populated in a single pass during Phase 1 (VSM construction).
    All fields default to safe no-op values.
    """

    slug: str | None = None
    draft: bool = False
    unlisted: bool = False
    tags: list[str] = field(default_factory=list)


def build_metadata_cache(
    md_contents: dict[Path, str],
    docs_root: Path,
    *,
    shield_enabled: bool = True,
) -> dict[str, FileMetadata]:
    """Build a metadata cache from all loaded Markdown files in one pass.

    Extracts ``slug``, ``draft``, ``unlisted``, and ``tags`` from each file's
    YAML frontmatter.  The returned dict is keyed by the POSIX relative path
    (e.g. ``"guide/install.mdx"``).

    This is the **Eager Metadata Harvesting** function: call it once during
    VSM construction to pre-compute all frontmatter metadata, then pass the
    result to adapter constructors or ``get_route_info()`` implementations.

    When ``shield_enabled`` is ``True`` (default), every frontmatter line is
    passed through :func:`~zenzic.core.shield.safe_read_line` before parsing.
    If a secret is detected, :class:`~zenzic.core.shield.ShieldViolation` is
    raised immediately — the VSM is never constructed.

    Args:
        md_contents: Pre-loaded mapping of absolute ``Path`` → raw content.
        docs_root: Resolved absolute ``docs/`` directory root.
        shield_enabled: When ``True``, invoke the Shield on frontmatter lines.

    Returns:
        Dict mapping POSIX relative path → :class:`FileMetadata`.

    Raises:
        :class:`~zenzic.core.shield.ShieldViolation`: When a secret is found
            in frontmatter content (only when ``shield_enabled=True``).
    """
    cache: dict[str, FileMetadata] = {}
    for abs_path, content in md_contents.items():
        try:
            rel = abs_path.relative_to(docs_root)
        except ValueError:
            continue

        # Shield check on frontmatter lines if enabled.
        if shield_enabled:
            fm_match = _FRONTMATTER_RE.match(content)
            if fm_match:
                from zenzic.core.shield import safe_read_line

                fm_text = fm_match.group(1)
                # Find the line offset of frontmatter start.
                prefix = content[: fm_match.start()]
                start_line = prefix.count("\n") + 2  # +1 for 1-based, +1 for --- line
                for i, line in enumerate(fm_text.split("\n")):
                    safe_read_line(line, abs_path, start_line + i)

        cache[rel.as_posix()] = FileMetadata(
            slug=extract_frontmatter_slug(content),
            draft=extract_frontmatter_draft(content),
            unlisted=extract_frontmatter_unlisted(content),
            tags=extract_frontmatter_tags(content),
        )
    return cache
