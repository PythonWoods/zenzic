# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Validation logic: native link checking (internal + external) and snippet checks.

Link validation no longer invokes any external process.  Instead it uses a
pure-Python two-pass approach:

1. Read every ``.md`` file under ``docs/`` into memory, extract all Markdown
   links while skipping fenced code blocks and inline code spans.
2. *Internal links* (relative or site-absolute paths) are resolved against the
   pre-built in-memory file map; ``#anchor`` fragments are validated against
   heading slugs extracted from the target file.
3. *External links* (``http://`` / ``https://``) are validated lazily — only
   when ``strict=True`` — via concurrent HEAD requests through ``httpx``.

Snippet validation supports four languages using pure-Python parsers:

- **Python** (``python``, ``py``) — ``compile()`` in ``exec`` mode
- **YAML** (``yaml``, ``yml``) — ``yaml.safe_load()``
- **JSON** (``json``) — ``json.loads()``
- **TOML** (``toml``) — ``tomllib.loads()`` (stdlib 3.11+)

No subprocesses are spawned for any language.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import fnmatch
import json
import os
import re
import tomllib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, NamedTuple
from urllib.parse import urlsplit

import httpx
import yaml

from zenzic.core.adapter import get_adapter
from zenzic.core.discovery import DOC_SUFFIXES, iter_markdown_sources, walk_files
from zenzic.core.resolver import (
    AnchorMissing,
    FileNotFound,
    InMemoryPathResolver,
    PathTraversal,
    Resolved,
)
from zenzic.models.config import ZenzicConfig
from zenzic.models.references import ReferenceMap
from zenzic.models.vsm import build_vsm


# ─── YAML loader (boundary layer — ignores unknown tags like MkDocs !ENV) ────


class _PermissiveSafeLoader(yaml.SafeLoader):
    """SafeLoader that silently ignores unknown YAML tags (e.g. MkDocs !ENV)."""


_PermissiveSafeLoader.add_multi_constructor("", lambda loader, tag_suffix, node: None)  # type: ignore[no-untyped-call]


# ─── Regexes ──────────────────────────────────────────────────────────────────

# Matches inline Markdown links [text](url) and images ![alt](url).
# Captures the raw content inside the parentheses (group 1).
# Does NOT match reference-style links [text][id] or auto-links <url>.
_MARKDOWN_LINK_RE = re.compile(r"!?\[[^\[\]]*\]\(([^)]+)\)")


class LinkInfo(NamedTuple):
    """Extracted link with source position for surgical caret rendering."""

    url: str
    lineno: int
    col_start: int = 0
    match_text: str = ""


# Matches ATX headings: ``# Heading``, ``## Sub``, etc. (multiline mode).
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+)", re.MULTILINE)

# Matches MkDocs Material explicit anchor attribute: ``{ #custom-id }``
_EXPLICIT_ANCHOR_RE = re.compile(r"\{[^}]*#([\w-]+)[^}]*\}")

# Matches HTML tags to strip from heading text before slugification.
_HTML_TAG_RE = re.compile(r"<[^>]+>")

# Reference definition: [id]: url  (up to 3 leading spaces per CommonMark §4.7)
_REF_DEF_RE = re.compile(r"^ {0,3}\[([^\]]+)\]:\s+(\S+)")

# Reference link: [text][id] or [text][] (collapsed reference)
_REF_LINK_RE = re.compile(r"\[([^\]]*)\]\[([^\]]*)\]")

# Shortcut reference link: [text] NOT followed by [ ( or : (CommonMark §4.7)
# (?<!\]) prevents matching the second part of [text][id] full/collapsed refs.
_REF_SHORTCUT_RE = re.compile(r"(?<![!\]])\[([^\]]+)\](?![\[(:])")

# URL schemes that are valid syntax but point to non-HTTP targets we skip.
_SKIP_SCHEMES = ("mailto:", "data:", "ftp:", "tel:", "javascript:", "irc:", "xmpp:")

# Maximum number of simultaneous outbound HTTP connections during external link checks.
# Prevents exhausting OS file descriptors and avoids triggering rate-limits on target servers.
_MAX_CONCURRENT_REQUESTS = 20

# Files at or above this threshold use parallel worker indexing for anchors
# and resolved links before the global validation phase runs.
VALIDATION_PARALLEL_THRESHOLD = 50


# ─── Data classes ─────────────────────────────────────────────────────────────


@dataclass(slots=True)
class SnippetError:
    file_path: Path
    line_no: int
    message: str


@dataclass(slots=True)
class LinkError:
    """A single link validation finding with source context for rich rendering.

    Attributes:
        file_path:   Absolute path of the source file containing the link.
        line_no:     1-based line number of the offending link.
        message:     Human-readable error description.
        source_line: The raw source line from the file (stripped), used by
                     the CLI to render the Visual Snippet indicator ``│``.
                     Empty string when the line cannot be retrieved.
        error_type:  Machine-readable category, e.g. ``'UNREACHABLE_LINK'``,
                     ``'FILE_NOT_FOUND'``, ``'ANCHOR_MISSING'``, etc.
    """

    file_path: Path
    line_no: int
    message: str
    source_line: str = ""
    error_type: str = "LINK_ERROR"
    col_start: int = 0
    match_text: str = ""

    def __str__(self) -> str:
        """Flat string form — backwards-compatible with the old list[str] API."""
        return self.message


# ─── Path-traversal intent classifier ────────────────────────────────────────

# Detects hrefs that, after traversal, would reach an OS system directory.
# Triggering this classifier upgrades a PATH_TRAVERSAL error to a
# PATH_TRAVERSAL_SUSPICIOUS security incident (Exit Code 3).
_RE_SYSTEM_PATH: re.Pattern[str] = re.compile(r"/(?:etc|root|var|proc|sys|usr)/")


