# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Guardians Truth Gate — DocusaurusAdapter discrepancy validation.

Each test class below corresponds to one specific discrepancy found by
auditing the official Docusaurus v3 source code during the v0.6.1 sprint.

The SOURCE OF TRUTH for each test is documented with the exact file and
line from the official engine repository.

Discrepancies covered:

  TRUTH-001  Latest version served at routeBasePath root (no version prefix).
             Source: docusaurus-plugin-content-docs/src/docs.ts — versioning table.
             Docusaurus: versioned_docs/version-1.1.0/hello.md (latest)
                         → /docs/hello  (no "1.1.0" in URL)
             Old bug:    → /docs/1.1.0/hello  (false version prefix)

  TRUTH-002  Absolute slug is always prefixed with routeBasePath.
             Source: docusaurus-plugin-content-docs/src/docs.ts line ~185
                     `permalink = normalizeUrl([versionMetadata.path, docSlug])`
             Old bug:    slug: /bonjour → /bonjour/  (routeBasePath ignored)
             Correct:    slug: /bonjour → /docs/bonjour/

  TRUTH-003  isCategoryIndex collapses README and same-name-as-folder files.
             Source: docusaurus-plugin-content-docs/src/docs.ts — isCategoryIndex():
                     `fileName.toLowerCase() in ['index', 'readme', dirs[0]?.toLowerCase()]`
             Old bug:    guides/README.md → /docs/guides/README/  (not collapsed)
                         Guides/Guides.md → /docs/Guides/Guides/  (not collapsed)
             Correct:    guides/README.md → /docs/guides/
                         Guides/Guides.md → /docs/Guides/

  TRUTH-004  @site/ alias resolves to repo_root, not outside root_dir.
             Source: Docusaurus @site/ alias documentation.
             Old bug:    @site/static/img.png → PathTraversal  (escaped docs root)
             Correct:    @site/static/img.png → FileNotFound   (within repo_root)
                         @site/docs/guide/install.md → Resolved
