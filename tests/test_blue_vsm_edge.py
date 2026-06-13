# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""TEAM BLUE — VSM edge-case stress tests.

Tests unusual structures: special characters, .mdx/.md mixing,
files outside docs/, nested paths, collision detection edge cases.
"""

from __future__ import annotations

from pathlib import Path

from zenzic.core.adapters._docusaurus import DocusaurusAdapter
from zenzic.core.adapters._mkdocs import MkDocsAdapter
from zenzic.core.adapters._standalone import StandaloneAdapter
from zenzic.models.config import BuildContext
from zenzic.models.vsm import Route, _detect_collisions, build_vsm


# ── Helpers ──────────────────────────────────────────────────────────────────


def _docusaurus(tmp_path: Path, locales: list[str] | None = None) -> DocusaurusAdapter:
    ctx = BuildContext(engine="docusaurus", locales=locales or [])
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    return DocusaurusAdapter(ctx, docs)


def _mkdocs(docs_root: Path, config: dict | None = None) -> MkDocsAdapter:  # type: ignore[type-arg]
    return MkDocsAdapter(BuildContext(), docs_root, config or {})


# ═══════════════════════════════════════════════════════════════════════════════
# VSM-EDGE-01: .mdx vs .md mixed usage (Docusaurus)
# ═══════════════════════════════════════════════════════════════════════════════


class TestMdxMdMixing:
    """Docusaurus projects may have both .md and .mdx files."""

    def test_md_and_mdx_same_stem_collide(self, tmp_path: Path) -> None:
        """guide/install.md and guide/install.mdx → same URL → CONFLICT."""
        adapter = _docusaurus(tmp_path)
        url_md = adapter.get_route_info(Path("guide/install.md")).canonical_url
        url_mdx = adapter.get_route_info(Path("guide/install.mdx")).canonical_url
        assert url_md == url_mdx == "/docs/guide/install/"

        routes = [
            Route(url=url_md, source="guide/install.md", status="REACHABLE"),
            Route(url=url_mdx, source="guide/install.mdx", status="REACHABLE"),
        ]
        _detect_collisions(routes)
        assert all(r.status == "CONFLICT" for r in routes)

    def test_index_md_and_index_mdx_collide(self, tmp_path: Path) -> None:
        """index.md and index.mdx both map to / → CONFLICT."""
        adapter = _docusaurus(tmp_path)
        url1 = adapter.get_route_info(Path("index.md")).canonical_url
        url2 = adapter.get_route_info(Path("index.mdx")).canonical_url
        assert url1 == url2 == "/docs/"

    def test_different_dirs_no_collision(self, tmp_path: Path) -> None:
        """guide/install.md and api/install.mdx → different URLs."""
        adapter = _docusaurus(tmp_path)
        assert (
            adapter.get_route_info(Path("guide/install.md")).canonical_url == "/docs/guide/install/"
        )
        assert adapter.get_route_info(Path("api/install.mdx")).canonical_url == "/docs/api/install/"


# ═══════════════════════════════════════════════════════════════════════════════
# VSM-EDGE-02: Special characters in filenames
# ═══════════════════════════════════════════════════════════════════════════════


class TestSpecialCharacterFilenames:
    """File names with spaces, dots, dashes, underscores in Docusaurus."""

    def test_spaces_in_filename(self, tmp_path: Path) -> None:
        adapter = _docusaurus(tmp_path)
        url = adapter.get_route_info(Path("my guide.md")).canonical_url
        assert url == "/docs/my guide/"

    def test_dots_in_filename(self, tmp_path: Path) -> None:
        adapter = _docusaurus(tmp_path)
        url = adapter.get_route_info(Path("v1.2.3-release.md")).canonical_url
        # Should strip .md, keep dots in stem
        assert url == "/docs/v1.2.3-release/"

    def test_dashes_in_filename(self, tmp_path: Path) -> None:
        adapter = _docusaurus(tmp_path)
        url = adapter.get_route_info(Path("getting-started.mdx")).canonical_url
        assert url == "/docs/getting-started/"

    def test_underscored_file_not_in_underscore_dir(self, tmp_path: Path) -> None:
        """_intro.md inside a non-underscore dir is still IGNORED (Docusaurus rule)."""
        adapter = _docusaurus(tmp_path)
        status = adapter.get_route_info(Path("_intro.md")).status
        assert status == "IGNORED"

    def test_deeply_nested_path(self, tmp_path: Path) -> None:
        adapter = _docusaurus(tmp_path)
        url = adapter.get_route_info(Path("a/b/c/d/e/f.md")).canonical_url
        assert url == "/docs/a/b/c/d/e/f/"


# ═══════════════════════════════════════════════════════════════════════════════
# VSM-EDGE-03: build_vsm with Docusaurus adapter end-to-end
# ═══════════════════════════════════════════════════════════════════════════════


class TestBuildVsmDocusaurus:
    """End-to-end VSM building with Docusaurus adapter."""

    def test_mixed_md_mdx_vsm(self, tmp_path: Path) -> None:
        adapter = _docusaurus(tmp_path)
        docs = tmp_path / "docs"
        for f in ["index.mdx", "guide/install.md", "guide/config.mdx"]:
            p = docs / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"# {f}\n")

        md_contents = {
            (docs / f).resolve(): f"# {f}\n"
            for f in ["index.mdx", "guide/install.md", "guide/config.mdx"]
        }
        vsm = build_vsm(adapter, docs.resolve(), md_contents)
        assert "/docs/" in vsm
        assert "/docs/guide/install/" in vsm
        assert "/docs/guide/config/" in vsm
        assert all(r.status == "REACHABLE" for r in vsm.values())

    def test_slug_override_in_vsm(self, tmp_path: Path) -> None:
        adapter = _docusaurus(tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir(exist_ok=True)
        (docs / "intro.mdx").write_text("---\nslug: /\n---\n# Intro\n")
        (docs / "guide.md").write_text("---\nslug: /getting-started\n---\n# Guide\n")

        md_contents = {
            (docs / "intro.mdx").resolve(): "---\nslug: /\n---\n# Intro\n",
            (docs / "guide.md").resolve(): "---\nslug: /getting-started\n---\n# Guide\n",
        }
        adapter.set_slug_map(md_contents)
        vsm = build_vsm(adapter, docs.resolve(), md_contents)
        # Absolute slugs are prefixed with routeBasePath (Docusaurus spec).
        assert "/docs/" in vsm
        assert "/docs/getting-started/" in vsm


# ═══════════════════════════════════════════════════════════════════════════════
# VSM-EDGE-04: Collision detection edge cases
# ═══════════════════════════════════════════════════════════════════════════════


class TestCollisionEdgeCases:
    """Edge cases in _detect_collisions."""

    def test_empty_routes(self) -> None:
        _detect_collisions([])  # should not raise

    def test_single_route_no_collision(self) -> None:
        r = Route(url="/a/", source="a.md", status="REACHABLE")
        _detect_collisions([r])
        assert r.status == "REACHABLE"

    def test_collision_preserves_source(self) -> None:
        """After collision, source paths are preserved."""
        r1 = Route(url="/x/", source="x.md", status="REACHABLE")
        r2 = Route(url="/x/", source="y.md", status="REACHABLE")
        _detect_collisions([r1, r2])
        assert r1.source == "x.md"
        assert r2.source == "y.md"

    def test_four_way_collision(self) -> None:
        routes = [Route(url="/z/", source=f"{i}.md", status="REACHABLE") for i in range(4)]
        _detect_collisions(routes)
        assert all(r.status == "CONFLICT" for r in routes)


# ═══════════════════════════════════════════════════════════════════════════════
# VSM-EDGE-05: MkDocs with nested sidebar structures
# ═══════════════════════════════════════════════════════════════════════════════


class TestMkDocsNestedNav:
    """MkDocs nav can have deeply nested structures."""

    def test_deeply_nested_nav_page_reachable(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        config = {"nav": [{"Section A": [{"Subsection": [{"Deep Page": "a/b/c/deep.md"}]}]}]}
        adapter = _mkdocs(docs, config)
        nav_paths = adapter.get_nav_paths()
        assert "a/b/c/deep.md" in nav_paths
        assert adapter.get_route_info(Path("a/b/c/deep.md")).status == "REACHABLE"

    def test_page_not_in_nested_nav_is_orphan(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        config = {"nav": [{"Home": "index.md"}]}
        adapter = _mkdocs(docs, config)
        assert adapter.get_route_info(Path("unlisted.md")).status == "ORPHAN_BUT_EXISTING"


# ═══════════════════════════════════════════════════════════════════════════════
# VSM-EDGE-06: StandaloneAdapter always REACHABLE
# ═══════════════════════════════════════════════════════════════════════════════


class TestStandaloneEdgeCases:
    """StandaloneAdapter treats everything as reachable."""

    def test_deeply_nested(self) -> None:
        adapter = StandaloneAdapter()
        assert adapter.get_route_info(Path("a/b/c/d.md")).canonical_url == "/a/b/c/d/"

    def test_special_chars(self) -> None:
        adapter = StandaloneAdapter()
        url = adapter.get_route_info(Path("my-file (1).md")).canonical_url
        assert "/my-file (1)/" == url