def _classify_traversal_intent(href: str) -> Literal["suspicious", "boundary"]:
    """Return 'suspicious' when *href* appears to target an OS system directory.

    A traversal to ``../../../../etc/passwd`` is a potential attack vector.
    A traversal to ``../../sibling-repo/README.md`` is a boundary violation
    but has no OS-exploitation intent.  Only the former warrants Exit Code 3.

    This check intentionally remains a fast regex scan over the raw href
    string — no filesystem calls, no Path resolution — to stay within the
    Zero I/O constraint of the validator hot-path.
    """
    return "suspicious" if _RE_SYSTEM_PATH.search(href) else "boundary"


def _build_link_graph(
    links_cache: dict[Path, list[LinkInfo]],
    resolver: InMemoryPathResolver,
    source_files: frozenset[Path],
) -> dict[Path, set[Path]]:
    """Build the adjacency map of internal Markdown→Markdown links.

    Only edges between files present in *source_files* are recorded.
    External links, fragment-only links, and links to Ghost Routes are
    excluded — Ghost Routes have no outgoing edges so they cannot be
    members of a cycle.

    This is called once after the InMemoryPathResolver is constructed
    (Phase 1.5).  The resolver is already warm; no additional I/O occurs.
    """
    adj: dict[Path, set[Path]] = {f: set() for f in source_files}
    for md_file, links in links_cache.items():
        for link in links:
            url = link.url
            # Skip external URLs, non-navigable schemes, and fragment-only links
            if (
                url.startswith(_SKIP_SCHEMES)
                or url.startswith(("http://", "https://"))
                or not url
                or url.startswith("#")
            ):
                continue
            outcome = resolver.resolve(md_file, url)
            if isinstance(outcome, Resolved) and outcome.target in source_files:
                adj.setdefault(md_file, set()).add(outcome.target)
    return adj


def _find_cycles_iterative(adj: dict[Path, set[Path]]) -> frozenset[str]:
    """Return canonical Path strings of all nodes that participate in at least one cycle.

    Iterative DFS with WHITE/GREY/BLACK colouring — avoids RecursionError on
    large documentation graphs (Pillar 2: Zero Subprocess / total portability).
    """
    WHITE, GREY, BLACK = 0, 1, 2
    color: dict[Path, int] = dict.fromkeys(adj, WHITE)
    in_cycle: set[str] = set()

    for start in list(adj):
        if color[start] != WHITE:
            continue
        stack: list[tuple[Path, Iterator[Path]]] = [(start, iter(adj[start]))]
        path: list[Path] = [start]
        path_set: set[Path] = {start}
        color[start] = GREY

        while stack:
            node, nbrs = stack[-1]
            try:
                nbr = next(nbrs)
                if nbr not in color:
                    color[nbr] = WHITE
                    adj.setdefault(nbr, set())
                if color[nbr] == GREY:  # back edge → cycle
                    idx = path.index(nbr)
                    in_cycle.update(str(p) for p in path[idx:])
                    in_cycle.add(str(nbr))
                elif color[nbr] == WHITE:
                    color[nbr] = GREY
                    stack.append((nbr, iter(adj.get(nbr, set()))))
                    path.append(nbr)
                    path_set.add(nbr)
            except StopIteration:
                done = path[-1]
                color[done] = BLACK
                path.pop()
                path_set.discard(done)
                stack.pop()

    return frozenset(in_cycle)


class _ValidationPayload(NamedTuple):
    """Worker output for one markdown file in link validation phase 1.

    Attributes:
        file_path: Absolute markdown file path.
        anchors: Heading anchor slugs extracted from the file.
        links: Resolved links from inline and reference-style syntax.
        source_lines: Source split by lines for O(1) error-context lookup.
    """

    file_path: Path
    anchors: set[str]
    links: list[LinkInfo]
    source_lines: list[str]


def _index_file_for_validation(args: tuple[Path, str]) -> _ValidationPayload:
    """Phase 1 worker: extract anchors and links for one markdown file.

    Runs as a pure function so it can be dispatched safely to a process pool.
    """
    md_file, content = args
    ref_map = _build_ref_map(content)
    all_links = extract_links(content) + extract_ref_links(content, ref_map)
    return _ValidationPayload(
        file_path=md_file,
        anchors=anchors_in_file(content),
        links=all_links,
        source_lines=content.splitlines(),
    )


# ─── Pure / I/O-agnostic functions ────────────────────────────────────────────


def extract_links(text: str) -> list[LinkInfo]:
    """Extract ``[text](url)`` and ``![alt](url)`` links from raw Markdown.

    Skips content inside fenced code blocks (````` ``` ````` / ``~~~``) and
    inline code spans (`` ` `` ) so that example links in documentation are
    never mistaken for real targets.  Optional link titles (``"title"`` /
    ``'title'``) are stripped so callers receive clean URL strings.

    Args:
        text: Raw markdown content.

    Returns:
        List of :class:`LinkInfo` with URL, line number, column, and match text.
    """
    results: list[LinkInfo] = []
    in_block = False

    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()

        # ── Fenced code block boundary tracking ──────────────────────────────
        if not in_block:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_block = True
                continue
        else:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_block = False
            continue  # always skip lines inside a fenced block

        # ── Inline code: blank out `...` spans to prevent false matches ───────
        clean = re.sub(r"`[^`]+`", lambda m: " " * len(m.group()), line)

        for m in _MARKDOWN_LINK_RE.finditer(clean):
            raw = m.group(1).strip()
            if not raw:
                continue
            # Strip optional title portion: url "title" or url 'title'
            url = re.sub(r"""\s+["'].*$""", "", raw).strip()
            if url:
                results.append(
                    LinkInfo(
                        url=url,
                        lineno=lineno,
                        col_start=m.start(),
                        match_text=m.group(0),
                    )
                )

    return results


