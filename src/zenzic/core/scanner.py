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
from typing import Any
from urllib.parse import unquote

from zenzic.core.adapter import get_adapter
from zenzic.core.rules import AdaptiveRuleEngine, BaseRule
from zenzic.core.shield import SecurityFinding, scan_line_for_secrets, scan_url_for_secrets
from zenzic.core.validator import LinkValidator
from zenzic.models.config import ZenzicConfig
from zenzic.models.references import IntegrityReport, ReferenceFinding, ReferenceMap


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


def find_repo_root() -> Path:
    """Walk upward from CWD until a Zenzic project root marker is found.

    Root markers (first match wins, checked in order):
    - ``.git/``  — universal VCS marker.
    - ``zenzic.toml`` — Zenzic's own configuration file.

    Using engine-neutral markers keeps the Core independent of any specific
    documentation build engine (e.g. ``mkdocs.yml`` is intentionally excluded).

    This is more robust than ``Path(__file__).parents[N]`` because it works
    regardless of where the CLI is invoked from inside the repo.

    Raises:
        RuntimeError: if no root marker is found in any ancestor.
    """
    cwd = Path.cwd().resolve()
    for candidate in [cwd, *cwd.parents]:
        if (candidate / ".git").is_dir() or (candidate / "zenzic.toml").is_file():
            return candidate
    raise RuntimeError(
        "Could not locate repo root: no .git directory or zenzic.toml found in any "
        f"ancestor of {cwd}. Run Zenzic from inside the repository."
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


@dataclass(slots=True)
class PlaceholderFinding:
    file_path: Path
    line_no: int
    issue: str
    detail: str


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

    words = text.split()
    if len(words) < config.placeholder_max_words:
        findings.append(
            PlaceholderFinding(
                file_path=path,
                line_no=1,
                issue="short-content",
                detail=f"Page has only {len(words)} words (minimum {config.placeholder_max_words}).",
            )
        )

    for i, line in enumerate(text.splitlines(), start=1):
        for pattern in patterns:
            if pattern.search(line):
                findings.append(
                    PlaceholderFinding(
                        file_path=path,
                        line_no=i,
                        issue="placeholder-text",
                        detail=f"Found placeholder text matching pattern: '{pattern.pattern}'",
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


def find_orphans(repo_root: Path, config: ZenzicConfig | None = None) -> list[Path]:
    """Return docs/*.md files whose adapter status is ORPHAN_BUT_EXISTING.

    Args:
        repo_root: Path to the repository root (contains mkdocs.yml).
        config: Optional configuration model.

    Returns:
        List of Path objects relative to docs_root that are not in the nav.
    """
    if config is None:
        config = ZenzicConfig()

    docs_root = repo_root / config.docs_dir
    if not docs_root.exists() or not docs_root.is_dir():
        return []

    # The adapter factory owns all engine-specific knowledge: config loading,
    # nav extraction, locale detection, and Zensical enforcement.
    adapter = get_adapter(config.build_context, docs_root, repo_root)

    # No engine config means no nav to compare against — skip orphan detection.
    if not adapter.has_engine_config():
        return []

    nav_paths = adapter.get_nav_paths()
    exclusion_patterns = set(config.excluded_file_patterns) | adapter.get_ignored_patterns()

    orphans: list[Path] = []
    for md_file in sorted(docs_root.rglob("*.md")):
        if md_file.is_symlink():
            continue
        rel = md_file.relative_to(docs_root)
        if any(part in config.excluded_dirs for part in rel.parts):
            continue
        # Skip all files inside a locale directory — managed by the i18n plugin.
        if rel.parts and adapter.is_locale_dir(rel.parts[0]):
            continue
        if any(fnmatch.fnmatch(md_file.name, pat) for pat in exclusion_patterns):
            continue
        if adapter.classify_route(rel, nav_paths) == "ORPHAN_BUT_EXISTING":
            orphans.append(rel)

    return orphans


def find_placeholders(
    repo_root: Path, config: ZenzicConfig | None = None
) -> list[PlaceholderFinding]:
    """Scan docs for placeholder/stub patterns and short word counts.

    Args:
        repo_root: Path to the repository root.
        config: Optional configuration model.

    Returns:
        List of PlaceholderFinding instances detailing the issues found.
    """
    if config is None:
        config = ZenzicConfig()

    docs_root = repo_root / config.docs_dir
    findings: list[PlaceholderFinding] = []

    if not docs_root.exists() or not docs_root.is_dir():
        return findings

    for md_file in sorted(docs_root.rglob("*.md")):
        if md_file.is_symlink():
            continue
        rel_path = md_file.relative_to(docs_root)
        if any(part in config.excluded_dirs for part in rel_path.parts):
            continue
        content = md_file.read_text(encoding="utf-8")
        findings.extend(check_placeholder_content(content, rel_path, config))

    return findings


def find_unused_assets(repo_root: Path, config: ZenzicConfig | None = None) -> list[Path]:
    """Return asset files in docs/ that are not referenced by any markdown file.

    Args:
        repo_root: Path to the repository root.
        config: Optional configuration model.

    Returns:
        List of Path objects relative to docs_root that are unused.
    """
    if config is None:
        config = ZenzicConfig()

    docs_root = repo_root / config.docs_dir

    if not docs_root.exists() or not docs_root.is_dir():
        return []

    all_assets: set[str] = set()
    for file_path in sorted(docs_root.rglob("*")):
        if file_path.is_dir() or file_path.is_symlink() or file_path.suffix == ".md":
            continue
        rel_path = file_path.relative_to(docs_root)
        if rel_path.suffix in {".css", ".js", ".yml", ".license", ".j2"}:
            continue
        if any(part in config.excluded_asset_dirs for part in rel_path.parts):
            continue
        rel_posix = rel_path.as_posix()
        if any(fnmatch.fnmatch(rel_posix, pat) for pat in config.excluded_build_artifacts):
            continue
        all_assets.add(rel_posix)

    if not all_assets:
        return []

    # Remove explicitly excluded assets before comparison.
    # excluded_assets paths are relative to docs_dir, matching the format of all_assets.
    excluded = {e.lstrip("/") for e in config.excluded_assets}
    all_assets -= excluded

    if not all_assets:
        return []

    used_assets: set[str] = set()
    for md_file in sorted(docs_root.rglob("*.md")):
        if md_file.is_symlink():
            continue
        content = md_file.read_text(encoding="utf-8")
        rel_md = md_file.relative_to(docs_root)
        page_dir = rel_md.parent.as_posix()
        if page_dir == ".":
            page_dir = ""
        used_assets |= check_asset_references(content, page_dir)

    return [Path(p) for p in calculate_unused_assets(all_assets, used_assets)]


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
        # ── 1.a Shield pass: scan every line (fences are NOT skipped) ────────
        # Collect SECRET events keyed by line number so duplicate suppression
        # (a definition URL that also matches scan_line_for_secrets) still works.
        secret_line_nos: set[int] = set()
        shield_events: list[HarvestEvent] = []
        with self.file_path.open(encoding="utf-8") as fh:
            for lineno, line in _skip_frontmatter(fh):
                for finding in scan_line_for_secrets(line, self.file_path, lineno):
                    shield_events.append((lineno, "SECRET", finding))
                    secret_line_nos.add(lineno)

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


def _iter_md_files(
    docs_root: Path,
    config: ZenzicConfig,
) -> Generator[Path, None, None]:
    """Yield absolute paths to .md files under docs_root, honouring exclusions."""
    for md_file in sorted(docs_root.rglob("*.md")):
        if md_file.is_symlink():
            continue
        rel = md_file.relative_to(docs_root)
        if any(part in config.excluded_dirs for part in rel.parts):
            continue
        yield md_file


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
    repo_root: Path,
    config: ZenzicConfig | None = None,
    *,
    validate_links: bool = False,
    workers: int | None = 1,
    verbose: bool = False,
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

    if config is None:
        config, _ = ZenzicConfig.load(repo_root)

    docs_root = repo_root / config.docs_dir
    if not docs_root.exists() or not docs_root.is_dir():
        return [], []

    rule_engine = _build_rule_engine(config)
    md_files = list(_iter_md_files(docs_root, config))

    if not md_files:
        return [], []

    use_parallel = workers != 1 and len(md_files) >= ADAPTIVE_PARALLEL_THRESHOLD

    _t0 = time.monotonic()

    if use_parallel:
        import concurrent.futures
        import os

        work_items = [(f, config, rule_engine) for f in md_files]
        actual_workers = workers if workers is not None else os.cpu_count() or 1
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
            raw = list(executor.map(_worker, work_items))
        reports: list[IntegrityReport] = sorted(raw, key=lambda r: r.file_path)

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
        return reports_seq, []

    # Phase B — global URL deduplication and async HTTP validation.
    # Uses the already-populated ref_maps from Phase A — no second file read.
    validator_seq = LinkValidator()
    for scanner in secure_scanners_seq:
        validator_seq.register_from_map(scanner.ref_map, scanner.file_path)
    return reports_seq, validator_seq.validate()


# ─── Adaptive parallel worker ─────────────────────────────────────────────────

#: Files below this threshold are scanned sequentially (zero process-spawn
#: overhead).  Above it, the AdaptiveRuleEngine switches to a
#: ProcessPoolExecutor automatically.  Exposed as a module constant so tests
#: can override it without patching private internals.
ADAPTIVE_PARALLEL_THRESHOLD: int = 50


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
