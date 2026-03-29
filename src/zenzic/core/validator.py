# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Validation logic: native link checking (internal + external) and Python snippet checks.

Link validation no longer invokes any external process.  Instead it uses a
pure-Python two-pass approach:

1. Read every ``.md`` file under ``docs/`` into memory, extract all Markdown
   links while skipping fenced code blocks and inline code spans.
2. *Internal links* (relative or site-absolute paths) are resolved against the
   pre-built in-memory file map; ``#anchor`` fragments are validated against
   heading slugs extracted from the target file.
3. *External links* (``http://`` / ``https://``) are validated lazily — only
   when ``strict=True`` — via concurrent HEAD requests through ``httpx``.
"""

from __future__ import annotations

import asyncio
import fnmatch
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple
from urllib.parse import urlsplit

import httpx
import yaml

from zenzic.core.adapter import get_adapter
from zenzic.core.exceptions import ConfigurationError
from zenzic.core.resolver import (
    AnchorMissing,
    FileNotFound,
    InMemoryPathResolver,
    PathTraversal,
    Resolved,
)
from zenzic.models.config import ZenzicConfig
from zenzic.models.references import ReferenceMap


# ─── YAML loader (boundary layer — ignores unknown tags like MkDocs !ENV) ────


class _PermissiveSafeLoader(yaml.SafeLoader):
    """SafeLoader that silently ignores unknown YAML tags (e.g. MkDocs !ENV)."""


_PermissiveSafeLoader.add_multi_constructor("", lambda loader, tag_suffix, node: None)  # type: ignore[no-untyped-call]


# ─── i18n Fallback Configuration ─────────────────────────────────────────────


class I18nFallbackConfig(NamedTuple):
    """i18n fallback resolution config derived from the docs generator config.

    When ``enabled`` is ``True``, a :class:`FileNotFound` outcome for a link
    whose source is under a non-default locale directory is re-checked against
    the default-locale tree before an error is emitted.  This mirrors the
    ``fallback_to_default`` behaviour of the ``mkdocs-i18n`` plugin.

    Attributes:
        enabled: ``True`` when ``fallback_to_default`` is active in the config.
        default_locale: Locale string of the default language (e.g. ``"en"``).
        locale_dirs: Frozenset of non-default locale directory names
            (e.g. ``frozenset({"it", "fr"})``).
    """

    enabled: bool
    default_locale: str
    locale_dirs: frozenset[str]


_I18N_FALLBACK_DISABLED: I18nFallbackConfig = I18nFallbackConfig(
    enabled=False, default_locale="", locale_dirs=frozenset()
)


# ─── Regexes ──────────────────────────────────────────────────────────────────

# Matches inline Markdown links [text](url) and images ![alt](url).
# Captures the raw content inside the parentheses (group 1).
# Does NOT match reference-style links [text][id] or auto-links <url>.
_MARKDOWN_LINK_RE = re.compile(r"!?\[[^\[\]]*\]\(([^)]+)\)")

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

# URL schemes that are valid syntax but point to non-HTTP targets we skip.
_SKIP_SCHEMES = ("mailto:", "data:", "ftp:", "tel:", "javascript:", "irc:", "xmpp:")

# Maximum number of simultaneous outbound HTTP connections during external link checks.
# Prevents exhausting OS file descriptors and avoids triggering rate-limits on target servers.
_MAX_CONCURRENT_REQUESTS = 20


# ─── Data classes ─────────────────────────────────────────────────────────────


@dataclass(slots=True)
class SnippetError:
    file_path: Path
    line_no: int
    message: str


# ─── Pure / I/O-agnostic functions ────────────────────────────────────────────


def extract_links(text: str) -> list[tuple[str, int]]:
    """Extract ``(url, 1-based-line-no)`` pairs from markdown, ignoring code blocks.

    Skips content inside fenced code blocks (````` ``` ````` / ``~~~``) and
    inline code spans (`` ` `` ) so that example links in documentation are
    never mistaken for real targets.  Optional link titles (``"title"`` /
    ``'title'``) are stripped so callers receive clean URL strings.

    Args:
        text: Raw markdown content.

    Returns:
        List of ``(url, line_number)`` pairs in document order.
    """
    results: list[tuple[str, int]] = []
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
                results.append((url, lineno))

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
    slug = _HTML_TAG_RE.sub("", heading).lower().strip()
    # Decompose accented characters and drop combining marks so that e.g.
    # "Integrità" → "integrita" (matching MkDocs toc extension behaviour).
    slug = unicodedata.normalize("NFKD", slug)
    slug = "".join(c for c in slug if not unicodedata.combining(c))
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


# ─── i18n fallback pure helpers ──────────────────────────────────────────────


def _extract_i18n_fallback_config(doc_config: dict[str, Any]) -> I18nFallbackConfig:
    """Extract i18n fallback config from a parsed docs generator config dict.

    Returns :data:`_I18N_FALLBACK_DISABLED` for any configuration that does
    not use folder-based i18n with ``fallback_to_default: true``.

    Args:
        doc_config: Parsed YAML config dict (e.g. from ``mkdocs.yml``).

    Returns:
        :class:`I18nFallbackConfig` describing the fallback settings.

    Raises:
        :class:`~zenzic.core.exceptions.ConfigurationError`: When
            ``fallback_to_default: true`` is set in folder mode but no
            language entry has ``default: true``.  Zenzic cannot infer
            the fallback target locale.
    """
    plugins = doc_config.get("plugins")
    if not isinstance(plugins, list):
        return _I18N_FALLBACK_DISABLED
    for plugin in plugins:
        if not isinstance(plugin, dict):
            continue
        i18n = plugin.get("i18n")
        if not isinstance(i18n, dict):
            continue
        if i18n.get("docs_structure") != "folder":
            break
        if not i18n.get("fallback_to_default", False):
            return _I18N_FALLBACK_DISABLED
        # fallback_to_default: true — locate the default locale
        default_locale = ""
        locale_dirs: set[str] = set()
        for lang in i18n.get("languages") or []:
            if not isinstance(lang, dict):
                continue
            locale = lang.get("locale", "")
            if not locale:
                continue
            if lang.get("default", False):
                default_locale = locale
            else:
                locale_dirs.add(locale)
        # Treat null/empty languages as "not configured" — null-safety guard.
        # Only raise ConfigurationError when languages is a non-empty list
        # but none of its entries declares default: true.
        if not locale_dirs and not default_locale:
            return _I18N_FALLBACK_DISABLED
        if not default_locale:
            raise ConfigurationError(
                "i18n plugin has fallback_to_default: true but no language with "
                "default: true — Zenzic cannot determine the fallback target locale.",
                context={"docs_structure": "folder", "fallback_to_default": True},
            )
        return I18nFallbackConfig(
            enabled=True,
            default_locale=default_locale,
            locale_dirs=frozenset(locale_dirs),
        )
    return _I18N_FALLBACK_DISABLED


def _should_suppress_via_i18n_fallback(
    asset_str: str,
    source_file: Path,
    docs_root: Path,
    href: str,
    fallback: I18nFallbackConfig,
    resolver: InMemoryPathResolver,
    known_assets: frozenset[str],
) -> bool:
    """Return ``True`` if a :class:`FileNotFound` is covered by i18n fallback.

    Mirrors the ``fallback_to_default`` behaviour of the MkDocs i18n plugin:
    when a translated file is absent, the build serves the default-locale
    version.  Zenzic suppresses the error when the link would resolve
    correctly if the source file were in the default-locale tree.

    The check applies only when the resolved missing path is *inside* the
    locale sub-tree (e.g. ``docs/it/api.md``).  Links that already navigate
    out of the locale dir at the Markdown level (e.g. ``../api.md`` which
    normalises to ``docs/api.md``) are :class:`Resolved` directly and never
    reach this function.

    Args:
        asset_str: Normalised absolute path string of the missing target.
        source_file: Absolute path of the file containing the link.
        docs_root: Absolute documentation root directory.
        href: Original href string (used for re-resolution from default root).
        fallback: Fallback config extracted from ``mkdocs.yml``.
        resolver: In-memory resolver instance (for ``.md`` fallback lookup).
        known_assets: Pre-built frozenset of non-``.md`` asset paths.

    Returns:
        ``True`` if the error should be suppressed; ``False`` otherwise.
    """
    if not fallback.enabled:
        return False
    source_rel = source_file.relative_to(docs_root)
    if not source_rel.parts or source_rel.parts[0] not in fallback.locale_dirs:
        return False

    locale = source_rel.parts[0]
    locale_prefix = str(docs_root) + os.sep + locale + os.sep

    # Fallback only applies when the missing target is inside the locale tree.
    if not asset_str.startswith(locale_prefix):
        return False

    stripped = asset_str[len(locale_prefix) :]
    fallback_str = os.path.normpath(str(docs_root) + os.sep + stripped)

    # Non-.md assets: check the pre-built known_assets frozenset.
    if fallback_str in known_assets:
        return True

    # .md files: re-resolve from the default-locale equivalent source.
    # _build_target uses only source_file.parent — the virtual source does
    # not need to exist on disk.
    rest = source_rel.parts[1:]
    if not rest:
        return False
    default_source = docs_root / Path(*rest)
    match resolver.resolve(default_source, href):
        case Resolved():
            return True
    return False


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


def extract_ref_links(text: str, ref_map: dict[str, str]) -> list[tuple[str, int]]:
    """Resolve reference-style links against *ref_map* and return ``(url, lineno)`` pairs.

    Handles ``[text][id]`` and collapsed ``[text][]`` syntax.  Skips fenced
    code blocks and inline code spans.  Only links whose normalised ID appears
    in *ref_map* are returned — undefined IDs are the responsibility of
    :class:`~zenzic.core.scanner.ReferenceScanner`.

    Reference IDs are compared case-insensitively per CommonMark §4.7.

    Args:
        text: Raw markdown content.
        ref_map: Mapping returned by :func:`_build_ref_map` (lowercase IDs).

    Returns:
        List of ``(resolved_url, 1-based-line-number)`` pairs in document order.
    """
    results: list[tuple[str, int]] = []
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
                results.append((url, lineno))
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
) -> list[str]:
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
        repo_root: Repository root directory (must contain ``docs/``).
        strict: When ``True``, also validate external HTTP/HTTPS links via
            network.  Adds latency; disabled by default for fast CI runs.

    Returns:
        Sorted list of human-readable error strings; empty when all links pass.
    """
    config, _ = ZenzicConfig.load(repo_root)
    docs_root = (repo_root / config.docs_dir).resolve()

    if not docs_root.is_dir():
        return []

    # ── Instantiate the build-engine adapter (locale-aware path resolution) ──
    adapter = get_adapter(config.build_context, docs_root, repo_root)

    # ── Pass 1: read all .md files + map all non-.md assets into memory ──────
    md_contents: dict[Path, str] = {}
    for md_file in sorted(docs_root.rglob("*.md")):
        if md_file.is_symlink():
            continue
        rel = md_file.relative_to(docs_root)
        if any(part in config.excluded_dirs for part in rel.parts):
            continue
        try:
            md_contents[md_file.resolve()] = md_file.read_text(encoding="utf-8")
        except OSError:
            continue

    # Build the asset map once — eliminates all Path.exists() calls from Pass 2.
    # Stores resolved absolute path strings so the Pass 2 lookup is a single
    # frozenset membership test (O(1), zero allocations per link).
    known_assets: frozenset[str] = frozenset(
        str(f.resolve())
        for f in docs_root.rglob("*")
        if f.is_file() and not f.is_symlink() and f.suffix != ".md"
    )

    # Build reference maps from pre-loaded content (pure, no extra I/O).
    # Used in Pass 2 to resolve [text][id] reference-style links.
    ref_maps: dict[Path, dict[str, str]] = {
        path: _build_ref_map(content) for path, content in md_contents.items()
    }

    # Pre-compute anchor sets once so target files are never re-parsed.
    anchors_cache: dict[Path, set[str]] = {
        path: anchors_in_file(content) for path, content in md_contents.items()
    }

    # Instantiate the resolver ONCE — _lookup_map is built here, not per-link.
    # Instantiating inside the file loop would regenerate the map N times,
    # cancelling the 14× performance gain from the pre-computed flat dict.
    resolver = InMemoryPathResolver(docs_root, md_contents, anchors_cache)

    # ── Pass 2: extract links (inline + reference-style) and validate ─────────
    internal_errors: list[str] = []
    external_entries: list[tuple[str, str, int]] = []  # (url, file_label, lineno)

    for md_file, content in md_contents.items():
        label = str(md_file.relative_to(docs_root))
        file_ref_map = ref_maps.get(md_file, {})

        # Combine inline links and resolved reference-style links into one pass.
        # extract_links handles [text](url); extract_ref_links handles [text][id].
        all_links = extract_links(content) + extract_ref_links(content, file_ref_map)

        for url, lineno in all_links:
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
                            f"{label}:{lineno}: anchor '#{anchor}' not found in '{label}'"
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
                    f"{label}:{lineno}: '{url}' uses an absolute path — "
                    "use a relative path (e.g. '../' or './') instead; "
                    "absolute paths break portability when the site is hosted "
                    "in a subdirectory"
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
                    internal_errors.append(
                        f"{label}:{lineno}: '{url}' resolves outside the docs directory"
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
                                f"{label}:{lineno}: '{path_part}' not found in docs"
                            )
                case AnchorMissing(path_part=path_part, anchor=anchor):
                    internal_errors.append(
                        f"{label}:{lineno}: anchor '#{anchor}' not found in '{path_part}'"
                    )
                case Resolved():
                    pass

    internal_errors.sort()

    if not strict:
        return internal_errors

    # ── Pass 3 (strict only): validate external links ─────────────────────────
    excluded = config.excluded_external_urls
    if excluded:
        external_entries = [
            (url, label, lineno)
            for url, label, lineno in external_entries
            if not any(url.startswith(prefix) for prefix in excluded)
        ]
    ext_errors = await _check_external_links(external_entries)
    return internal_errors + ext_errors


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
    for md_file in docs_root.rglob("*.md"):
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
    return asyncio.run(validate_links_async(repo_root, strict=strict))


# ─── Python snippet validation ────────────────────────────────────────────────


def _extract_python_blocks(text: str) -> list[tuple[str, int]]:
    """Return (snippet, fence_line_no) pairs for every fenced Python block in *text*.

    Uses a deterministic line-by-line state machine rather than a regex so that
    inline triple-backtick code spans (e.g. `` ` ```python ` ``) cannot cause the
    matcher to run away across the rest of the file.

    *fence_line_no* is the 1-based line number of the opening fence.  The closing
    fence must be a line whose stripped content is exactly three or more backticks
    (per CommonMark §4.5).
    """
    blocks: list[tuple[str, int]] = []
    in_block = False
    block_lines: list[str] = []
    fence_line_no = 0

    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not in_block:
            if stripped.startswith("```"):
                info = stripped[3:].strip()
                lang = info.split()[0].lower() if info else ""
                if lang in ("python", "py"):
                    in_block = True
                    block_lines = []
                    fence_line_no = lineno
        else:
            # Closing fence: line is only backtick characters (at least 3)
            if stripped.startswith("```") and not stripped.lstrip("`"):
                blocks.append(("\n".join(block_lines), fence_line_no))
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
    """Pure function: compile Python fenced code blocks in text. No I/O.

    Args:
        text: Raw markdown content to analyse.
        file_path: Path identifier used to label errors (no disk access).
        config: Optional Zenzic configuration.

    Returns:
        List of SnippetError instances for each invalid Python code block.
    """
    if config is None:
        config = ZenzicConfig()

    path = Path(file_path)
    errors: list[SnippetError] = []

    for snippet, fence_line in _extract_python_blocks(text):
        if len(snippet.strip().splitlines()) < config.snippet_min_lines:
            continue

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
    """Compile every Python fenced code block in docs and report syntax errors.

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

    for md_file in sorted(docs_root.rglob("*.md")):
        if md_file.is_symlink():
            continue

        rel_path = md_file.relative_to(docs_root)

        if any(part in config.excluded_dirs for part in rel_path.parts):
            continue

        content = md_file.read_text(encoding="utf-8")
        errors.extend(check_snippet_content(content, rel_path, config))

    return errors