def slug_heading(heading: str) -> str:
    """Convert heading text to a URL-safe anchor slug (GitHub / MkDocs compatible).

    Handles MkDocs Material explicit anchor syntax (``{ #custom-id }``) and
    strips HTML tags (e.g. ``<small>``) before slugification.

    Resolution order:
    1. If the heading contains ``{ #custom-id }``, return ``custom-id`` directly.
    2. Otherwise strip HTML tags, lowercase, apply NFKD Unicode normalisation to
       decompose accented characters (e.g. ``à`` → ``a`` + combining grave), drop
       all combining/non-ASCII characters, then drop remaining non-word characters
       (keeping hyphens) and collapse whitespace into single hyphens — matching
       the behaviour of Python-Markdown's ``toc`` extension and GitHub heading IDs.

    Args:
        heading: Raw heading text without leading ``#`` characters.

    Returns:
        Lowercase hyphenated anchor slug (e.g. ``'quick-start'``).
    """
    import unicodedata

    explicit = _EXPLICIT_ANCHOR_RE.search(heading)
    if explicit:
        return explicit.group(1).lower()
    slug = _HTML_TAG_RE.sub("", heading).strip()
    # Decompose accented characters and drop combining marks so that e.g.
    # "Integrità" → "integrita" (matching MkDocs toc extension behaviour).
    # Lowercase AFTER NFKD so that mathematical/styled Unicode codepoints
    # (e.g. U+1D400 𝐀 → A) are correctly lowered.
    slug = unicodedata.normalize("NFKD", slug)
    slug = "".join(c for c in slug if not unicodedata.combining(c))
    slug = slug.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug).strip("-")
    return slug


def anchors_in_file(content: str) -> set[str]:
    """Return anchor slugs for every ATX heading in *content*.

    Recognises MkDocs Material explicit anchors (``{ #id }``) and strips HTML
    tags from heading text before slugification.

    Args:
        content: Raw markdown content (no I/O).

    Returns:
        Set of lowercase anchor slugs, e.g. ``{'introduction', 'quick-start'}``.
    """
    return {slug_heading(m.group(1)) for m in _HEADING_RE.finditer(content)}


# ─── Reference link pure helpers (S4-4) ──────────────────────────────────────


def _build_ref_map(text: str) -> dict[str, str]:
    """Extract link reference definitions from markdown content.  No I/O.

    Skips fenced code blocks so that reference definitions inside example
    code are never collected.  First-definition-wins per CommonMark §4.7.
    Reference IDs are lowercased for case-insensitive lookup.

    Args:
        text: Raw markdown content.

    Returns:
        Mapping of lowercase-normalised reference IDs to their URL targets.
    """
    ref_map: dict[str, str] = {}
    in_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if not in_block:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_block = True
                continue
            m = _REF_DEF_RE.match(line)
            if m:
                norm_id = m.group(1).lower().strip()
                if norm_id not in ref_map:  # first-definition-wins
                    ref_map[norm_id] = m.group(2)
        else:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_block = False
    return ref_map


def extract_ref_links(text: str, ref_map: dict[str, str]) -> list[LinkInfo]:
    """Resolve reference-style links against *ref_map* and return :class:`LinkInfo` items.

    Handles ``[text][id]`` and collapsed ``[text][]`` syntax.  Skips fenced
    code blocks and inline code spans.  Only links whose normalised ID appears
    in *ref_map* are returned — undefined IDs are the responsibility of
    :class:`~zenzic.core.scanner.ReferenceScanner`.

    Reference IDs are compared case-insensitively per CommonMark §4.7.

    Args:
        text: Raw markdown content.
        ref_map: Mapping returned by :func:`_build_ref_map` (lowercase IDs).

    Returns:
        List of :class:`LinkInfo` with resolved URLs and source positions.
    """
    results: list[LinkInfo] = []
    in_block = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not in_block:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_block = True
                continue
        else:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_block = False
            continue
        clean = re.sub(r"`[^`]+`", lambda m: " " * len(m.group()), line)
        for m in _REF_LINK_RE.finditer(clean):
            text_part = m.group(1)
            raw_id = m.group(2) if m.group(2) else text_part
            ref_id = raw_id.lower().strip()
            if not ref_id:
                continue
            url = ref_map.get(ref_id)
            if url:
                results.append(
                    LinkInfo(
                        url=url,
                        lineno=lineno,
                        col_start=m.start(),
                        match_text=m.group(0),
                    )
                )
        # Shortcut reference links: [text] (CommonMark §4.7)
        for m in _REF_SHORTCUT_RE.finditer(clean):
            ref_id = m.group(1).lower().strip()
            url = ref_map.get(ref_id)
            if url:
                results.append(
                    LinkInfo(
                        url=url,
                        lineno=lineno,
                        col_start=m.start(),
                        match_text=m.group(0),
                    )
                )
    return results


# ─── Async I/O helpers ────────────────────────────────────────────────────────


async def _ping_url(client: httpx.AsyncClient, url: str) -> str | None:
    """HEAD-ping a single URL; returns an error string or ``None`` if reachable.

    Falls back to GET when the server returns 405 Method Not Allowed.
    Treats HTTP 401 / 403 / 429 as "alive" — the server is responding but
    restricting access, which is common for GitHub, StackOverflow, etc.
    """
    try:
        response = await client.head(url)
        if response.status_code == 405:
            response = await client.get(url)
        if response.status_code in (401, 403, 429):
            return None
        if response.status_code >= 400:
            return f"external link '{url}' returned HTTP {response.status_code}"
        return None
    except httpx.TimeoutException:
        return f"external link '{url}' timed out (>10 s)"
    except httpx.RequestError as exc:
        return f"external link '{url}' — connection error: {exc}"


