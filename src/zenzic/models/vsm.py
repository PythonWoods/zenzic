# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Virtual Site Map (VSM) data model.

The VSM is the single source of truth for routing: it maps every physical
Markdown source file to the canonical URL the build engine will serve,
together with a reachability status and the set of heading anchors.

Design principles (The Zenzic Way):
- Pure data, no I/O.  ``Route`` is a frozen dataclass; ``VSM`` is a plain dict.
- ``build_vsm()`` is the only I/O entry point; it delegates URL mapping to the
  adapter and collision detection to ``_detect_collisions()``.
- Status values match the Routing Table Specification in the project brief.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


_log = logging.getLogger(__name__)


# ─── Status type ──────────────────────────────────────────────────────────────

RouteStatus = Literal["REACHABLE", "ORPHAN_BUT_EXISTING", "IGNORED", "CONFLICT"]


# ─── Route ────────────────────────────────────────────────────────────────────


@dataclass
class Route:
    """One entry in the Virtual Site Map.

    Attributes:
        url:     Canonical URL path (e.g. ``/guide/installation/``).
        source:  Physical path of the Markdown source file, relative to
                 ``docs_root`` (e.g. ``guide/installation.md``).
        status:  Routing status:

                 ``REACHABLE``
                     The page is reachable via the site navigation (listed in
                     nav for MkDocs, or all files for Zensical).
                 ``ORPHAN_BUT_EXISTING``
                     The file exists on disk but is **not** referenced in the
                     nav.  The build engine will still render it (it is
                     accessible via direct URL), but it has no navigation
                     entry — it is invisible to browsing users.
                 ``IGNORED``
                     The file should not be served (e.g. ``README.md`` not
                     in nav for MkDocs, files in ``_private/`` dirs for
                     Zensical).
                 ``CONFLICT``
                     Two or more source files map to the same canonical URL.
                     The build result is undefined/engine-dependent.

        anchors: Heading anchor slugs extracted from the source file
                 (e.g. ``{'installation', 'quick-start'}``).
        aliases: Additional URL aliases or redirects for this page (reserved
                 for future use; populated by adapters that support redirect
                 declarations).
    """

    url: str
    source: str
    status: RouteStatus
    anchors: set[str] = field(default_factory=set)
    aliases: set[str] = field(default_factory=set)
    proxy_sources: frozenset[str] = field(default_factory=frozenset)

    # Convenience ──────────────────────────────────────────────────────────────

    @property
    def is_reachable(self) -> bool:
        """``True`` when status is ``REACHABLE``."""
        return self.status == "REACHABLE"

    @property
    def is_conflict(self) -> bool:
        """``True`` when status is ``CONFLICT``."""
        return self.status == "CONFLICT"


# ─── VSM type alias ────────────────────────────────────────────────────────────

# Canonical URL → Route.  All routes (including IGNORED) are included so that
# links to ignored files (e.g. _private/ in Zensical) can be caught as
# UNREACHABLE_LINK by the validator.
VSM = dict[str, Route]


# ─── Collision detection (pure, adapter-independent) ─────────────────────────


def _detect_collisions(routes: list[Route]) -> None:
    """Mark conflicting routes in-place.

    Two routes conflict when they share the same canonical URL.  Both are
    marked ``CONFLICT`` (the first one too, to avoid silent shadowing).

    Pure function: no I/O, mutates only the ``status`` field of the provided
    ``Route`` objects.

    Args:
        routes: List of ``Route`` objects (mutated in-place).
    """
    seen: dict[str, Route] = {}
    for route in routes:
        if route.url in seen:
            route.status = "CONFLICT"
            seen[route.url].status = "CONFLICT"
        else:
            seen[route.url] = route


# ─── VSM builder (I/O boundary) ───────────────────────────────────────────────