"""

from __future__ import annotations

from pathlib import Path

from zenzic.core.adapters._docusaurus import DocusaurusAdapter
from zenzic.core.resolver import (
    FileNotFound,
    InMemoryPathResolver,
    PathTraversal,
    Resolved,
)
from zenzic.models.config import BuildContext


# ── Shared helpers ────────────────────────────────────────────────────────────

DOCS_ROOT = Path("/repo/docs")
REPO_ROOT = Path("/repo")


def _ctx(locales: list[str] | None = None) -> BuildContext:
    return BuildContext(
        engine="docusaurus",
        locales=locales or [],
        fallback_to_default=False,
        offline_mode=False,
    )


def _adapter(
    *,
    route_base_path: str | None = "docs",
    versions: list[str] | None = None,
    locales: list[str] | None = None,
) -> DocusaurusAdapter:
    return DocusaurusAdapter(
        _ctx(locales=locales),
        DOCS_ROOT,
        "/",
        route_base_path,
        versions or [],
    )


# ── TRUTH-001: Latest version served at routeBasePath root ───────────────────


class TestTruth001LatestVersionIsRoot:
    """The first entry in versions.json is 'latest' — no version label in URL.

    Official source: Docusaurus versioning documentation table.
    versions.json = ["1.1.0", "1.0.0"]  →  1.1.0 is latest.
    """

    def test_latest_version_produces_no_version_prefix(self) -> None:
        """versioned_docs/version-1.1.0/hello.md (latest) → /docs/hello/."""
        adapter = _adapter(versions=["1.1.0", "1.0.0"])
        url = adapter.map_url(Path("_version_/1.1.0/hello.md"))
        assert url == "/docs/hello/", (
            "Latest version must NOT include version label in URL. "
            f"Got: {url} — expected: /docs/hello/"
        )

    def test_older_version_produces_version_prefix(self) -> None:
        """versioned_docs/version-1.0.0/hello.md (older) → /docs/1.0.0/hello/."""
        adapter = _adapter(versions=["1.1.0", "1.0.0"])
        url = adapter.map_url(Path("_version_/1.0.0/hello.md"))
        assert url == "/docs/1.0.0/hello/", (
            "Non-latest version MUST include version label in URL. "
            f"Got: {url} — expected: /docs/1.0.0/hello/"
        )

    def test_single_version_is_treated_as_latest(self) -> None:
        """With only one version in versions.json, it is the latest."""
        adapter = _adapter(versions=["2.0.0"])
        url = adapter.map_url(Path("_version_/2.0.0/intro.md"))
        assert url == "/docs/intro/"

    def test_no_versions_list_is_unaffected(self) -> None:
        """Adapter with no versions list is not impacted."""
        adapter = _adapter(versions=[])
        url = adapter.map_url(Path("intro.md"))
        assert url == "/docs/intro/"

    def test_latest_version_nested_path(self) -> None:
        """Latest version preserves subdirectory structure without version label."""
        adapter = _adapter(versions=["3.0.0", "2.0.0", "1.0.0"])
        url = adapter.map_url(Path("_version_/3.0.0/guides/setup.md"))
        assert url == "/docs/guides/setup/"

    def test_older_version_nested_path(self) -> None:
        """Older versions retain their version label even for nested files."""
        adapter = _adapter(versions=["3.0.0", "2.0.0", "1.0.0"])
        url = adapter.map_url(Path("_version_/2.0.0/guides/setup.md"))
        assert url == "/docs/2.0.0/guides/setup/"

    def test_latest_version_index_collapse(self) -> None:
        """Latest version index.md collapses to routeBasePath root."""
        adapter = _adapter(versions=["1.1.0", "1.0.0"])
        url = adapter.map_url(Path("_version_/1.1.0/index.md"))
        assert url == "/docs/"

    def test_latest_version_attribute_stored(self) -> None:
        """_latest_version is the first entry in versions list."""
        adapter = _adapter(versions=["1.5.0", "1.4.0", "1.3.0"])
        assert adapter._latest_version == "1.5.0"  # noqa: SLF001

    def test_no_versions_latest_is_none(self) -> None:
        """_latest_version is None when no versions are provided."""
        adapter = _adapter(versions=[])
        assert adapter._latest_version is None  # noqa: SLF001


# ── TRUTH-002: Absolute slug prefixed with routeBasePath ─────────────────────


class TestTruth002AbsoluteSlugWithRouteBasePath:
    """Absolute frontmatter slug is always appended to routeBasePath.

    Official source: docusaurus-plugin-content-docs/src/docs.ts ~line 185
    `permalink = normalizeUrl([versionMetadata.path, docSlug])`
    versionMetadata.path IS the routeBasePath (e.g., '/docs').
    """

    def test_absolute_slug_prepends_route_base_path(self) -> None:
        """slug: /bonjour + routeBasePath=docs → /docs/bonjour/."""
        adapter = _adapter(route_base_path="docs")
        adapter.set_slug_map({DOCS_ROOT / "tutorial.md": "---\nslug: /bonjour\n---\n# T"})
        url = adapter.map_url(Path("tutorial.md"))
        assert url == "/docs/bonjour/", (
            "Absolute slug must be prefixed with routeBasePath. "
            f"Got: {url} — expected: /docs/bonjour/"
        )

    def test_absolute_slug_empty_route_base_path(self) -> None:
        """slug: /bonjour + routeBasePath='' → /bonjour/ (docs at site root)."""
        adapter = _adapter(route_base_path="")
        adapter.set_slug_map({DOCS_ROOT / "tutorial.md": "---\nslug: /bonjour\n---\n# T"})
        url = adapter.map_url(Path("tutorial.md"))
        assert url == "/bonjour/"

    def test_absolute_slug_custom_route_base_path(self) -> None:
        """slug: /abc + routeBasePath=reference → /reference/abc/."""
        adapter = _adapter(route_base_path="reference")
        adapter.set_slug_map({DOCS_ROOT / "api.md": "---\nslug: /abc\n---\n# A"})
        url = adapter.map_url(Path("api.md"))
        assert url == "/reference/abc/"

    def test_absolute_slug_nested_path(self) -> None:
        """slug: /custom/deep/path + routeBasePath=docs → /docs/custom/deep/path/."""
        adapter = _adapter(route_base_path="docs")
        adapter.set_slug_map({DOCS_ROOT / "page.md": "---\nslug: /custom/deep/path\n---\n# P"})
        url = adapter.map_url(Path("page.md"))
        assert url == "/docs/custom/deep/path/"

    def test_relative_slug_unchanged(self) -> None:
        """Relative slugs (no leading /) still replace the last path segment only."""
        adapter = _adapter(route_base_path="docs")
        adapter.set_slug_map({DOCS_ROOT / "guide/install.md": "---\nslug: setup\n---\n# S"})
        url = adapter.map_url(Path("guide/install.md"))
        assert url == "/guide/setup/"

    def test_default_route_base_path_used_when_none(self) -> None:
        """When route_base_path is None, Docusaurus default 'docs' is used."""
        adapter = _adapter(route_base_path=None)
        adapter.set_slug_map({DOCS_ROOT / "page.md": "---\nslug: /hello\n---\n# H"})
        url = adapter.map_url(Path("page.md"))
        assert url == "/docs/hello/"


# ── TRUTH-003: isCategoryIndex — README and same-name-as-folder collapsing ───


class TestTruth003SmartIndexCollapsing:
    """isCategoryIndex collapses README.md and {FolderName}/{FolderName}.md.

    Official source: docusaurus-plugin-content-docs/src/docs.ts — isCategoryIndex():
        fileName.toLowerCase() in ['index', 'readme', dirs[0]?.toLowerCase()]
    """

    def test_readme_md_collapses_to_parent(self) -> None:
        """guides/README.md → /docs/guides/ (not /docs/guides/readme/)."""
        adapter = _adapter()
        url = adapter.map_url(Path("guides/README.md"))
        assert url == "/docs/guides/"

    def test_readme_mdx_collapses_to_parent(self) -> None:
        """guides/README.mdx collapses identically to README.md."""
        adapter = _adapter()
        url = adapter.map_url(Path("guides/README.mdx"))
        assert url == "/docs/guides/"

    def test_readme_case_insensitive(self) -> None:
        """readme.md (lowercase) also collapses."""
        adapter = _adapter()
        url = adapter.map_url(Path("guides/readme.md"))
        assert url == "/docs/guides/"

    def test_index_uppercase_collapses(self) -> None:
        """INDEX.md (uppercase) collapses case-insensitively."""
        adapter = _adapter()
        url = adapter.map_url(Path("guides/INDEX.md"))
        assert url == "/docs/guides/"

    def test_same_name_as_folder_collapses(self) -> None:
        """Guides/Guides.md collapses to /docs/Guides/ (FolderName == FileName)."""
        adapter = _adapter()
        url = adapter.map_url(Path("Guides/Guides.md"))
        assert url == "/docs/Guides/"

    def test_same_name_as_folder_case_insensitive(self) -> None:
        """guides/GUIDES.md collapses case-insensitively."""
        adapter = _adapter()
        url = adapter.map_url(Path("guides/GUIDES.md"))
        assert url == "/docs/guides/"

    def test_same_name_lowercase(self) -> None:
        """guides/guides.md collapses to /docs/guides/."""
        adapter = _adapter()
        url = adapter.map_url(Path("guides/guides.md"))
        assert url == "/docs/guides/"

    def test_non_matching_name_does_not_collapse(self) -> None:
        """guides/intro.md does NOT collapse (intro != guides)."""
        adapter = _adapter()
        url = adapter.map_url(Path("guides/intro.md"))
        assert url == "/docs/guides/intro/"

    def test_standard_index_still_collapses(self) -> None:
        """Original index.md collapse still works after the smart expansion."""
        adapter = _adapter()
        url = adapter.map_url(Path("guides/index.md"))
        assert url == "/docs/guides/"

    def test_readme_at_root_collapses_to_root(self) -> None:
        """A top-level README.md collapses to the routeBasePath root."""
        adapter = _adapter()
        url = adapter.map_url(Path("README.md"))
        # No parent folder → parts = [] after collapse → /docs/
        assert url == "/docs/"

    def test_deep_nested_readme_collapses(self) -> None:
        """api/v2/README.md → /docs/api/v2/."""
        adapter = _adapter()
        url = adapter.map_url(Path("api/v2/README.md"))
        assert url == "/docs/api/v2/"

    def test_same_name_does_not_apply_at_root_level(self) -> None:
        """At root level there is no parent folder — same-name cannot match."""
        adapter = _adapter()
        # "guides.md" at root: parts[-1]="guides", no parts[-2] → no collapse
        url = adapter.map_url(Path("guides.md"))
        assert url == "/docs/guides/"


# ── TRUTH-004: @site/ alias resolves to repo_root ────────────────────────────


class TestTruth004SiteAliasResolvesToRepoRoot:
    """@site/ alias must resolve to repo_root, not escape via `../`.

    The original implementation built `root_str + "/.." + path`, causing the
    Shield to reject all @site/ non-docs links as PathTraversal.

    With explicit repo_root, the Shield accepts @site/ paths within repo_root.
    """

    def _make_resolver(self, repo_root: Path | None = None) -> InMemoryPathResolver:
        md_contents = {
            REPO_ROOT / "docs" / "guide" / "install.md": "# Install\n## Setup\n",
            REPO_ROOT / "docs" / "index.md": "# Home\n",
        }
        anchors: dict[Path, set[str]] = {
            REPO_ROOT / "docs" / "guide" / "install.md": {"install", "setup"},
        }
        return InMemoryPathResolver(
            root_dir=REPO_ROOT / "docs",
            md_contents=md_contents,
            anchors_cache=anchors,
            repo_root=repo_root,
        )

    def test_site_docs_resolves_to_file(self) -> None:
        """@site/docs/guide/install.md resolves to the actual file."""
        resolver = self._make_resolver(repo_root=REPO_ROOT)
        result = resolver.resolve(
            REPO_ROOT / "docs" / "index.md",
            "@site/docs/guide/install.md",
        )
        assert isinstance(result, Resolved)
        assert result.target == REPO_ROOT / "docs" / "guide" / "install.md"

    def test_site_docs_with_anchor_resolves(self) -> None:
        """@site/docs/guide/install.md#setup resolves with valid anchor."""
        resolver = self._make_resolver(repo_root=REPO_ROOT)
        result = resolver.resolve(
            REPO_ROOT / "docs" / "index.md",
            "@site/docs/guide/install.md#setup",
        )
        assert isinstance(result, Resolved)

    def test_site_non_docs_is_file_not_found_not_path_traversal(self) -> None:
        """@site/static/img.png with repo_root → FileNotFound (within repo_root).

        Before fix: PathTraversal (path escaped docs root via "/../").
        After fix:  FileNotFound (path is within repo_root, not in md_contents).
        """
        resolver = self._make_resolver(repo_root=REPO_ROOT)
        result = resolver.resolve(
            REPO_ROOT / "docs" / "index.md",
            "@site/static/img.png",
        )
        assert isinstance(result, FileNotFound), (
            "@site/static/img.png must be FileNotFound (within repo_root), "
            f"NOT PathTraversal. Got: {result!r}"
        )

    def test_site_alias_traversal_still_blocked(self) -> None:
        """@site/../../etc/passwd is still blocked by the Shield."""
        resolver = self._make_resolver(repo_root=REPO_ROOT)
        result = resolver.resolve(
            REPO_ROOT / "docs" / "index.md",
            "@site/../../etc/passwd",
        )
        assert isinstance(result, PathTraversal)

    def test_site_docs_without_repo_root_still_works(self) -> None:
        """@site/docs/ always works even when repo_root is not provided."""
        resolver = self._make_resolver(repo_root=None)
        result = resolver.resolve(
            REPO_ROOT / "docs" / "index.md",
            "@site/docs/guide/install.md",
        )
        assert isinstance(result, Resolved)

    def test_repo_root_stored_correctly(self) -> None:
        """repo_root is stored and accessible for Shield boundary checks."""
        resolver = self._make_resolver(repo_root=REPO_ROOT)
        assert resolver._repo_root_str == str(REPO_ROOT)  # noqa: SLF001

    def test_repo_root_defaults_to_root_dir(self) -> None:
        """When repo_root is None, _repo_root_str falls back to root_dir."""
        resolver = self._make_resolver(repo_root=None)
        assert resolver._repo_root_str == str(REPO_ROOT / "docs")  # noqa: SLF001

    def test_normal_relative_links_unaffected(self) -> None:
        """Non-@site/ links still resolve normally against root_dir."""
        resolver = self._make_resolver(repo_root=REPO_ROOT)
        result = resolver.resolve(
            REPO_ROOT / "docs" / "index.md",
            "guide/install.md",
        )
        assert isinstance(result, Resolved)

    def test_path_traversal_still_blocked_for_normal_links(self) -> None:
        """Normal links that escape root_dir are still PathTraversal."""
        resolver = self._make_resolver(repo_root=REPO_ROOT)
        result = resolver.resolve(
            REPO_ROOT / "docs" / "index.md",
            "../../etc/passwd",
        )
        assert isinstance(result, PathTraversal)