async def _check_external_links(
    entries: list[tuple[str, str, int]],
) -> list[str]:
    """Concurrently validate a batch of external URLs.

    Deduplicates URLs so each is pinged exactly once, then maps any error back
    to every ``(file_label, lineno)`` pair that referenced that URL.

    Args:
        entries: List of ``(url, file_label, line_no)`` tuples.

    Returns:
        Sorted list of human-readable error strings.
    """
    if not entries:
        return []

    # Deduplicate: url → list[(label, lineno)]
    url_occurrences: dict[str, list[tuple[str, int]]] = {}
    for url, label, lineno in entries:
        url_occurrences.setdefault(url, []).append((label, lineno))

    headers = {
        "User-Agent": (
            "Zenzic-Documentation-Linter/0.1.0 (+https://github.com/PythonWoods/zenzic)"
        ),
        "Accept": "text/html,application/xhtml+xml,*/*",
    }

    semaphore = asyncio.Semaphore(_MAX_CONCURRENT_REQUESTS)

    async def _bounded_ping(client: httpx.AsyncClient, url: str) -> str | None:
        async with semaphore:
            return await _ping_url(client, url)

    errors: list[str] = []
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=10.0,
        headers=headers,
    ) as client:
        unique_urls = list(url_occurrences)
        results = await asyncio.gather(
            *(_bounded_ping(client, u) for u in unique_urls),
            return_exceptions=True,
        )

        for url, result in zip(unique_urls, results, strict=True):
            if result is None:
                continue
            msg = str(result) if isinstance(result, Exception) else result
            for label, lineno in url_occurrences[url]:
                errors.append(f"{label}:{lineno}: {msg}")

    return sorted(errors)


# ─── Main link validator ──────────────────────────────────────────────────────