def build_vsm(
    adapter: object,
    docs_root: Path,
    md_contents: dict[Path, str],
    *,
    anchors_cache: dict[Path, set[str]] | None = None,
    extra_content_roots: list[tuple[Path, str]] | None = None,
) -> VSM:
    """Build the Virtual Site Map from a pre-loaded file map.

    This is the I/O boundary: all file content has already been loaded into
    ``md_contents`` by the caller (``validate_links_async``).  No disk reads
    occur here.

    Routing resolution strategy (v0.6.0a1+):

    1. **Metadata-Driven** — when the adapter implements ``get_route_info()``,
       the builder calls it once per file to obtain :class:`RouteMetadata`
       containing canonical URL, status, slug, and proxy flag in a single
       dispatch — eliminating the double-call overhead.
    2. **Legacy File-to-URL** — when ``get_route_info()`` is not available,
       the builder falls back to calling ``map_url()`` + ``classify_route()``
       separately (backward-compatible with third-party adapters).

    Multi-Root resolution (v0.7.x):

    Files under ``docs_root`` are routed using ``rel = path.relative_to(docs_root)``.
    Files under any of the *extra_content_roots* are routed with the declared
    ``url_prefix`` injected as the first ``rel`` segment, so the active adapter
    can disambiguate (e.g. Docusaurus blog posts) without a separate dispatch.
    Files outside both sets (locale translations) carry no canonical URL and
    are skipped — they are validated for link integrity only.

    Workflow:

    1. Iterate over every ``.md`` file in ``md_contents``.
    2. Compute routing metadata via the preferred API.
    3. Run ``_detect_collisions()`` across all routes.
    4. Build and return the ``VSM`` dict.

    Args:
        adapter:             Build-engine adapter.  Must implement either
                             ``get_route_info(rel)`` or the legacy
                             ``map_url(rel)`` + ``classify_route(rel, nav_paths)``
                             + ``get_nav_paths()``.
        docs_root:           Resolved absolute path to the ``docs/`` directory.
        md_contents:         Pre-loaded mapping of absolute ``Path`` → raw Markdown.
        anchors_cache:       Pre-computed ``Path`` → anchor slug set.  When
                             ``None``, anchors are left as empty sets.
        extra_content_roots: Optional list of ``(root_path, url_prefix)`` pairs
                             from the adapter's ``get_extra_content_roots()``.
                             Files under these roots are admitted to the VSM
                             with the prefix injected at the front of their
                             relative path.

    Returns:
        ``VSM`` mapping canonical URL → ``Route`` (IGNORED entries omitted).
    """
    ac = anchors_cache or {}
    extra_roots: list[tuple[Path, str]] = list(extra_content_roots or [])

    # Detect which routing API the adapter supports.
    use_metadata_api = hasattr(adapter, "get_route_info") and callable(
        getattr(adapter, "get_route_info", None)
    )

    # Legacy path needs nav_paths pre-computed once.
    nav_paths: frozenset[str] = frozenset()
    if not use_metadata_api:
        nav_paths = adapter.get_nav_paths()  # type: ignore[attr-defined]

    routes: list[Route] = []
    for abs_path, _content in md_contents.items():
        # ── Resolve the logical rel and source label ────────────────────────
        # Files under docs_root use their ordinary relative path.  Files under
        # an extra content root carry the URL prefix as their first segment so
        # the adapter can disambiguate.  Anything else (locale translations)
        # carries no canonical URL — skipped here, validated elsewhere.
        if abs_path.is_relative_to(docs_root):
            rel = abs_path.relative_to(docs_root)
        else:
            matched_root: tuple[Path, str] | None = None
            for root, prefix in extra_roots:
                if abs_path.is_relative_to(root):
                    matched_root = (root, prefix)
                    break
            if matched_root is None:
                continue
            root, prefix = matched_root
            inner = abs_path.relative_to(root)
            rel = (Path(prefix) / inner) if prefix else inner
        rel_posix = rel.as_posix()

        if use_metadata_api:
            meta = adapter.get_route_info(rel)  # type: ignore[attr-defined]
            url = meta.canonical_url
            status: RouteStatus = meta.status
        else:
            url = adapter.map_url(rel)  # type: ignore[attr-defined]
            status = adapter.classify_route(rel, nav_paths)  # type: ignore[attr-defined]

        route = Route(
            url=url,
            source=rel_posix,
            status=status,
            anchors=set(ac.get(abs_path, set())),
        )
        routes.append(route)

    if hasattr(adapter, "get_virtual_routes"):
        for vr in adapter.get_virtual_routes(md_contents):
            # Layer 2 defensive check (layer 1 already enforced in __post_init__)
            if not vr.source_files:  # pragma: no cover
                _log.error("VirtualRoute %r escaped invariant — skipped", vr.url)
                continue
            routes.append(
                Route(
                    url=vr.url,
                    source="<virtual>",
                    status="REACHABLE",
                    proxy_sources=vr.source_files,
                )
            )

    _detect_collisions(routes)

    return {r.url: r for r in routes}
