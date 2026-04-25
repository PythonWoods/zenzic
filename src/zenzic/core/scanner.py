# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Filesystem scanning utilities: repo root discovery, orphan page detection,
placeholder scanning, and the Two-Pass Reference Pipeline.

v0.2.0 additions
----------------
* ``ReferenceScanner`` — stateful per-file scanner implementing the three-phase
  pipeline (Harvest → Cross-Check → Integrity Report).
* ``check_image_alt_text`` — pure function that flags images without alt text.
* ``scan_docs_references`` — I/O wrapper that runs ReferenceScanner over every
  .md file under docs/ and returns consolidated results.
"""

from __future__ import annotations

import fnmatch
import posixpath
import re
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote

from zenzic.core.adapter import get_adapter
from zenzic.core.discovery import (
    DOC_SUFFIXES,
    iter_locale_markdown_sources,
    iter_markdown_sources,
    walk_files,
)
from zenzic.core.reporter import Finding
from zenzic.core.rules import AdaptiveRuleEngine, BaseRule
from zenzic.core.shield import SecurityFinding, scan_lines_with_lookback, scan_url_for_secrets
from zenzic.core.validator import LinkValidator
from zenzic.models.config import (
    SYSTEM_EXCLUDED_FILE_NAMES,
    SYSTEM_EXCLUDED_FILE_PATTERNS,
    ZenzicConfig,
)
from zenzic.models.references import IntegrityReport, ReferenceFinding, ReferenceMap


if TYPE_CHECKING:
    from zenzic.core.exclusion import LayeredExclusionManager


# ─── Reference pipeline regexes ───────────────────────────────────────────────

# Reference definition: [id]: url  (up to 3 leading spaces per CommonMark §4.7)
# Optional title on the same line is ignored (we only need the URL for Shield scan).
_RE_REF_DEF = re.compile(r"^ {0,3}\[([^\]]+)\]:\s+(\S+)")

# Reference link usage: [text][id] or [text][] (collapsed reference).
# Negative lookbehind (?<!!) prevents matching image reference links ![alt][id].
_RE_REF_LINK = re.compile(r"(?<!!)(\[([^\]]*)\]\[([^\]]*)\])")

# Shortcut reference link: [text] NOT followed by [ ( or : (CommonMark §4.7).
# Negative lookbehinds: (?<!!) avoids image refs; (?<!\]) avoids matching the
# second bracket pair of full/collapsed refs [text][id].
_RE_REF_SHORTCUT = re.compile(r"(?<![!\]])\[([^\]]+)\](?![\[(:])")

# Inline image: ![alt](url)
_RE_IMAGE_INLINE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

# HTML image tag — captures the entire tag for alt extraction
_RE_HTML_IMG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_RE_HTML_ALT = re.compile(r'\balt=["\']([^"\']*)["\']', re.IGNORECASE)


_MARKDOWN_ASSET_LINK_RE = re.compile(r"!\[.*?\]\((.*?)\)|<img.*?src=[\"'](.*?)[\"'].*?>")


def find_repo_root(*, fallback_to_cwd: bool = False, search_from: Path | None = None) -> Path:
    """Walk upward from *search_from* (or CWD) until a Zenzic project root marker is found.

    Root markers (first match wins, checked in order):
    - ``.git/``  — universal VCS marker.
    - ``zenzic.toml`` — Zenzic's own configuration file.

    Using engine-neutral markers keeps the Core independent of any specific
    documentation build engine (e.g. ``mkdocs.yml`` is intentionally excluded).

    This is more robust than ``Path(__file__).parents[N]`` because it works
    regardless of where the CLI is invoked from inside the repo.

    Args:
        fallback_to_cwd: When *True* and no root marker is found, return the
            starting path instead of raising.  Use this only for bootstrap
            commands (``zenzic init``) that are explicitly designed to create a
            project root from scratch — the "Genesis Fallback".
        search_from: Optional starting path for the upward search.  When
            provided, the search begins here instead of ``Path.cwd()``.
            CEO-052 "The Sovereign Root Fix": pass the explicit target path so
            the project config follows the target, not the caller.

    Raises:
        RuntimeError: if no root marker is found in any ancestor and
            ``fallback_to_cwd`` is *False*.
    """
    start = search_from.resolve() if search_from is not None else Path.cwd().resolve()
    for candidate in [start, *start.parents]:
        if (candidate / ".git").is_dir() or (candidate / "zenzic.toml").is_file():
            return candidate

    if fallback_to_cwd:
        return start

    raise RuntimeError(
        "Could not locate repo root: no .git directory or zenzic.toml found in any "
        f"ancestor of {start}. Run Zenzic from inside the repository."
    )


# ─── Pure / I/O-agnostic functions ────────────────────────────────────────────


def calculate_orphans(all_md: set[str], nav_paths: set[str] | frozenset[str]) -> list[str]:
    """Pure function: return sorted list of .md paths present in all_md but absent from nav_paths.

    Args:
        all_md: Set of all .md src_uri paths (relative to docs root).
        nav_paths: Set of .md src_uri paths explicitly listed in the nav.

    Returns:
        Sorted list of orphaned paths.
    """
    return sorted(all_md - nav_paths)


def _map_shield_to_finding(sf: SecurityFinding, docs_root: Path) -> Finding:
    """Convert a :class:`SecurityFinding` into a reporter :class:`Finding`.

    This is the **sole authorised bridge** between the Shield detection layer
    and the SentinelReporter.  It is extracted as a standalone pure function so
    that mutation testing can target it directly (see the Mutation Gate in
    ``CONTRIBUTING.md``, Obligation 4 — "The Invisible", "The Amnesiac", and
    "The Silencer" mutants must all be killed here).

    Args:
        sf: A secret detection result from :func:`~zenzic.core.shield.scan_line_for_secrets`
            or :func:`~zenzic.core.shield.scan_url_for_secrets`.
        docs_root: Absolute path to the docs root directory used to compute
            a project-relative display path.

    Returns:
        A :class:`~zenzic.core.reporter.Finding` with
        ``severity="security_breach"`` ready for the SentinelReporter pipeline.
    """
    try:
        rel = str(sf.file_path.relative_to(docs_root))
    except ValueError:
        rel = str(sf.file_path)

    return Finding(
        rel_path=rel,
        line_no=sf.line_no,
        code="Z201",
        severity="security_breach",
        message=f"Secret detected ({sf.secret_type}) — rotate immediately.",
        source_line=sf.url,
        col_start=sf.col_start,
        match_text=sf.match_text,
    )


@dataclass(slots=True)
class PlaceholderFinding:
    file_path: Path
    line_no: int
    issue: str
    detail: str
    col_start: int = 0
    match_text: str = ""


# Strips YAML frontmatter (leading ---...--- block).
_FRONTMATTER_RE: re.Pattern[str] = re.compile(r"\A\s*---\s*\n.*?\n---\s*\n?", re.DOTALL)
# Strips MDX comments {/* ... */} — invisible in the rendered page.
_MDX_COMMENT_RE: re.Pattern[str] = re.compile(r"\{/\*.*?\*/\}", re.DOTALL)
# Strips HTML comments <!-- ... --> — also invisible.
_HTML_COMMENT_RE: re.Pattern[str] = re.compile(r"<!--.*?-->", re.DOTALL)


def _first_content_line(text: str) -> int:
    """Return the 1-based line number of the first prose content line.

    Skips, in order:

    1. Leading HTML comments (``<!-- … -->``) — may span multiple lines.
    2. Leading MDX comments (``{/* … */}``) — may span multiple lines.
    3. YAML frontmatter (``--- … ---`` block).
    4. Blank lines interspersed among the above.

    This ensures Z502 short-content findings point at actual prose, not at
    SPDX licence headers (``<!-- SPDX-FileCopyrightText: … -->``) or at the
    frontmatter delimiters (``---``).
    """
    lines = text.splitlines()
    n = len(lines)
    i = 0

    # ── Phase 1: skip leading comments and blank lines ────────────────
    in_html = False
    in_mdx = False
    while i < n:
        stripped = lines[i].strip()
        if in_html:
            if "-->" in lines[i]:
                in_html = False
            i += 1
            continue
        if in_mdx:
            if "*/" in lines[i]:
                in_mdx = False
            i += 1
            continue
        if stripped.startswith("<!--"):
            if "-->" not in lines[i]:
                in_html = True
            i += 1
            continue
        if stripped.startswith("{/*"):
            if "*/" not in lines[i]:
                in_mdx = True
            i += 1
            continue
        if stripped == "":
            i += 1
            continue
        break  # first non-comment, non-blank line

    # ── Phase 2: skip YAML frontmatter block (--- … ---) ─────────────
    if i < n and lines[i].strip() == "---":
        i += 1  # skip opening ---
        while i < n and lines[i].strip() != "---":
            i += 1
        if i < n:
            i += 1  # skip closing ---

    # ── Phase 3: skip blank lines after frontmatter ───────────────────
    while i < n and lines[i].strip() == "":
        i += 1

    return i + 1  # 1-based


def _visible_word_count(text: str) -> int:
    """Return the number of prose words in *text*, excluding invisible markup.

    Strips MDX and HTML comments **first**, then YAML frontmatter.  The ordering
    is load-bearing: MDX files often open with a ``{/* SPDX … */}`` licence
    header *before* the ``---`` block.  If frontmatter stripping runs first,
    ``_FRONTMATTER_RE`` (anchored to ``\\A``) fails to match because ``{`` is not
    whitespace, leaving the entire YAML block counted as prose words.  Stripping
    comments first guarantees the frontmatter lands at the start of the string
    where the regex can anchor correctly.
    """
    # Strip invisible comments first — they may precede YAML frontmatter.
    text = _MDX_COMMENT_RE.sub("", text)
    text = _HTML_COMMENT_RE.sub("", text)
    # Frontmatter is now at \A — strip it.
    text = _FRONTMATTER_RE.sub("", text)
    return len(text.split())


def check_placeholder_content(
    text: str,
    file_path: Path | str,
    config: ZenzicConfig | None = None,
) -> list[PlaceholderFinding]:
    """Pure function: analyse markdown text for placeholder patterns. No I/O.

    Args:
        text: Raw markdown content to analyse.
        file_path: Path identifier used to label findings (no disk access).
        config: Optional Zenzic configuration.

    Returns:
        List of PlaceholderFinding instances.
    """
    if config is None:
        config = ZenzicConfig()

    path = Path(file_path)
    findings: list[PlaceholderFinding] = []
    patterns = config.placeholder_patterns_compiled

    visible = _visible_word_count(text)
    if visible < config.placeholder_max_words:
        findings.append(
            PlaceholderFinding(
                file_path=path,
                line_no=_first_content_line(text),
                issue="short-content",
                detail=f"Page has only {visible} words (minimum {config.placeholder_max_words}).",
            )
        )

    for i, line in enumerate(text.splitlines(), start=1):
        for pattern in patterns:
            m = pattern.search(line)
            if m:
                findings.append(
                    PlaceholderFinding(
                        file_path=path,
                        line_no=i,
                        issue="placeholder-text",
                        detail=f"Found placeholder text matching pattern: '{pattern.pattern}'",
                        col_start=m.start(),
                        match_text=m.group(),
                    )
                )

    return findings


def check_asset_references(text: str, page_dir: str = "") -> set[str]:
    """Pure function: extract normalised asset paths referenced in markdown text.

    Args:
        text: Raw markdown content.
        page_dir: POSIX directory of the page relative to docs root (e.g. ``"guide"``).
                  Pass an empty string for pages at the root.

    Returns:
        Set of normalised asset paths relative to docs root.
    """
    referenced: set[str] = set()
    for match in _MARKDOWN_ASSET_LINK_RE.finditer(text):
        url = match.group(1) or match.group(2)
        if not url or url.startswith(("http://", "https://", "data:", "#")):
            continue
        clean_url = unquote(url.split("?")[0].split("#")[0])
        base = page_dir if page_dir else "."
        normalized = posixpath.normpath(posixpath.join(base, clean_url))
        if not normalized.startswith(".."):  # skip paths that escape the docs root
            referenced.add(normalized)
    return referenced


def calculate_unused_assets(all_assets: set[str], used_assets: set[str]) -> list[str]:
    """Pure function: return sorted list of assets not referenced by any page.

    Args:
        all_assets: Set of all known asset paths (relative to docs root).
        used_assets: Set of asset paths referenced in documentation pages.

    Returns:
        Sorted list of unused asset paths.
    """
    return sorted(all_assets - used_assets)


# ─── CLI / I/O wrappers ───────────────────────────────────────────────────────


def find_orphans(
    docs_root: Path,
    exclusion_manager: LayeredExclusionManager,
    *,
    repo_root: Path,
    config: ZenzicConfig,
) -> list[Path]:
    """Return docs/*.md files whose adapter status is ORPHAN_BUT_EXISTING.

    Args:
        docs_root: Resolved path to the documentation root.
        exclusion_manager: Layered exclusion manager (mandatory).
        repo_root: Path to the repository root (for adapter creation).
        config: Zenzic configuration model.

    Returns:
        List of Path objects relative to docs_root that are not in the nav.
    """
    if not docs_root.exists() or not docs_root.is_dir():
        return []

    adapter = get_adapter(config.build_context, docs_root, repo_root)

    if not adapter.has_engine_config():
        return []

    nav_paths = adapter.get_nav_paths()
    adapter_ignored = adapter.get_ignored_patterns()

    orphans: list[Path] = []
    for md_file in iter_markdown_sources(docs_root, config, exclusion_manager):
        rel = md_file.relative_to(docs_root)
        if rel.parts and adapter.is_locale_dir(rel.parts[0]):
            continue
        if any(fnmatch.fnmatch(md_file.name, pat) for pat in adapter_ignored):
            continue
        if adapter.classify_route(rel, nav_paths) == "ORPHAN_BUT_EXISTING":
            orphans.append(rel)

    return orphans


def find_placeholders(
    docs_root: Path,
    exclusion_manager: LayeredExclusionManager,
    *,
    config: ZenzicConfig,
    repo_root: Path | None = None,
) -> list[PlaceholderFinding]:
    """Scan docs for placeholder/stub patterns and short word counts.

    Args:
        docs_root: Resolved path to the documentation root.
        exclusion_manager: Layered exclusion manager (mandatory).
        config: Zenzic configuration model.
        repo_root: Optional repository root.  When provided and the adapter
            exposes ``get_locale_source_roots()``, locale translation trees
            are also scanned (Docusaurus i18n support).

    Returns:
        List of PlaceholderFinding instances detailing the issues found.
    """
    findings: list[PlaceholderFinding] = []

    if not docs_root.exists() or not docs_root.is_dir():
        return findings

    for md_file in iter_markdown_sources(docs_root, config, exclusion_manager):
        rel_path = md_file.relative_to(docs_root)
        content = md_file.read_text(encoding="utf-8")
        findings.extend(check_placeholder_content(content, rel_path, config))

    if repo_root is not None:
        adapter = get_adapter(config.build_context, docs_root, repo_root)
        if hasattr(adapter, "get_locale_source_roots"):
            for locale_root, locale_name in adapter.get_locale_source_roots(repo_root):
                for md_file, logical_rel in iter_locale_markdown_sources(
                    locale_root, locale_name, config, exclusion_manager
                ):
                    content = md_file.read_text(encoding="utf-8")
                    findings.extend(check_placeholder_content(content, logical_rel, config))

    return findings


def find_unused_assets(
    docs_root: Path,
    exclusion_manager: LayeredExclusionManager,
    *,
    config: ZenzicConfig,
    repo_root: Path | None = None,
    adapter_metadata_files: frozenset[str] = frozenset(),
) -> list[Path]:
    """Return asset files in docs/ that are not referenced by any markdown file.

    Args:
        docs_root: Resolved path to the documentation root.
        exclusion_manager: Layered exclusion manager (mandatory).
        config: Zenzic configuration model.
        repo_root: Optional repository root.  When provided and the adapter
            exposes ``get_locale_source_roots()``, locale translation trees
            are also scanned when collecting asset reference sets
            (Docusaurus i18n support).
        adapter_metadata_files: Filenames (basename only) that the active adapter
            consumes as configuration — shielded from Z903 (Level 1b guardrail).

    Returns:
        List of Path objects relative to docs_root that are unused.
    """
    if not docs_root.exists() or not docs_root.is_dir():
        return []

    all_assets: set[str] = set()
    # Asset-specific prune set: excluded_asset_dirs are layered on top of
    # the exclusion_manager's directory decisions.
    asset_extra_prune = set(config.excluded_asset_dirs)
    for file_path in walk_files(docs_root, asset_extra_prune, exclusion_manager):
        if file_path.is_dir() or file_path.is_symlink() or file_path.suffix in DOC_SUFFIXES:
            continue
        # L1: System file guardrails + adapter metadata (CEO-050)
        name = file_path.name
        if (
            name in SYSTEM_EXCLUDED_FILE_NAMES
            or any(fnmatch.fnmatch(name, p) for p in SYSTEM_EXCLUDED_FILE_PATTERNS)
            or name in adapter_metadata_files
        ):
            continue
        rel_path = file_path.relative_to(docs_root)
        if rel_path.suffix in {".css", ".js", ".yml", ".sarif", ".license", ".j2"}:
            continue
        if any(part in config.excluded_asset_dirs for part in rel_path.parts):
            continue
        rel_posix = rel_path.as_posix()
        if any(fnmatch.fnmatch(rel_posix, pat) for pat in config.excluded_build_artifacts):
            continue
        all_assets.add(rel_posix)

    if not all_assets:
        return []

    # Remove explicitly excluded assets.
    # Every entry in excluded_assets is treated as an fnmatch pattern
    # (relative to docs_dir).  Literal paths work as-is because fnmatch
    # treats a string without metacharacters as a literal match.
    excluded_patterns = [e.lstrip("/") for e in config.excluded_assets]
    if excluded_patterns:
        all_assets = {
            a for a in all_assets if not any(fnmatch.fnmatch(a, pat) for pat in excluded_patterns)
        }

    if not all_assets:
        return []

    used_assets: set[str] = set()
    for md_file in iter_markdown_sources(docs_root, config, exclusion_manager):
        content = md_file.read_text(encoding="utf-8")
        rel_md = md_file.relative_to(docs_root)
        page_dir = rel_md.parent.as_posix()
        if page_dir == ".":
            page_dir = ""
        used_assets |= check_asset_references(content, page_dir)

    # Also collect asset references cited from locale translation trees.
    if repo_root is not None:
        adapter = get_adapter(config.build_context, docs_root, repo_root)
        if hasattr(adapter, "get_locale_source_roots"):
            for locale_root, locale_name in adapter.get_locale_source_roots(repo_root):
                for md_file, logical_rel in iter_locale_markdown_sources(
                    locale_root, locale_name, config, exclusion_manager
                ):
                    content = md_file.read_text(encoding="utf-8")
                    page_dir = logical_rel.parent.as_posix()
                    if page_dir == ".":
                        page_dir = ""
                    used_assets |= check_asset_references(content, page_dir)

    return [Path(p) for p in calculate_unused_assets(all_assets, used_assets)]


def find_missing_directory_indices(
    docs_root: Path,
    exclusion_manager: LayeredExclusionManager,
    *,
    repo_root: Path,
    config: ZenzicConfig,
) -> list[Path]:
    """Return directories that contain ``.md`` / ``.mdx`` source files but no
    engine-provided index page, indicating a potential 404 at the directory URL.

    The check is engine-aware: it delegates to
    :meth:`~zenzic.core.adapters._base.BaseAdapter.provides_index` on the
    resolved adapter so that each engine's index-page conventions are respected
    (Docusaurus ``index.mdx`` / ``_category_.json``, MkDocs ``README.md``,
    Zensical strict ``index.md``, etc.).

    The docs root itself is excluded — a missing ``docs/index.*`` is reported
    only when it actually causes a 404 visible to end-users (i.e. sub-dirs).

    I/O is permitted here: this function is part of the discovery phase and
    calls :meth:`provides_index` exactly once per candidate directory.

    Args:
        docs_root: Resolved absolute path to the documentation root.
        exclusion_manager: Mandatory layered exclusion manager.
        repo_root: Repository root used to instantiate the adapter.
        config: Zenzic configuration model.

    Returns:
        List of :class:`~pathlib.Path` objects relative to *docs_root*,
        sorted lexicographically, for directories that lack an index page.
    """
    if not docs_root.exists() or not docs_root.is_dir():
        return []

    adapter = get_adapter(config.build_context, docs_root, repo_root)

    # Collect the set of unique parent directories that contain at least one
    # Markdown source file (excluding docs_root itself — the root index is a
    # separate concern handled in DIRETTIVA CEO 011).
    dirs_with_docs: set[Path] = set()
    for file_path in walk_files(docs_root, set(), exclusion_manager):
        if file_path.suffix.lower() in DOC_SUFFIXES and file_path.parent != docs_root:
            dirs_with_docs.add(file_path.parent)

    if not dirs_with_docs:
        return []

    missing: list[Path] = []
    for dir_abs in sorted(dirs_with_docs):
        if not adapter.provides_index(dir_abs):
            try:
                missing.append(dir_abs.relative_to(docs_root))
            except ValueError:
                missing.append(dir_abs)

    return missing


# ─── Two-Pass Reference Pipeline ──────────────────────────────────────────────

# Harvest event type aliases (yielded by ReferenceScanner.harvest())
# (lineno, "DEF",           (ref_id_norm, url))      — definition accepted
# (lineno, "DUPLICATE_DEF", (ref_id_norm, url))      — duplicate ignored
# (lineno, "IMG",           (alt_text, url))          — image found
# (lineno, "MISSING_ALT",   url)                      — image without alt-text
# (lineno, "SECRET",        SecurityFinding)          — secret detected by Shield

HarvestEvent = tuple[int, str, Any]


def _skip_frontmatter(
    fh: Any,
) -> Generator[tuple[int, str], None, None]:
    """Yield ``(lineno, line)`` pairs from an open file handle, skipping YAML frontmatter.

    Frontmatter is a leading ``---`` block that ends with ``---`` or ``...``.
    Every other line — including lines inside fenced code blocks — is yielded.
    This is the raw stream used by the Shield so that secrets embedded inside
    code examples are never invisible.

    Args:
        fh: An open text file handle positioned at the start of the file.

    Yields:
        ``(1-based line number, raw line string)`` for every non-frontmatter line.
    """
    in_frontmatter = False
    frontmatter_checked = False

    for lineno, line in enumerate(fh, start=1):
        stripped = line.strip()

        if not frontmatter_checked:
            frontmatter_checked = True
            if stripped == "---":
                in_frontmatter = True
                continue

        if in_frontmatter:
            if stripped in ("---", "..."):
                in_frontmatter = False
            continue

        yield lineno, line


def _iter_content_lines(
    file_path: Path,
) -> Generator[tuple[int, str], None, None]:
    """Stream non-code, non-frontmatter lines from a Markdown file one at a time.

    Opens the file in text mode and iterates line-by-line (no .read() /
    .readlines()).  Two categories of lines are silently skipped:

    * **YAML frontmatter**: A leading ``---`` block (line 1 only) is skipped in
      its entirety up to and including the closing ``---`` or ``...`` delimiter.
      This prevents reference definitions embedded in YAML from being harvested
      as Markdown content.
    * **Fenced code blocks**: Lines inside ``` or ~~~ fences are skipped so that
      example URLs inside code never trigger false positives.

    Use :func:`_skip_frontmatter` when the Shield needs to scan every line,
    including lines inside fenced blocks.

    Args:
        file_path: Path to the Markdown source file.

    Yields:
        ``(1-based line number, raw line string)`` for every content line.
    """
    in_block = False

    with file_path.open(encoding="utf-8") as fh:
        for lineno, line in _skip_frontmatter(fh):
            stripped = line.strip()

            # ── Fenced code block skip ────────────────────────────────────
            if not in_block:
                if stripped.startswith("```") or stripped.startswith("~~~"):
                    in_block = True
                    continue
            else:
                if stripped.startswith("```") or stripped.startswith("~~~"):
                    in_block = False
                continue  # always skip lines inside fenced block

            yield lineno, line


def check_image_alt_text(
    text: str,
    file_path: Path | str,
) -> list[ReferenceFinding]:
    """Pure function: find images that are missing alt text.

    Checks both inline Markdown images ``![alt](url)`` and HTML ``<img>`` tags.
    An empty alt attribute (``alt=""``) is treated as intentionally decorative
    and is *not* flagged — the issue is a completely absent or blank alt string.

    Args:
        text: Raw Markdown content.
        file_path: Path identifier for labelling findings (no disk access).

    Returns:
        List of :class:`ReferenceFinding` with ``issue="missing-alt"`` and
        ``is_warning=True`` for every offending image.
    """
    path = Path(file_path)
    findings: list[ReferenceFinding] = []

    for lineno, line in enumerate(text.splitlines(), start=1):
        # Inline Markdown images
        for m in _RE_IMAGE_INLINE.finditer(line):
            alt_text = m.group(1)
            url = m.group(2)
            if not alt_text.strip():
                findings.append(
                    ReferenceFinding(
                        file_path=path,
                        line_no=lineno,
                        issue="missing-alt",
                        detail=f"Image '{url}' has no alt text.",
                        is_warning=True,
                    )
                )

        # HTML <img> tags
        for img_match in _RE_HTML_IMG.finditer(line):
            tag = img_match.group()
            alt_match = _RE_HTML_ALT.search(tag)
            src = tag  # fallback label when src is hard to extract
            if alt_match is None or not alt_match.group(1).strip():
                findings.append(
                    ReferenceFinding(
                        file_path=path,
                        line_no=lineno,
                        issue="missing-alt",
                        detail=f"HTML <img> tag has no alt text: {src[:60]}",
                        is_warning=True,
                    )
                )

    return findings


class ReferenceScanner:
    """Per-file stateful scanner implementing the Three-Phase Reference Pipeline.

    State lives entirely inside the instance via ``self.ref_map``.  There is no
    global scope pollution: create one ``ReferenceScanner`` per file.

    Usage::

        scanner = ReferenceScanner(Path("docs/guide.md"))

        # Pass 1 — drive the generator; bail immediately on SECRET events
        for event in scanner.harvest():
            lineno, event_type, data = event
            if event_type == "SECRET":
                raise SystemExit(2)  # or typer.Exit(2) in CLI layer

        # Pass 2 — resolve reference links (ref_map must be fully populated)
        cross_check_findings = scanner.cross_check()

        # Pass 3 — compute integrity score and collect all findings
        report = scanner.get_integrity_report(cross_check_findings)
    """

    def __init__(self, file_path: Path, config: ZenzicConfig | None = None) -> None:
        self.file_path = file_path
        self.ref_map: ReferenceMap = ReferenceMap()
        self._config = config or ZenzicConfig()

    # ── Pass 1: Harvesting & Shield ────────────────────────────────────────────

    def harvest(self) -> Generator[HarvestEvent, None, None]:
        """Pass 1: stream the file, extract reference definitions, run the Shield.

        Populates ``self.ref_map.definitions`` as a side effect.  Security
        findings are yielded immediately as ``("SECRET", SecurityFinding)``
        events so callers can abort with Exit Code 2 before Pass 2 begins.

        Uses two independent line streams from the same file:

        * **Shield stream** — every line except YAML frontmatter, including lines
          inside fenced code blocks.  Ensures that credentials in ``bash`` or
          unlabelled code examples are never invisible to the Shield.
        * **Content stream** — lines outside fenced blocks (``_iter_content_lines``).
          Used for reference-definition harvesting and alt-text detection so that
          example URLs inside code blocks never produce false positives.

        Reference definitions (``[id]: url``) are always outside fenced blocks by
        CommonMark §4.7 convention, so scanning them on the content stream is
        sufficient.  The Shield additionally scans every definition URL via
        ``scan_url_for_secrets`` to catch embedded secrets in reference URLs.

        Yields:
            ``(lineno, event_type, data)`` tuples.  See module-level type alias
            ``HarvestEvent`` for the full list of event types and data shapes.
        """
        # ── 1.a Shield pass: scan EVERY line including YAML frontmatter ──────────
        # ZRT-001 fix: the Shield must have priority over ALL content, including
        # YAML frontmatter.  Frontmatter values (aws_key, api_token, ...) are
        # real secrets — we use raw enumerate() so no line is ever skipped.
        # The Content Stream (1.b below) still uses _iter_content_lines which
        # skips frontmatter correctly to avoid false-positive ref-def hits.
        secret_line_nos: set[int] = set()
        shield_events: list[HarvestEvent] = []
        with self.file_path.open(encoding="utf-8") as fh:
            for finding in scan_lines_with_lookback(enumerate(fh, start=1), self.file_path):
                shield_events.append((finding.line_no, "SECRET", finding))
                secret_line_nos.add(finding.line_no)

        # ── 1.b Content pass: harvest ref-defs and alt-text (fences skipped) ─
        content_events: list[HarvestEvent] = []
        for lineno, line in _iter_content_lines(self.file_path):
            def_match = _RE_REF_DEF.match(line)
            if def_match:
                raw_id, url = def_match.group(1), def_match.group(2)
                accepted = self.ref_map.add_definition(raw_id, url, lineno)
                norm_id = raw_id.lower().strip()

                if accepted:
                    content_events.append((lineno, "DEF", (norm_id, url)))

                    # ── 1.c Shield: scan URL for secrets ─────────────────────
                    for finding in scan_url_for_secrets(url, self.file_path, lineno):
                        # Only emit if scan_line_for_secrets hasn't already
                        # emitted a SECRET for this line (avoid duplicates).
                        if lineno not in secret_line_nos:
                            shield_events.append((lineno, "SECRET", finding))
                            secret_line_nos.add(lineno)
                else:
                    content_events.append((lineno, "DUPLICATE_DEF", (norm_id, url)))
                continue

            # ── Alt-text: inline images ───────────────────────────────────────
            for img_match in _RE_IMAGE_INLINE.finditer(line):
                alt_text = img_match.group(1)
                url = img_match.group(2)
                if alt_text.strip():
                    content_events.append((lineno, "IMG", (alt_text, url)))
                else:
                    content_events.append((lineno, "MISSING_ALT", url))

        # Yield all events in line-number order
        yield from sorted(shield_events + content_events, key=lambda e: e[0])

    # ── Pass 2: Cross-Check & Validation ──────────────────────────────────────

    def cross_check(self) -> list[ReferenceFinding]:
        """Pass 2: resolve reference links against the populated ReferenceMap.

        Must be called **after** ``harvest()`` has been fully consumed so that
        ``self.ref_map.definitions`` is complete.

        Returns:
            List of :class:`ReferenceFinding` for dangling references (links
            that use an undefined ID).
        """
        findings: list[ReferenceFinding] = []

        for lineno, line in _iter_content_lines(self.file_path):
            # Blank out inline code to avoid false matches inside `[code][spans]`
            clean = re.sub(r"`[^`]+`", lambda m: " " * len(m.group()), line)

            for m in _RE_REF_LINK.finditer(clean):
                text = m.group(2)
                ref_id = m.group(3) if m.group(3) else text  # collapsed ref
                url = self.ref_map.resolve(ref_id)
                if url is None:
                    norm_id = ref_id.lower().strip()
                    findings.append(
                        ReferenceFinding(
                            file_path=self.file_path,
                            line_no=lineno,
                            issue="DANGLING",
                            detail=(
                                f"Reference '[{text}][{ref_id}]' uses undefined ID '{norm_id}'."
                            ),
                            is_warning=False,
                        )
                    )

            # Shortcut reference links: [text] (CommonMark §4.7)
            for m in _RE_REF_SHORTCUT.finditer(clean):
                ref_id = m.group(1)
                self.ref_map.resolve(ref_id)  # mark as used if defined

        return findings

    # ── Pass 3: Cleanup & Metrics ──────────────────────────────────────────────

    def get_integrity_report(
        self,
        cross_check_findings: list[ReferenceFinding] | None = None,
        security_findings: list[SecurityFinding] | None = None,
    ) -> IntegrityReport:
        """Pass 3: compute integrity score and consolidate all findings.

        Args:
            cross_check_findings: Findings from :meth:`cross_check` (dangling
                refs).  Pass ``None`` or omit to skip.
            security_findings: Shield findings collected during
                :meth:`harvest`.  Pass ``None`` or omit to skip.

        Returns:
            :class:`IntegrityReport` with the integrity score and the full
            ordered list of findings (errors first, warnings last).
        """
        findings: list[ReferenceFinding] = list(cross_check_findings or [])

        # Orphan definitions — defined but never used (warning)
        for norm_id in sorted(self.ref_map.orphan_definitions):
            url, def_line = self.ref_map.definitions[norm_id]
            findings.append(
                ReferenceFinding(
                    file_path=self.file_path,
                    line_no=def_line,
                    issue="DEAD_DEF",
                    detail=(f"Reference '[{norm_id}]: {url}' is defined but never used."),
                    is_warning=True,
                )
            )

        # Duplicate definitions — subsequent occurrences ignored (warning)
        for norm_id in sorted(self.ref_map.duplicate_ids):
            url, def_line = self.ref_map.definitions[norm_id]
            findings.append(
                ReferenceFinding(
                    file_path=self.file_path,
                    line_no=def_line,
                    issue="duplicate-def",
                    detail=(
                        f"Reference ID '[{norm_id}]' is defined more than once. "
                        "First definition wins (CommonMark §4.7)."
                    ),
                    is_warning=True,
                )
            )

        return IntegrityReport(
            file_path=self.file_path,
            score=self.ref_map.integrity_score,
            findings=findings,
            security_findings=list(security_findings or []),
        )


# ─── I/O wrapper: scan all docs ───────────────────────────────────────────────


def _scan_single_file(
    md_file: Path,
    config: ZenzicConfig,
    rule_engine: AdaptiveRuleEngine | None = None,
) -> tuple[IntegrityReport, ReferenceScanner | None]:
    """Run the Three-Phase Pipeline on one Markdown file.

    Returns the scanner alongside the report so callers that need the
    populated ``ref_map`` (e.g. for external URL registration) can reuse it
    without triggering a second read of the file.

    Args:
        md_file: Absolute path to the Markdown file to process.
        config: Zenzic configuration.
        rule_engine: Optional :class:`~zenzic.core.rules.AdaptiveRuleEngine` to apply
            after the reference pipeline.  When provided, the file is read once
            more as a string for the rule pass (rules receive the full text, not
            the line-by-line generator output).  When ``None`` or empty, the
            rule pass is skipped entirely.

    Returns:
        ``(report, scanner)`` where ``scanner`` is ``None`` when the Shield
        detected secrets (no external URLs should be registered from such files).
    """
    scanner = ReferenceScanner(md_file, config)
    security_findings: list[SecurityFinding] = []

    # Pass 1 — harvest; collect security findings
    for _lineno, event_type, data in scanner.harvest():
        if event_type == "SECRET":
            security_findings.append(data)

    # Pass 2 — cross-check (only if no secrets; Shield is a firewall)
    cross_findings: list[ReferenceFinding] = []
    if not security_findings:
        cross_findings = scanner.cross_check()

    # Pass 3 — integrity report
    report = scanner.get_integrity_report(cross_findings, security_findings)

    # Rule Engine pass — applied after reference pipeline, only when configured.
    # Files with security findings are also excluded from rule scanning to avoid
    # further processing of potentially compromised content.
    if rule_engine and not security_findings:
        text = md_file.read_text(encoding="utf-8")
        report.rule_findings = rule_engine.run(md_file, text)

    # Return scanner only when the file is secure — callers must not register
    # URLs from files that failed the Shield (they may embed leaked credentials).
    secure_scanner: ReferenceScanner | None = None if security_findings else scanner
    return report, secure_scanner


def _build_rule_engine(config: ZenzicConfig) -> AdaptiveRuleEngine | None:
    """Construct a :class:`~zenzic.core.rules.AdaptiveRuleEngine` from the config.

    Load order is deterministic:

    1. Core rules registered by Zenzic itself (always enabled).
    2. Regex rules from ``[[custom_rules]]``.
    3. External plugin rules explicitly listed in ``plugins = [...]``.

    Returns ``None`` when no rules are available.
    """
    from zenzic.core.rules import CustomRule, PluginRegistry  # deferred to keep import graph clean

    # In this per-file pipeline, core VSM-only rules are no-op. Avoid building
    # an engine (and avoid extra read_text calls) when no effective rules exist.
    if not config.custom_rules and not config.plugins:
        return None

    registry = PluginRegistry()
    rules = registry.load_core_rules()
    rules.extend(
        CustomRule(
            id=cr.id,
            pattern=cr.pattern,
            message=cr.message,
            severity=cr.severity,
        )
        for cr in config.custom_rules
    )
    rules.extend(registry.load_selected_rules(config.plugins))

    # Deduplicate by rule_id while preserving declaration priority.
    deduped: list[BaseRule] = []
    seen: set[str] = set()
    for rule in rules:
        rid = rule.rule_id
        if rid in seen:
            continue
        seen.add(rid)
        deduped.append(rule)

    if not deduped:
        return None
    return AdaptiveRuleEngine(deduped)


def _emit_telemetry(*, mode: str, workers: int, n_files: int, elapsed: float) -> None:
    """Write a one-line performance summary to stderr.

    Only called when ``verbose=True`` is passed to :func:`scan_docs_references`.
    Writes to stderr so it never contaminates stdout-captured output.

    The speedup estimate for parallel mode assumes a linear model relative to
    the sequential baseline: ``speedup ≈ workers × 0.7`` (accounting for
    overhead and I/O serialisation).  This is a rough heuristic for display
    purposes only.

    Args:
        mode:     ``"Sequential"`` or ``"Parallel"``.
        workers:  Effective worker count used.
        n_files:  Number of ``.md`` files scanned.
        elapsed:  Wall-clock seconds from scan start to completion.
    """
    import sys

    engine_label = (
        f"Adaptive (Parallel, {workers} worker{'s' if workers != 1 else ''})"
        if mode == "Parallel"
        else "Adaptive (Sequential)"
    )
    time_str = f"{elapsed:.2f}s"
    speedup_str = ""
    if mode == "Parallel" and workers > 1:
        estimated = round(min(workers * 0.7, workers - 0.1), 1)
        speedup_str = f"  Estimated speedup: {estimated}x"

    print(
        f"[zenzic] Engine: {engine_label}  "
        f"Files: {n_files}  "
        f"Execution time: {time_str}"
        f"{speedup_str}",
        file=sys.stderr,
    )


def scan_docs_references(
    docs_root: Path,
    exclusion_manager: LayeredExclusionManager,
    *,
    config: ZenzicConfig,
    validate_links: bool = False,
    workers: int | None = 1,
    verbose: bool = False,
    locale_roots: list[tuple[Path, str]] | None = None,
) -> tuple[list[IntegrityReport], list[str]]:
    """Run the Three-Phase Pipeline over every .md file in docs/.

    This is the single unified entry point for all scan modes.  The engine
    selects sequential or parallel execution automatically based on the number
    of files found (**Hybrid Adaptive Mode**):

    * **Sequential** — used when ``workers=1`` (the default) or when the repo
      has fewer than :data:`ADAPTIVE_PARALLEL_THRESHOLD` files.  Zero
      process-spawn overhead; supports external URL validation.
    * **Parallel** — activated when ``workers != 1`` *and* the file count
      meets or exceeds :data:`ADAPTIVE_PARALLEL_THRESHOLD`.  Distributes each
      file to an independent worker process via ``ProcessPoolExecutor``.
      External URL validation is performed in the main process after all
      workers complete.

    The threshold default (50 files) is a conservative heuristic: below it,
    ``ProcessPoolExecutor`` spawn overhead (~200–400 ms on a cold interpreter)
    exceeds the parallelism benefit.  Override with ``workers=N`` to select a
    specific pool size when parallel mode is active.

    **Determinism guarantee:** results are always sorted by ``file_path``
    regardless of execution mode.

    **Shield behaviour:** enforced per-worker in parallel mode; per-file in
    sequential mode.  Files with security findings are excluded from link
    validation in both modes.

    **Read behaviour:** total I/O remains :math:`O(N)` in the number of files,
    but individual files may be read multiple times.  In sequential mode the
    scanner typically performs separate Shield and content passes, and some
    rules may trigger an additional ``read_text()`` call.  In parallel mode the
    same per-worker behaviour applies; when ``validate_links=True`` an extra
    lightweight sequential pass in the main process registers external URLs
    after workers complete (workers discard scanners).

    Args:
        repo_root:      Repository root (must contain ``docs/``).
        config:         Optional Zenzic configuration.
        validate_links: When ``True``, perform async HTTP validation of all
                        external reference URLs found across the docs tree.
                        Disabled by default.
        workers:        Number of worker processes for parallel mode.
                        ``1`` (default) always uses sequential execution.
                        ``None`` lets ``ProcessPoolExecutor`` pick based on
                        ``os.cpu_count()``.  Values must be ``None`` or
                        greater than or equal to ``1``.
        verbose:        When ``True``, print a single telemetry line to stderr
                        after the scan completes.  Shows the engine mode, worker
                        count, elapsed time, and estimated speedup (parallel
                        mode only).  Defaults to ``False``.

    Returns:
        A ``(reports, link_errors)`` tuple where:

        - ``reports`` is the sorted list of :class:`IntegrityReport` objects,
          one per ``.md`` file.
        - ``link_errors`` is a sorted list of human-readable HTTP error strings
          (empty when ``validate_links=False`` or all URLs pass).
    """
    import time

    if workers is not None and workers < 1:
        raise ValueError("workers must be None or an integer >= 1")

    if not docs_root.exists() or not docs_root.is_dir():
        return [], []

    rule_engine = _build_rule_engine(config)
    md_files = list(iter_markdown_sources(docs_root, config, exclusion_manager))

    # Build locale path remap: actual_abs_path → virtual_path_under_docs_root.
    # virtual_path = docs_root / locale_name / rel_within_locale
    # This maps locale files to logical paths so the reporter displays
    # "it/architecture.mdx" rather than the full i18n/ absolute path.
    _locale_path_remap: dict[Path, Path] = {}
    if locale_roots:
        for locale_root, locale_name in locale_roots:
            for abs_path, logical_rel in iter_locale_markdown_sources(
                locale_root, locale_name, config, exclusion_manager
            ):
                _locale_path_remap[abs_path] = docs_root / logical_rel
                md_files.append(abs_path)

    if not md_files:
        return [], []

    use_parallel = workers != 1 and len(md_files) >= ADAPTIVE_PARALLEL_THRESHOLD

    _t0 = time.monotonic()

    if use_parallel:
        import concurrent.futures
        import os

        actual_workers = workers if workers is not None else os.cpu_count() or 1
        work_items = [(f, config, rule_engine) for f in md_files]
        # GA-1 fix: use actual_workers for the executor (not the raw `workers`
        # sentinel) so max_workers always matches what telemetry reports.
        with concurrent.futures.ProcessPoolExecutor(max_workers=actual_workers) as executor:
            # ZRT-002 fix: use submit() + future.result(timeout=...) instead of
            # executor.map().  This prevents a deadlocked worker (e.g. from a
            # ReDoS pattern in [[custom_rules]]) from blocking the entire scan.
            futures_map = {executor.submit(_worker, item): item[0] for item in work_items}
            raw: list[IntegrityReport] = []
            for fut, md_file in futures_map.items():
                try:
                    raw.append(fut.result(timeout=_WORKER_TIMEOUT_S))
                except concurrent.futures.TimeoutError:
                    raw.append(_make_timeout_report(md_file))
                except Exception as exc:  # noqa: BLE001
                    raw.append(_make_error_report(md_file, exc))

        reports: list[IntegrityReport] = sorted(raw, key=lambda r: r.file_path)

        # Remap locale file paths to their logical display paths.
        if _locale_path_remap:
            for _r in reports:
                if _r.file_path in _locale_path_remap:
                    _r.file_path = _locale_path_remap[_r.file_path]

        elapsed = time.monotonic() - _t0
        if verbose:
            _emit_telemetry(
                mode="Parallel",
                workers=actual_workers,
                n_files=len(md_files),
                elapsed=elapsed,
            )

        if not validate_links:
            return reports, []

        # Phase B in main process: lightweight sequential pass for URL
        # registration.  Workers discard scanners; we re-collect ref_maps here
        # for deduplication.  This is an additional O(N) read but preserves the
        # Shield-as-firewall guarantee (no URLs from compromised files).
        secure_scanners_b: list[ReferenceScanner] = []
        for md_file in md_files:
            _report_b, secure_scanner_b = _scan_single_file(md_file, config, None)
            if secure_scanner_b is not None:
                secure_scanners_b.append(secure_scanner_b)
        validator_b = LinkValidator()
        for scanner in secure_scanners_b:
            validator_b.register_from_map(scanner.ref_map, scanner.file_path)
        return reports, validator_b.validate()

    # Sequential path — zero overhead, full O(N) link-validation support.
    reports_seq: list[IntegrityReport] = []
    secure_scanners_seq: list[ReferenceScanner] = []

    for md_file in md_files:
        report, secure_scanner = _scan_single_file(md_file, config, rule_engine)
        reports_seq.append(report)
        if validate_links and secure_scanner is not None:
            secure_scanners_seq.append(secure_scanner)

    elapsed_seq = time.monotonic() - _t0
    if verbose:
        _emit_telemetry(
            mode="Sequential",
            workers=1,
            n_files=len(md_files),
            elapsed=elapsed_seq,
        )

    if not validate_links:
        # Remap locale file paths to their logical display paths.
        if _locale_path_remap:
            for _r in reports_seq:
                if _r.file_path in _locale_path_remap:
                    _r.file_path = _locale_path_remap[_r.file_path]
        return reports_seq, []

    # Phase B — global URL deduplication and async HTTP validation.
    # Uses the already-populated ref_maps from Phase A — no second file read.
    validator_seq = LinkValidator()
    for scanner in secure_scanners_seq:
        validator_seq.register_from_map(scanner.ref_map, scanner.file_path)
    # Remap locale file paths to their logical display paths.
    if _locale_path_remap:
        for _r in reports_seq:
            if _r.file_path in _locale_path_remap:
                _r.file_path = _locale_path_remap[_r.file_path]
    return reports_seq, validator_seq.validate()


# ─── Adaptive parallel worker ─────────────────────────────────────────────────

#: Files below this threshold are scanned sequentially (zero process-spawn
#: overhead).  Above it, the AdaptiveRuleEngine switches to a
#: ProcessPoolExecutor automatically.  Exposed as a module constant so tests
#: can override it without patching private internals.
ADAPTIVE_PARALLEL_THRESHOLD: int = 50

#: Maximum wall-clock seconds a single worker may spend analysing one file.
#: If a worker exceeds this limit it is abandoned and a Z009 timeout finding
#: is emitted for the file instead of a normal IntegrityReport.  The purpose
#: is to prevent ReDoS patterns in [[custom_rules]] from deadlocking the
#: entire parallel pipeline.  (ZRT-002 fix)
_WORKER_TIMEOUT_S: int = 30


def _make_timeout_report(md_file: Path) -> IntegrityReport:
    """Produce a minimal :class:`IntegrityReport` for a worker that timed out.

    Called by the parallel coordinator when ``future.result(timeout=...)``
    raises :class:`concurrent.futures.TimeoutError`.  The returned report
    carries a single ``Z009`` rule finding so the CLI can surface the
    timeout in the standard findings UI without crashing the scan.

    Args:
        md_file: Absolute path of the file whose worker timed out.

    Returns:
        A :class:`IntegrityReport` with ``score=0`` and one ``Z009`` finding.
    """
    from zenzic.core.rules import RuleFinding  # deferred: avoid circular at module level
    from zenzic.models.references import IntegrityReport

    timeout_finding = RuleFinding(
        file_path=md_file,
        line_no=0,
        rule_id="Z009",
        message=(
            f"Analysis of '{md_file.name}' timed out after {_WORKER_TIMEOUT_S}s. "
            "A custom rule pattern may be causing catastrophic backtracking (ReDoS). "
            "Check [[custom_rules]] patterns in zenzic.toml."
        ),
        severity="error",
    )
    return IntegrityReport(
        file_path=md_file,
        score=0,
        findings=[],
        security_findings=[],
        rule_findings=[timeout_finding],
    )


def _make_error_report(md_file: Path, exc: BaseException) -> IntegrityReport:
    """Produce a minimal :class:`IntegrityReport` for a worker that raised.

    Args:
        md_file: Absolute path of the file whose worker raised an exception.
        exc: The exception caught from ``future.result()``.

    Returns:
        A :class:`IntegrityReport` with ``score=0`` and one ``RULE-ENGINE-ERROR`` finding.
    """
    from zenzic.core.rules import RuleFinding
    from zenzic.models.references import IntegrityReport

    error_finding = RuleFinding(
        file_path=md_file,
        line_no=0,
        rule_id="RULE-ENGINE-ERROR",
        message=(
            f"Worker for '{md_file.name}' raised an unexpected exception: "
            f"{type(exc).__name__}: {exc}"
        ),
        severity="error",
    )
    return IntegrityReport(
        file_path=md_file,
        score=0,
        findings=[],
        security_findings=[],
        rule_findings=[error_finding],
    )


def _worker(args: tuple[Path, ZenzicConfig, AdaptiveRuleEngine | None]) -> IntegrityReport:
    """Top-level worker function for ``ProcessPoolExecutor``.

    Must be a module-level function (not a lambda or nested function) so that
    ``pickle`` can serialise it for inter-process transport.

    **Immutability contract:** ``config`` and ``rule_engine`` are serialised by
    ``pickle`` when dispatched to a worker process.  Each worker receives an
    independent copy — there is no shared state between processes.  Workers
    must never mutate ``config``; :func:`_scan_single_file` and all functions
    it calls are pure and honour this contract.

    Args:
        args: ``(md_file, config, rule_engine)`` tuple.

    Returns:
        The :class:`IntegrityReport` for *md_file*.  The ``ReferenceScanner``
        is discarded — workers do not participate in Phase B URL registration.
    """
    md_file, config, rule_engine = args
    report, _scanner = _scan_single_file(md_file, config, rule_engine)
    return report