async def validate_links_async(
    repo_root: Path,
    *,
    strict: bool = False,
    structured: bool = False,
) -> list[str] | list[LinkError]:
    """Native link validator — no subprocesses, no MkDocs dependency.

    **Internal links** (always checked):
        Relative and site-absolute paths are resolved against the ``docs/``
        directory.  The target file must exist within the scanned ``.md`` file
        set.  ``#anchor`` fragments are validated against heading slugs
        extracted from the destination file's content.

    **External links** (``strict=True`` only):
        Concurrent HEAD requests via ``httpx`` verify that HTTP / HTTPS URLs
        return a successful or access-restricted response.

    Args:
        repo_root:  Repository root directory (must contain ``docs/``).
        strict:     When ``True``, also validate external HTTP/HTTPS links via
                    network.  Adds latency; disabled by default for fast CI runs.
        structured: When ``True``, return ``list[LinkError]`` with per-error
                    source-line context for rich CLI rendering.  When ``False``
                    (default), return the legacy ``list[str]`` for backwards
                    compatibility.

    Returns:
        ``list[str]`` (``structured=False``) or ``list[LinkError]``
        (``structured=True``); empty when all links pass.
    """
    config, _ = ZenzicConfig.load(repo_root)
    docs_root = (repo_root / config.docs_dir).resolve()

    if not docs_root.is_dir():
        return []

    # ── Instantiate the build-engine adapter (locale-aware path resolution) ──
    adapter = get_adapter(config.build_context, docs_root, repo_root)

    # ── Pass 1: read all .md/.mdx files + map all non-doc assets into memory ──
    md_contents: dict[Path, str] = {}
    for md_file in sorted(iter_markdown_sources(docs_root, config)):
        try:
            md_contents[md_file.resolve()] = md_file.read_text(encoding="utf-8")
        except OSError:
            continue

    # Build the asset map once — eliminates all Path.exists() calls from Pass 2.
    # Stores resolved absolute path strings so the Pass 2 lookup is a single
    # frozenset membership test (O(1), zero allocations per link).
    known_assets: frozenset[str] = frozenset(
        str(f.resolve())
        for f in walk_files(docs_root, set(config.excluded_dirs))
        if f.is_file() and not f.is_symlink() and f.suffix not in DOC_SUFFIXES
    )

    # ── Phase 1: parallel index (anchors + resolved links) ────────────────
    # Workers return immutable payloads. The main process only merges maps
    # and performs global validation (phase 2), avoiding order-dependent
    # false positives for file.md#anchor links.
    use_parallel_index = (
        len(md_contents) >= VALIDATION_PARALLEL_THRESHOLD and (os.cpu_count() or 1) > 1
    )
    if use_parallel_index:
        with concurrent.futures.ProcessPoolExecutor() as executor:
            payloads = list(executor.map(_index_file_for_validation, md_contents.items()))
    else:
        payloads = [_index_file_for_validation(item) for item in md_contents.items()]

    anchors_cache: dict[Path, set[str]] = {p.file_path: p.anchors for p in payloads}
    links_cache: dict[Path, list[LinkInfo]] = {p.file_path: p.links for p in payloads}
    source_lines_cache: dict[Path, list[str]] = {p.file_path: p.source_lines for p in payloads}

    # Instantiate the resolver ONCE — _lookup_map is built here, not per-link.
    # Instantiating inside the file loop would regenerate the map N times,
    # cancelling the 14× performance gain from the pre-computed flat dict.
    resolver = InMemoryPathResolver(docs_root, md_contents, anchors_cache)

    # ── Build the Virtual Site Map (VSM) ──────────────────────────────────────
    # The VSM maps every .md file to its canonical URL and routing status.
    # It is only meaningful when the adapter has a nav (MkDocs with mkdocs.yml);
    # for VanillaAdapter / Zensical every file is REACHABLE by definition.
    vsm = build_vsm(adapter, docs_root, md_contents, anchors_cache=anchors_cache)

    # ── Phase 1.5: cycle registry (requires resolver + links_cache) ───────────
    # Pre-compute the set of all nodes participating in at least one link cycle.
    # This Θ(V+E) DFS runs once here; Phase 2 checks are O(1) per resolved link.
    _source_files: frozenset[Path] = frozenset(md_contents)
    _link_adj = _build_link_graph(links_cache, resolver, _source_files)
    cycle_registry: frozenset[str] = _find_cycles_iterative(_link_adj)
    # ─────────────────────────────────────────────────────────────────────────

    # ── Phase 2: validate against global indexes ────────────────────────────
    internal_errors: list[LinkError] = []
    external_entries: list[tuple[str, str, int]] = []  # (url, file_label, lineno)

    def _source_line(md_file: Path, lineno: int) -> str:
        """Return the raw source line (1-based) from the pre-split cache."""
        lines = source_lines_cache.get(md_file, [])
        idx = lineno - 1
        return lines[idx].strip() if 0 <= idx < len(lines) else ""

    for md_file in md_contents:
        label = str(md_file.relative_to(docs_root))
        all_links = links_cache.get(md_file, [])

        for link in all_links:
            url, lineno = link.url, link.lineno
            # Skip non-navigable schemes and bare fragment-only links
            if url.startswith(_SKIP_SCHEMES) or url == "#":
                continue

            parsed = urlsplit(url)

            # ── External links ────────────────────────────────────────────────
            if parsed.scheme in ("http", "https"):
                external_entries.append((url, label, lineno))
                continue

            # Pure same-page anchor (#section) — validated only when
            # validate_same_page_anchors is enabled in zenzic.toml.
            if not parsed.path:
                if config.validate_same_page_anchors and parsed.fragment:
                    anchor = parsed.fragment
                    if anchor not in anchors_cache.get(md_file, set()):
                        internal_errors.append(
                            LinkError(
                                file_path=md_file,
                                line_no=lineno,
                                message=f"{label}:{lineno}: anchor '#{anchor}' not found in '{label}'",
                                source_line=_source_line(md_file, lineno),
                                error_type="ANCHOR_MISSING",
                                col_start=link.col_start,
                                match_text=link.match_text,
                            )
                        )
                continue

            # ── Absolute-path prohibition ─────────────────────────────────────
            # Links starting with "/" are environment-dependent: they resolve
            # against the server root, not the docs root. This breaks hosting
            # in subdirectories (e.g. site.io/docs/) and engine-agnosticism.
            # Internal links must always be relative. Full URLs (https://...)
            # are handled above as external links and are not affected.
            if parsed.path.startswith("/"):
                internal_errors.append(
                    LinkError(
                        file_path=md_file,
                        line_no=lineno,
                        message=(
                            f"{label}:{lineno}: '{url}' uses an absolute path — "
                            "use a relative path (e.g. '../' or './') instead; "
                            "absolute paths break portability when the site is hosted "
                            "in a subdirectory"
                        ),
                        source_line=_source_line(md_file, lineno),
                        error_type="ABSOLUTE_PATH",
                        col_start=link.col_start,
                        match_text=link.match_text,
                    )
                )
                continue

            # ── Internal resolution: delegate entirely to InMemoryPathResolver ─
            # The resolver receives the raw href; it handles percent-decoding,
            # backslash normalisation, normpath, Shield check, and anchor lookup.
            # Do NOT pre-process the url before passing it — double-decoding
            # would corrupt links with legitimately encoded characters.
            match resolver.resolve(md_file, url):
                case PathTraversal():
                    # Security finding — path escaped the docs root.
                    # Classify intent: hrefs targeting OS system directories
                    # are promoted to PATH_TRAVERSAL_SUSPICIOUS (Exit Code 3).
                    _intent = _classify_traversal_intent(url)
                    internal_errors.append(
                        LinkError(
                            file_path=md_file,
                            line_no=lineno,
                            message=f"{label}:{lineno}: '{url}' resolves outside the docs directory",
                            source_line=_source_line(md_file, lineno),
                            error_type=(
                                "PATH_TRAVERSAL_SUSPICIOUS"
                                if _intent == "suspicious"
                                else "PATH_TRAVERSAL"
                            ),
                            col_start=link.col_start,
                            match_text=link.match_text,
                        )
                    )
                case FileNotFound(path_part=path_part):
                    # Non-Markdown assets are not tracked in md_contents.  Resolve
                    # the target to a normalised absolute path string and check
                    # against known_assets — the frozenset built in Pass 1.
                    # No disk I/O in the hot path.
                    if path_part.startswith("/"):
                        asset_str = os.path.normpath(
                            str(docs_root) + os.sep + path_part.lstrip("/")
                        )
                    else:
                        asset_str = os.path.normpath(str(md_file.parent) + os.sep + path_part)
                    if asset_str not in known_assets:
                        # Check adapter fallback before reporting: the build engine
                        # serves the default-locale asset when a locale-specific
                        # copy is absent.  Suppress the error when the fallback exists.
                        if adapter.resolve_asset(Path(asset_str), docs_root) is not None:
                            continue
                        # Suppress errors for build-time generated artifacts
                        # (e.g. PDFs from to-pdf plugin, ZIPs assembled in CI).
                        rel_asset = Path(asset_str).relative_to(docs_root).as_posix()
                        if not any(
                            fnmatch.fnmatch(rel_asset, pat)
                            for pat in config.excluded_build_artifacts
                        ):
                            internal_errors.append(
                                LinkError(
                                    file_path=md_file,
                                    line_no=lineno,
                                    message=f"{label}:{lineno}: '{path_part}' not found in docs",
                                    source_line=_source_line(md_file, lineno),
                                    error_type="FILE_NOT_FOUND",
                                    col_start=link.col_start,
                                    match_text=link.match_text,
                                )
                            )
                case AnchorMissing(path_part=path_part, anchor=anchor, resolved_file=resolved_file):
                    # Mirror the FileNotFound i18n fallback: when a locale file
                    # exists but lacks the anchor (because headings are translated),
                    # suppress the error if the anchor is present in the
                    # default-locale equivalent file.  The build engine serves the
                    # default-locale page for this anchor at build time.
                    if adapter.resolve_anchor(resolved_file, anchor, anchors_cache, docs_root):
                        continue
                    internal_errors.append(
                        LinkError(
                            file_path=md_file,
                            line_no=lineno,
                            message=f"{label}:{lineno}: anchor '#{anchor}' not found in '{path_part}'",
                            source_line=_source_line(md_file, lineno),
                            error_type="ANCHOR_MISSING",
                            col_start=link.col_start,
                            match_text=link.match_text,
                        )
                    )
                case Resolved(target=resolved_target):
                    # ── CIRCULAR_LINK: resolved target is part of a link cycle ─
                    if str(resolved_target) in cycle_registry:
                        internal_errors.append(
                            LinkError(
                                file_path=md_file,
                                line_no=lineno,
                                message=(
                                    f"{label}:{lineno}: '{url}' is part of a circular link cycle"
                                ),
                                source_line=_source_line(md_file, lineno),
                                error_type="CIRCULAR_LINK",
                                col_start=link.col_start,
                                match_text=link.match_text,
                            )
                        )
                    # ── UNREACHABLE_LINK: file exists but cannot be reached ───
                    # Fires when the adapter has a build config and the resolved
                    # target maps to a route that is either:
                    #   - ORPHAN_BUT_EXISTING: file exists but not in MkDocs nav
                    #   - IGNORED: file in a _private/ dir (Zensical) or an
                    #     unlisted README.md — engine will never serve it
                    if adapter.has_engine_config():
                        try:
                            target_rel = resolved_target.relative_to(docs_root)
                        except ValueError:
                            pass  # target outside docs_root — already handled by Shield
                        else:
                            target_url = adapter.map_url(target_rel)
                            route = vsm.get(target_url)
                            if route is not None and route.status in (
                                "ORPHAN_BUT_EXISTING",
                                "IGNORED",
                            ):
                                internal_errors.append(
                                    LinkError(
                                        file_path=md_file,
                                        line_no=lineno,
                                        message=(
                                            f"{label}:{lineno}: '{target_rel.as_posix()}' resolves "
                                            f"to '{target_url}' which exists on disk but is not "
                                            "listed in the site navigation (UNREACHABLE_LINK) — "
                                            "add it to nav in mkdocs.yml or remove the link"
                                        ),
                                        source_line=_source_line(md_file, lineno),
                                        error_type="UNREACHABLE_LINK",
                                        col_start=link.col_start,
                                        match_text=link.match_text,
                                    )
                                )

    internal_errors.sort(key=lambda e: e.message)

    if not strict:
        if structured:
            return internal_errors
        return [e.message for e in internal_errors]

    # ── Pass 3 (strict only): validate external links ─────────────────────────
    excluded = config.excluded_external_urls
    if excluded:
        external_entries = [
            (url, label, lineno)
            for url, label, lineno in external_entries
            if not any(url.startswith(prefix) for prefix in excluded)
        ]
    ext_error_strs = await _check_external_links(external_entries)
    ext_link_errors = [
        LinkError(
            file_path=docs_root,  # no single file context for external errors
            line_no=0,
            message=msg,
            source_line="",
            error_type="EXTERNAL_LINK",
        )
        for msg in ext_error_strs
    ]
    all_errors: list[LinkError] = internal_errors + ext_link_errors
    if structured:
        return all_errors
    return [e.message for e in all_errors]


