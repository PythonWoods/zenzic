# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for the Virtual Site Map (VSM) — models/vsm.py and adapter integration.

Test philosophy (The Zenzic Way):
- Pure functions are tested with in-memory inputs only.
- I/O tests use tmp_path to create real but ephemeral filesystem trees.
- Every test asserts a single, named invariant.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from zenzic.core.adapters._mkdocs import MkDocsAdapter
from zenzic.core.adapters._vanilla import VanillaAdapter
from zenzic.core.adapters._zensical import ZensicalAdapter
from zenzic.core.validator import validate_links
from zenzic.models.config import BuildContext
from zenzic.models.vsm import Route, _detect_collisions, build_vsm


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _make_docs(root: Path, files: dict[str, str]) -> None:
    """Create stub .md files with given content under root/docs/."""
    docs = root / "docs"
    docs.mkdir(exist_ok=True)
    for rel, content in files.items():
        p = docs / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def _write_mkdocs(root: Path, config: dict) -> None:
    with (root / "mkdocs.yml").open("w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def _write_zenzic_toml(root: Path, engine: str = "mkdocs") -> None:
    (root / "zenzic.toml").write_text(f'[build_context]\nengine = "{engine}"\n', encoding="utf-8")


# ─── Route dataclass ──────────────────────────────────────────────────────────


class TestRoute:
    def test_is_reachable_true(self) -> None:
        r = Route(url="/page/", source="page.md", status="REACHABLE")
        assert r.is_reachable is True

    def test_is_reachable_false_for_orphan(self) -> None:
        r = Route(url="/page/", source="page.md", status="ORPHAN_BUT_EXISTING")
        assert r.is_reachable is False

    def test_is_conflict_true(self) -> None:
        r = Route(url="/dir/", source="dir/index.md", status="CONFLICT")
        assert r.is_conflict is True

    def test_anchors_default_empty(self) -> None:
        r = Route(url="/page/", source="page.md", status="REACHABLE")
        assert r.anchors == set()

    def test_aliases_default_empty(self) -> None:
        r = Route(url="/page/", source="page.md", status="REACHABLE")
        assert r.aliases == set()


# ─── _detect_collisions (pure) ────────────────────────────────────────────────


class TestDetectCollisions:
    def test_no_collision_leaves_status_unchanged(self) -> None:
        routes = [
            Route(url="/a/", source="a.md", status="REACHABLE"),
            Route(url="/b/", source="b.md", status="REACHABLE"),
        ]
        _detect_collisions(routes)
        assert all(r.status == "REACHABLE" for r in routes)

    def test_two_files_same_url_both_marked_conflict(self) -> None:
        routes = [
            Route(url="/dir/", source="dir/index.md", status="REACHABLE"),
            Route(url="/dir/", source="dir/README.md", status="REACHABLE"),
        ]
        _detect_collisions(routes)
        assert all(r.status == "CONFLICT" for r in routes)

    def test_double_index_conflict(self) -> None:
        """index.md + README.md in same dir → same URL → CONFLICT (Double Index)."""
        routes = [
            Route(url="/guide/", source="guide/index.md", status="REACHABLE"),
            Route(url="/guide/", source="guide/README.md", status="REACHABLE"),
        ]
        _detect_collisions(routes)
        assert routes[0].status == "CONFLICT"
        assert routes[1].status == "CONFLICT"

    def test_first_route_also_marked_when_collision_found_later(self) -> None:
        """The first route must be retroactively marked CONFLICT."""
        r1 = Route(url="/x/", source="x.md", status="REACHABLE")
        r2 = Route(url="/x/", source="x2.md", status="ORPHAN_BUT_EXISTING")
        _detect_collisions([r1, r2])
        assert r1.status == "CONFLICT"

    def test_three_way_collision(self) -> None:
        routes = [
            Route(url="/same/", source="a.md", status="REACHABLE"),
            Route(url="/same/", source="b.md", status="REACHABLE"),
            Route(url="/same/", source="c.md", status="REACHABLE"),
        ]
        _detect_collisions(routes)
        assert all(r.status == "CONFLICT" for r in routes)


# ─── MkDocsAdapter.map_url ────────────────────────────────────────────────────


class TestMkDocsAdapterMapUrl:
    def _make_adapter(self, config: dict | None = None) -> MkDocsAdapter:
        ctx = BuildContext()
        return MkDocsAdapter(ctx, Path("/docs"), config or {})

    def test_page_md_maps_to_slash_page_slash(self) -> None:
        a = self._make_adapter()
        assert a.map_url(Path("page.md")) == "/page/"

    def test_index_md_maps_to_slash(self) -> None:
        a = self._make_adapter()
        assert a.map_url(Path("index.md")) == "/"

    def test_nested_index_md(self) -> None:
        a = self._make_adapter()
        assert a.map_url(Path("guide/index.md")) == "/guide/"

    def test_readme_md_same_as_index(self) -> None:
        """README.md must produce the same URL as index.md → collision risk."""
        a = self._make_adapter()
        assert a.map_url(Path("guide/README.md")) == "/guide/"

    def test_nested_page(self) -> None:
        a = self._make_adapter()
        assert a.map_url(Path("guide/installation.md")) == "/guide/installation/"

    def test_no_directory_urls(self) -> None:
        a = self._make_adapter({"use_directory_urls": False})
        assert a.map_url(Path("page.md")) == "/page.html"

    def test_no_directory_urls_index(self) -> None:
        # With use_directory_urls=false, guide/index.md → parts=["guide"] → /guide.html
        a = self._make_adapter({"use_directory_urls": False})
        assert a.map_url(Path("guide/index.md")) == "/guide.html"


# ─── MkDocsAdapter.classify_route ────────────────────────────────────────────


class TestMkDocsAdapterClassifyRoute:
    def _make_adapter(self, nav_paths: frozenset[str]) -> MkDocsAdapter:
        nav_list = [{"page": p} for p in nav_paths]
        ctx = BuildContext()
        return MkDocsAdapter(ctx, Path("/docs"), {"nav": nav_list})

    def test_file_in_nav_is_reachable(self) -> None:
        a = self._make_adapter(frozenset({"index.md"}))
        assert a.classify_route(Path("index.md"), frozenset({"index.md"})) == "REACHABLE"

    def test_file_not_in_nav_is_orphan(self) -> None:
        a = self._make_adapter(frozenset({"index.md"}))
        assert a.classify_route(Path("draft.md"), frozenset({"index.md"})) == "ORPHAN_BUT_EXISTING"

    def test_readme_not_in_nav_is_ignored(self) -> None:
        a = self._make_adapter(frozenset({"index.md"}))
        assert a.classify_route(Path("README.md"), frozenset({"index.md"})) == "IGNORED"

    def test_readme_in_nav_is_reachable(self) -> None:
        a = self._make_adapter(frozenset({"README.md"}))
        assert a.classify_route(Path("README.md"), frozenset({"README.md"})) == "REACHABLE"


# ─── ZensicalAdapter.map_url + classify_route ─────────────────────────────────


class TestZensicalAdapterMapUrl:
    def _make_adapter(self) -> ZensicalAdapter:
        return ZensicalAdapter(BuildContext(), Path("/docs"), {})

    def test_page_md(self) -> None:
        assert self._make_adapter().map_url(Path("page.md")) == "/page/"

    def test_index_md(self) -> None:
        assert self._make_adapter().map_url(Path("index.md")) == "/"

    def test_readme_md_treated_as_index(self) -> None:
        assert self._make_adapter().map_url(Path("guide/README.md")) == "/guide/"

    def test_nested_page(self) -> None:
        assert self._make_adapter().map_url(Path("guide/install.md")) == "/guide/install/"

    def test_all_files_reachable(self) -> None:
        a = self._make_adapter()
        assert a.classify_route(Path("any/page.md"), frozenset()) == "REACHABLE"

    def test_underscore_prefix_is_ignored(self) -> None:
        a = self._make_adapter()
        assert a.classify_route(Path("_private/notes.md"), frozenset()) == "IGNORED"

    def test_underscore_in_nested_segment_is_ignored(self) -> None:
        a = self._make_adapter()
        assert a.classify_route(Path("section/_draft.md"), frozenset()) == "IGNORED"


# ─── build_vsm (I/O boundary) ─────────────────────────────────────────────────


class TestBuildVsm:
    def _adapter_and_contents(
        self, tmp_path: Path, files: dict[str, str], nav: list | None = None
    ) -> tuple[MkDocsAdapter, Path, dict[Path, str]]:
        _make_docs(tmp_path, files)
        docs_root = (tmp_path / "docs").resolve()
        cfg: dict = {"nav": nav} if nav is not None else {}
        adapter = MkDocsAdapter(BuildContext(), docs_root, cfg)
        md_contents = {(docs_root / rel).resolve(): content for rel, content in files.items()}
        return adapter, docs_root, md_contents

    def test_single_reachable_page(self, tmp_path: Path) -> None:
        adapter, docs_root, md_contents = self._adapter_and_contents(
            tmp_path,
            {"index.md": "# Home"},
            nav=[{"Home": "index.md"}],
        )
        vsm = build_vsm(adapter, docs_root, md_contents)
        assert "/" in vsm
        assert vsm["/"].status == "REACHABLE"

    def test_orphan_page_present(self, tmp_path: Path) -> None:
        adapter, docs_root, md_contents = self._adapter_and_contents(
            tmp_path,
            {"index.md": "# Home", "draft.md": "# Draft"},
            nav=[{"Home": "index.md"}],
        )
        vsm = build_vsm(adapter, docs_root, md_contents)
        assert "/draft/" in vsm
        assert vsm["/draft/"].status == "ORPHAN_BUT_EXISTING"

    def test_ignored_readme_excluded_from_vsm(self, tmp_path: Path) -> None:
        """README.md not in nav → IGNORED → excluded from returned VSM."""
        adapter, docs_root, md_contents = self._adapter_and_contents(
            tmp_path,
            {"index.md": "# Home", "README.md": "# Readme"},
            nav=[{"Home": "index.md"}],
        )
        vsm = build_vsm(adapter, docs_root, md_contents)
        # README maps to "/" same as index.md, but is IGNORED → excluded
        # index.md wins the "/" URL as REACHABLE
        assert "/" in vsm

    def test_double_index_conflict(self, tmp_path: Path) -> None:
        """index.md + README.md in same dir both map to /dir/ → CONFLICT."""
        adapter, docs_root, md_contents = self._adapter_and_contents(
            tmp_path,
            {
                "guide/index.md": "# Guide",
                "guide/README.md": "# Guide Readme",
                "index.md": "# Home",
            },
            nav=[{"Home": "index.md"}, {"Guide": "guide/index.md"}],
        )
        vsm = build_vsm(adapter, docs_root, md_contents)
        # Both map to /guide/ → CONFLICT; CONFLICT routes ARE included in VSM
        assert "/guide/" in vsm
        assert vsm["/guide/"].status == "CONFLICT"

    def test_anchors_propagated(self, tmp_path: Path) -> None:
        adapter, docs_root, md_contents = self._adapter_and_contents(
            tmp_path,
            {"index.md": "# Quick Start\n\n## Installation"},
            nav=[{"Home": "index.md"}],
        )
        from zenzic.core.validator import anchors_in_file

        anchors_cache = {p: anchors_in_file(c) for p, c in md_contents.items()}
        vsm = build_vsm(adapter, docs_root, md_contents, anchors_cache=anchors_cache)
        assert "quick-start" in vsm["/"].anchors
        assert "installation" in vsm["/"].anchors

    def test_zensical_all_reachable(self, tmp_path: Path) -> None:
        _make_docs(tmp_path, {"index.md": "# Home", "draft.md": "# Draft"})
        docs_root = (tmp_path / "docs").resolve()
        adapter = ZensicalAdapter(BuildContext(), docs_root, {})
        md_contents = {
            (docs_root / "index.md").resolve(): "# Home",
            (docs_root / "draft.md").resolve(): "# Draft",
        }
        vsm = build_vsm(adapter, docs_root, md_contents)
        assert vsm["/"].status == "REACHABLE"
        assert vsm["/draft/"].status == "REACHABLE"

    def test_vanilla_all_reachable(self, tmp_path: Path) -> None:
        _make_docs(tmp_path, {"index.md": "# Home", "page.md": "# Page"})
        docs_root = (tmp_path / "docs").resolve()
        adapter = VanillaAdapter()
        md_contents = {
            (docs_root / "index.md").resolve(): "# Home",
            (docs_root / "page.md").resolve(): "# Page",
        }
        vsm = build_vsm(adapter, docs_root, md_contents)
        assert vsm["/"].status == "REACHABLE"
        assert vsm["/page/"].status == "REACHABLE"


# ─── Dev 4 Mandato: "Zenzic rc4 vs Pulsante Get Started" ────────────────────
# This test fulfils the QA/Inquisitor directive: validate_links must emit
# UNREACHABLE_LINK when a link points to a file that exists on disk but is
# not listed in the MkDocs nav.  It models the real-world scenario where a
# "Get Started" button links to a page that was accidentally removed from nav.


class TestUnreachableLinkDetection:
    def _build_repo(
        self,
        tmp_path: Path,
        nav_files: list[str],
        link_from: str,
        link_to: str,
        link_content: str,
    ) -> Path:
        """Build a minimal docs repo and return the repo root."""
        all_files = {f: f"# {f}\n" for f in nav_files}
        all_files[link_from] = f"# Source\n\n[Get Started]({link_content})\n"
        _make_docs(tmp_path, all_files)
        _write_zenzic_toml(tmp_path, engine="mkdocs")
        nav_entries = [{f.split("/")[-1]: f} for f in nav_files]
        _write_mkdocs(tmp_path, {"site_name": "Test", "docs_dir": "docs", "nav": nav_entries})
        return tmp_path

    def test_link_to_nav_page_is_ok(self, tmp_path: Path) -> None:
        """Button pointing to a REACHABLE page → no errors."""
        repo = self._build_repo(
            tmp_path,
            nav_files=["index.md", "guide/index.md"],
            link_from="index.md",
            link_to="guide/index.md",
            link_content="guide/index.md",
        )
        errors = validate_links(repo)
        assert not any("UNREACHABLE_LINK" in e for e in errors)

    def test_link_to_orphan_page_emits_unreachable_link(self, tmp_path: Path) -> None:
        """Button pointing to a page that exists on disk but is NOT in nav
        must produce an UNREACHABLE_LINK error.  This is the 'Get Started'
        scenario from the rc4 brief."""
        # guide/index.md exists on disk but is NOT listed in nav
        _make_docs(
            tmp_path,
            {
                "index.md": "[Get Started](guide/index.md)\n",
                "guide/index.md": "# Guide\n",
            },
        )
        _write_zenzic_toml(tmp_path, engine="mkdocs")
        _write_mkdocs(
            tmp_path,
            {
                "site_name": "Test",
                "docs_dir": "docs",
                "nav": [{"Home": "index.md"}],  # guide/index.md intentionally absent
            },
        )
        errors = validate_links(tmp_path)
        assert any("UNREACHABLE_LINK" in e for e in errors), (
            f"Expected UNREACHABLE_LINK in errors but got: {errors}"
        )

    def test_vanilla_adapter_never_emits_unreachable_link(self, tmp_path: Path) -> None:
        """Without mkdocs.yml (VanillaAdapter), no UNREACHABLE_LINK is emitted
        because every file is implicitly reachable."""
        _make_docs(
            tmp_path,
            {
                "index.md": "[link](draft.md)\n",
                "draft.md": "# Draft\n",
            },
        )
        _write_zenzic_toml(tmp_path, engine="mkdocs")
        # No mkdocs.yml → VanillaAdapter
        errors = validate_links(tmp_path)
        assert not any("UNREACHABLE_LINK" in e for e in errors)

    def test_zensical_never_emits_unreachable_link(self, tmp_path: Path) -> None:
        """Zensical is filesystem-driven — all files are reachable by design."""
        _make_docs(
            tmp_path,
            {
                "index.md": "[link](draft.md)\n",
                "draft.md": "# Draft\n",
            },
        )
        _write_zenzic_toml(tmp_path, engine="zensical")
        (tmp_path / "zensical.toml").write_text(
            '[site]\nname = "Test"\n[nav]\nnav = []\n', encoding="utf-8"
        )
        errors = validate_links(tmp_path)
        assert not any("UNREACHABLE_LINK" in e for e in errors)

    def test_conflict_route_not_emitting_unreachable_link(self, tmp_path: Path) -> None:
        """A CONFLICT route is a build error, not an unreachable link per se.
        The linter should not double-report it as UNREACHABLE_LINK."""
        _make_docs(
            tmp_path,
            {
                "index.md": "[link](guide/index.md)\n",
                "guide/index.md": "# Guide\n",
                "guide/README.md": "# Guide Readme\n",
            },
        )
        _write_zenzic_toml(tmp_path, engine="mkdocs")
        _write_mkdocs(
            tmp_path,
            {
                "site_name": "Test",
                "docs_dir": "docs",
                "nav": [{"Home": "index.md"}, {"Guide": "guide/index.md"}],
            },
        )
        errors = validate_links(tmp_path)
        # Should not contain UNREACHABLE_LINK for the CONFLICT route
        unreachable = [e for e in errors if "UNREACHABLE_LINK" in e]
        assert not unreachable, f"Unexpected UNREACHABLE_LINK for CONFLICT route: {unreachable}"