def generate_virtual_site_map(docs_root: Path, docs_structure: str) -> frozenset[str]:
    """Project the set of URL paths the build engine will generate.

    This is a pure function: given a directory of Markdown source files and
    a ``docs_structure`` strategy, it returns the exact set of URL paths that
    the build engine (Zensical / MkDocs) will produce — without running the
    build.

    Transformation rules (empirically verified against Zensical 0.0.27):

    * ``docs/page.md``        → ``/page/``      (default locale)
    * ``docs/page.it.md``     → ``/page.it/``   (suffix mode — locale in stem)
    * ``docs/index.md``       → ``/``           (root index special case)
    * ``docs/dir/page.md``    → ``/dir/page/``
    * ``docs/dir/index.md``   → ``/dir/``       (directory index special case)

    The function does **not** discriminate between locales or docs_structure
    strategies beyond walking the files — any ``.md`` file that exists on disk
    will be served at a deterministic URL.

    Args:
        docs_root: Path to the ``docs/`` directory.
        docs_structure: Value of ``docs_structure`` from the i18n plugin config
            (``"suffix"`` or ``"folder"``).  Currently unused — the URL
            projection is the same regardless of strategy because in suffix mode
            the locale is encoded in the filename stem, not in a directory
            prefix.  Kept as a parameter for future folder-mode support.

    Returns:
        Frozenset of URL path strings (e.g. ``{"/", "/checks.it/", ...}``).
    """
    urls: set[str] = set()
    if not docs_root.is_dir():
        return frozenset()
    for md_file in docs_root.rglob("*"):
        if md_file.suffix not in DOC_SUFFIXES:
            continue
        rel = md_file.relative_to(docs_root)
        # Strip .md suffix → path stem
        stem = rel.with_suffix("")
        parts = list(stem.parts)
        if not parts:
            continue
        # Directory index: dir/index → /dir/
        if parts[-1] == "index":
            parts = parts[:-1]
        if not parts:
            urls.add("/")
        else:
            urls.add("/" + "/".join(parts) + "/")
    return frozenset(urls)


def check_nav_contract(repo_root: Path) -> list[str]:
    """Validate ``extra.alternate`` links against the Virtual Site Map.

    Loads ``mkdocs.yml``, projects the full set of URLs the build engine will
    generate via :func:`generate_virtual_site_map`, then checks that every
    ``extra.alternate`` link resolves to a URL that exists in that map.

    No heuristics, no regex on URL patterns.  If a link is not in the VSM,
    it is a 404 — regardless of *why* the author wrote it.

    Args:
        repo_root: Repository root directory.

    Returns:
        List of human-readable error strings (empty = no violations).
    """
    from zenzic.core.adapter import find_config_file

    errors: list[str] = []
    config_file = find_config_file(repo_root)
    if config_file is None:
        return errors
    with config_file.open(encoding="utf-8") as f:
        try:
            doc_config: dict[str, Any] = yaml.load(f, Loader=_PermissiveSafeLoader) or {}
        except yaml.YAMLError:
            return errors

    # ── Extract docs_structure ────────────────────────────────────────────────
    docs_structure: str = "suffix"  # default assumption
    plugins = doc_config.get("plugins", [])
    if isinstance(plugins, list):
        for plugin in plugins:
            if not isinstance(plugin, dict):
                continue
            i18n = plugin.get("i18n")
            if not isinstance(i18n, dict):
                continue
            docs_structure = i18n.get("docs_structure", "suffix")
            break

    # ── Build the Virtual Site Map ────────────────────────────────────────────
    docs_dir = doc_config.get("docs_dir", "docs")
    docs_root_path = repo_root / docs_dir
    vsm = generate_virtual_site_map(docs_root_path, docs_structure)

    # ── Validate every extra.alternate link against the VSM ──────────────────
    extra = doc_config.get("extra") or {}
    alternate = extra.get("alternate", []) if isinstance(extra, dict) else []
    if not isinstance(alternate, list):
        return errors

    for entry in alternate:
        if not isinstance(entry, dict):
            continue
        link: str = entry.get("link", "")
        lang: str = entry.get("lang", "")
        if not link:
            continue
        # Normalise: ensure trailing slash for directory-style URLs
        normalised = link if link.endswith("/") else link + "/"
        if normalised not in vsm:
            errors.append(
                f"mkdocs.yml extra.alternate[{lang}]: link '{link}' does not "
                f"correspond to any URL the build engine will generate. "
                f"The Virtual Site Map contains no entry for '{normalised}'. "
                f"Use a path that maps to an existing source file "
                f"(e.g. '/index.{lang}/' for the {lang} home page)."
            )
    return errors


def validate_links(repo_root: Path, *, strict: bool = False) -> list[str]:
    """Synchronous wrapper around :func:`validate_links_async`.

    Always checks internal links (no network).  Pass ``strict=True`` to also
    fire HTTP HEAD requests against every external URL found in the docs.

    Args:
        repo_root: Repository root directory.
        strict: Include external HTTP/HTTPS link checks (requires network).

    Returns:
        Sorted list of human-readable error strings.
    """
    result = asyncio.run(validate_links_async(repo_root, strict=strict, structured=False))
    assert isinstance(result, list)
    return result  # type: ignore[return-value]


def validate_links_structured(
    repo_root: Path,
    *,
    strict: bool = False,
) -> list[LinkError]:
    """Synchronous wrapper that returns rich :class:`LinkError` objects.

    Identical to :func:`validate_links` but returns structured findings with
    ``source_line`` and ``error_type`` populated, enabling the CLI to render
    Visual Snippets with the ``│`` indicator.

    Args:
        repo_root: Repository root directory.
        strict: Include external HTTP/HTTPS link checks (requires network).

    Returns:
        Sorted list of :class:`LinkError` objects; empty when all links pass.
    """
    result = asyncio.run(validate_links_async(repo_root, strict=strict, structured=True))
    assert isinstance(result, list)
    return result  # type: ignore[return-value]


# ─── Multi-language snippet validation ────────────────────────────────────────

_VALIDATABLE_LANGS = frozenset({"python", "py", "yaml", "yml", "json", "toml"})


def _extract_code_blocks(text: str) -> list[tuple[str, str, int]]:
    """Return (lang, snippet, fence_line_no) triples for every validatable fenced block.

    Only blocks whose language tag is in ``_VALIDATABLE_LANGS`` are returned.
    Uses a deterministic line-by-line state machine rather than a regex so that
    inline triple-backtick code spans (e.g. `` ` ```python ` ``) cannot cause
    the matcher to run away across the rest of the file.

    *fence_line_no* is the 1-based line number of the opening fence.  The closing
    fence must be a line whose stripped content is exactly three or more backticks
    (per CommonMark §4.5).
    """
    blocks: list[tuple[str, str, int]] = []
    in_block = False
    current_lang = ""
    block_lines: list[str] = []
    fence_line_no = 0

    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not in_block:
            if stripped.startswith("```"):
                info = stripped[3:].strip()
                lang = info.split()[0].lower() if info else ""
                if lang in _VALIDATABLE_LANGS:
                    in_block = True
                    current_lang = lang
                    block_lines = []
                    fence_line_no = lineno
        else:
            # Closing fence: line is only backtick characters (at least 3)
            if stripped.startswith("```") and not stripped.lstrip("`"):
                blocks.append((current_lang, "\n".join(block_lines), fence_line_no))
                in_block = False
                block_lines = []
            else:
                block_lines.append(line)

    return blocks


def check_snippet_content(
    text: str,
    file_path: Path | str,
    config: ZenzicConfig | None = None,
) -> list[SnippetError]:
    """Pure function: validate fenced code blocks in text using pure-Python parsers. No I/O.

    Supported languages:

    - **Python** (``python``, ``py``) — ``compile()`` in ``exec`` mode
    - **YAML** (``yaml``, ``yml``) — ``yaml.safe_load()``
    - **JSON** (``json``) — ``json.loads()``
    - **TOML** (``toml``) — ``tomllib.loads()``

    Args:
        text: Raw markdown content to analyse.
        file_path: Path identifier used to label errors (no disk access).
        config: Optional Zenzic configuration.

    Returns:
        List of SnippetError instances for each invalid code block.
    """
    if config is None:
        config = ZenzicConfig()

    path = Path(file_path)
    errors: list[SnippetError] = []

    for lang, snippet, fence_line in _extract_code_blocks(text):
        if len(snippet.strip().splitlines()) < config.snippet_min_lines:
            continue

        if lang in ("python", "py"):
            try:
                compile(snippet, str(path), "exec")
            except SyntaxError as exc:
                errors.append(
                    SnippetError(
                        file_path=path,
                        line_no=fence_line + (exc.lineno or 1),
                        message=f"SyntaxError in Python snippet — {exc.msg}",
                    )
                )
            except Exception as exc:
                errors.append(
                    SnippetError(
                        file_path=path,
                        line_no=fence_line + 1,
                        message=f"ParserError in Python snippet — {type(exc).__name__}: {exc}",
                    )
                )

        elif lang in ("yaml", "yml"):
            try:
                yaml.safe_load(snippet)
            except yaml.YAMLError as exc:
                errors.append(
                    SnippetError(
                        file_path=path,
                        line_no=fence_line + 1,
                        message=f"SyntaxError in YAML snippet — {exc}",
                    )
                )

        elif lang == "json":
            try:
                json.loads(snippet)
            except json.JSONDecodeError as exc:
                errors.append(
                    SnippetError(
                        file_path=path,
                        line_no=fence_line + exc.lineno,
                        message=f"SyntaxError in JSON snippet — {exc.msg}",
                    )
                )

        elif lang == "toml":
            try:
                tomllib.loads(snippet)
            except tomllib.TOMLDecodeError as exc:
                errors.append(
                    SnippetError(
                        file_path=path,
                        line_no=fence_line + 1,
                        message=f"SyntaxError in TOML snippet — {exc}",
                    )
                )

    return errors


# ─── Global reference-URL validator ──────────────────────────────────────────


class LinkValidator:
    """Cross-file URL deduplicator and async validator for reference definitions.

    Collects URLs registered from multiple :class:`~zenzic.models.references.ReferenceMap`
    instances and validates each *unique* URL exactly once via concurrent HEAD
    requests.  This guarantees that even if 50 docs all reference
    ``https://github.com``, only one HTTP ping is issued per session.

    Rate limiting is handled by a shared asyncio semaphore (inherited from
    ``_check_external_links``).  HTTP 429 and 401/403 responses are treated as
    "alive" to avoid false positives from access-restricted servers.

    Usage::

        validator = LinkValidator()

        # Register from each file's ReferenceMap after Pass 1
        for report_scanner in scanners:
            validator.register_from_map(report_scanner.ref_map, report_scanner.file_path)

        # One async pass — each unique URL pinged exactly once
        errors = validator.validate()

    Attributes:
        _registrations: Mapping of URL to the list of ``(file_path, line_no)``
            pairs that reference it.  The list enables accurate error attribution
            when multiple files define the same URL.
    """

    def __init__(self) -> None:
        # url → [(file_path, line_no), ...]  — deduplication key is the URL
        self._registrations: dict[str, list[tuple[Path, int]]] = {}

    def register(self, url: str, source: Path, line_no: int) -> None:
        """Register a single external URL for validation.

        Only ``http://`` and ``https://`` URLs are accepted; all others are
        silently ignored so callers do not need to pre-filter.

        Args:
            url: The raw URL string from the reference definition.
            source: Path to the file that contains the definition.
            line_no: 1-based line number of the definition.
        """
        if not url.startswith(("http://", "https://")):
            return
        self._registrations.setdefault(url, []).append((source, line_no))

    def register_from_map(self, ref_map: ReferenceMap, file_path: Path) -> None:
        """Register all HTTP/HTTPS URLs found in a :class:`ReferenceMap`.

        Iterates over every *accepted* definition in the map (first-wins entries
        only) and delegates to :meth:`register`.

        Args:
            ref_map: Fully-populated ReferenceMap from Pass 1.
            file_path: Source file that owns this map (used for error labels).
        """
        for _norm_id, (url, line_no) in ref_map.definitions.items():
            self.register(url, file_path, line_no)

    @property
    def unique_url_count(self) -> int:
        """Number of distinct URLs scheduled for validation."""
        return len(self._registrations)

    async def validate_async(self) -> list[str]:
        """Ping every registered URL exactly once and return error strings.

        Delegates to :func:`_check_external_links` which:
        - Enforces the semaphore cap (``_MAX_CONCURRENT_REQUESTS = 20``)
        - Falls back from HEAD to GET on 405 responses
        - Treats 401/403/429 as alive (access-restricted, not broken)
        - Maps each URL error back to *all* files that referenced it

        Returns:
            Sorted list of ``"file:lineno: <error message>"`` strings.
            Empty list when all URLs are reachable.
        """
        if not self._registrations:
            return []

        entries: list[tuple[str, str, int]] = [
            (url, str(occurrences[0][0]), occurrences[0][1])
            for url, occurrences in self._registrations.items()
        ]
        return await _check_external_links(entries)

    def validate(self) -> list[str]:
        """Synchronous wrapper around :meth:`validate_async`.

        Returns:
            Sorted list of error strings (empty when all URLs pass).
        """
        return asyncio.run(self.validate_async())


# ─── CLI / I/O wrappers ───────────────────────────────────────────────────────


def validate_snippets(repo_root: Path, config: ZenzicConfig | None = None) -> list[SnippetError]:
    """Validate every fenced code block (Python, YAML, JSON, TOML) in docs and report syntax errors.

    Args:
        repo_root: Path to the repository root.
        config: Optional Zenzic configuration.

    Returns:
        List of SnippetError objects detailing the issues.
    """
    if config is None:
        config = ZenzicConfig()

    docs_root = repo_root / config.docs_dir
    errors: list[SnippetError] = []

    if not docs_root.exists() or not docs_root.is_dir():
        return errors

    for md_file in sorted(iter_markdown_sources(docs_root, config)):
        rel_path = md_file.relative_to(docs_root)
        content = md_file.read_text(encoding="utf-8")
        errors.extend(check_snippet_content(content, rel_path, config))

    return errors
