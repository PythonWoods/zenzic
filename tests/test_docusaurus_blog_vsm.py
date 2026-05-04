# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""EPOCH 7a regression — Docusaurus blog/ files must enter the VSM and link checks.

Pre-fix bug: the VSM only ingested files under ``docs_dir``, so Docusaurus
blog posts were invisible to ``zenzic check`` and broken links inside the
``blog/`` tree slipped past validation while ``docusaurus build`` flagged them.

This suite locks in the four invariants of the fix:

1. ``DocusaurusAdapter.get_extra_content_roots()`` advertises ``blog/`` when
   the directory exists (convention auto-detection).
2. ``build_vsm()`` ingests blog files and assigns them ``REACHABLE`` URLs
   under the configured ``routeBasePath``.
3. The validator (``validate_links_async``) catches a broken link that lives
   inside a blog post — the original bug-of-record.
4. The validator catches a broken link from a ``docs/`` page that targets a
   non-existent blog post (cross-tree resolution).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from zenzic.core.adapters._base import ContentRoot
from zenzic.core.adapters._docusaurus import DocusaurusAdapter
from zenzic.core.exclusion import LayeredExclusionManager
from zenzic.core.validator import validate_links_async
from zenzic.models.config import BuildContext, ZenzicConfig
from zenzic.models.vsm import build_vsm


# ── Sandbox builder ───────────────────────────────────────────────────────────


def _build_sandbox(repo: Path, *, with_broken_links: bool = False) -> tuple[Path, Path]:
    """Materialise a minimal Docusaurus repo with docs/ and blog/.

    Returns ``(docs_root, repo_root)``.
    """
    docs = repo / "docs"
    blog = repo / "blog"
    docs.mkdir()
    blog.mkdir()

    (repo / "docusaurus.config.ts").write_text(
        "export default { baseUrl: '/', title: 't' };\n",
        encoding="utf-8",
    )
    (docs / "intro.md").write_text(
        "# Intro\n\nSee [welcome](../blog/2026-04-12-welcome.md).\n", encoding="utf-8"
    )
    (blog / "2026-04-12-welcome.md").write_text(
        "# Welcome\n\nA standalone blog post.\n",
        encoding="utf-8",
    )

    if with_broken_links:
        # Broken link inside the blog — the canonical bug-of-record.
        (blog / "2026-04-13-broken.md").write_text(
            "# Broken\n\nSee [missing](./does-not-exist.md).\n",
            encoding="utf-8",
        )
        # Broken cross-tree link from docs/ to a non-existent blog post.
        (docs / "stale.md").write_text(
            "# Stale\n\n[Old post](../blog/2030-01-01-ghost.md).\n",
            encoding="utf-8",
        )

    return docs, repo


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestEpoch7aBlogDiscovery:
    """get_extra_content_roots returns blog/ via convention auto-detection."""

    def test_blog_directory_advertised_as_content_root(self, tmp_path: Path) -> None:
        docs, repo = _build_sandbox(tmp_path)
        adapter = DocusaurusAdapter.from_repo(BuildContext(engine="docusaurus"), docs, repo)
        roots = adapter.get_extra_content_roots(repo)
        assert len(roots) == 1
        root = roots[0]
        assert isinstance(root, ContentRoot)
        assert root.path == (repo / "blog").resolve()
        assert root.url_prefix == "blog"

    def test_no_blog_directory_yields_empty_list(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (tmp_path / "docusaurus.config.ts").write_text(
            "export default { baseUrl: '/' };\n", encoding="utf-8"
        )
        adapter = DocusaurusAdapter.from_repo(BuildContext(engine="docusaurus"), docs, tmp_path)
        assert adapter.get_extra_content_roots(tmp_path) == []


class TestEpoch7aVsmIngestion:
    """build_vsm() walks extra content roots and routes blog files correctly."""

    def test_blog_file_appears_as_reachable_route(self, tmp_path: Path) -> None:
        docs, repo = _build_sandbox(tmp_path)
        adapter = DocusaurusAdapter.from_repo(BuildContext(engine="docusaurus"), docs, repo)
        blog_file = (repo / "blog" / "2026-04-12-welcome.md").resolve()
        intro = (docs / "intro.md").resolve()
        md_contents = {
            intro: intro.read_text(encoding="utf-8"),
            blog_file: blog_file.read_text(encoding="utf-8"),
        }
        vsm = build_vsm(
            adapter,
            docs.resolve(),
            md_contents,
            extra_content_roots=[((repo / "blog").resolve(), "blog")],
        )
        # Date prefix is stripped; URL lives under /blog/.
        assert "/blog/welcome/" in vsm
        assert vsm["/blog/welcome/"].status == "REACHABLE"
        # docs/intro.md is still routed normally (default routeBasePath = 'docs').
        assert "/docs/intro/" in vsm


class TestEpoch7aReverseMapping:
    """Traceability invariant: every VSM route resolves back to a real source file.

    Locks the contract that EPOCH 7b virtual routes (tags, pagination,
    authors) must also satisfy — a route without a physical origin is a
    validator screaming ``error`` without ever saying ``where``.
    """

    def test_every_blog_route_traces_back_to_a_real_file(self, tmp_path: Path) -> None:
        docs, repo = _build_sandbox(tmp_path)
        # Add a second blog post so the assertion is non-trivially plural.
        (repo / "blog" / "2026-05-01-second.md").write_text(
            "# Second\n\nAnother standalone post.\n", encoding="utf-8"
        )
        adapter = DocusaurusAdapter.from_repo(BuildContext(engine="docusaurus"), docs, repo)
        md_contents = {
            p.resolve(): p.read_text(encoding="utf-8")
            for p in [
                docs / "intro.md",
                repo / "blog" / "2026-04-12-welcome.md",
                repo / "blog" / "2026-05-01-second.md",
            ]
        }
        vsm = build_vsm(
            adapter,
            docs.resolve(),
            md_contents,
            extra_content_roots=[((repo / "blog").resolve(), "blog")],
        )
        blog_routes = [r for r in vsm.values() if r.url.startswith("/blog/")]
        assert len(blog_routes) >= 2, f"expected ≥2 blog routes, got {blog_routes}"
        for route in blog_routes:
            # ``source`` carries the prefix-injected logical rel — strip the
            # 'blog/' prefix to land back on the physical file under repo/blog.
            assert route.source.startswith("blog/"), (
                f"blog route source must carry 'blog/' prefix, got {route.source!r}"
            )
            physical = repo / route.source
            assert physical.is_file(), (
                f"route {route.url!r} traces to {physical} which does not exist"
            )


class TestEpoch7aValidatorClosesTheGap:
    """validate_links_async catches broken links inside and across blog/."""

    def _run(self, repo: Path, docs: Path) -> list[str]:
        config = ZenzicConfig(build_context=BuildContext(engine="docusaurus"))
        em = LayeredExclusionManager(repo_root=repo, config=config)
        result = asyncio.run(
            validate_links_async(
                docs.resolve(),
                em,
                repo_root=repo.resolve(),
                config=config,
                strict=False,
                structured=False,
                check_external=False,
            )
        )
        assert isinstance(result, list)
        return [str(e) for e in result]

    def test_broken_link_inside_blog_is_detected(self, tmp_path: Path) -> None:
        docs, repo = _build_sandbox(tmp_path, with_broken_links=True)
        errors = self._run(repo, docs)
        # The blog-internal broken link is the canonical bug-of-record.
        assert any("does-not-exist.md" in e and "broken" in e.lower() for e in errors), (
            f"expected broken-link inside blog/, got: {errors}"
        )

    def test_broken_cross_tree_link_to_blog_is_detected(self, tmp_path: Path) -> None:
        docs, repo = _build_sandbox(tmp_path, with_broken_links=True)
        errors = self._run(repo, docs)
        # docs/stale.md → /blog/2030-01-01-ghost (no such post)
        assert any("2030-01-01-ghost" in e or "ghost" in e for e in errors), (
            f"expected broken cross-tree link, got: {errors}"
        )

    def test_clean_repo_has_no_blog_errors(self, tmp_path: Path) -> None:
        docs, repo = _build_sandbox(tmp_path, with_broken_links=False)
        errors = self._run(repo, docs)
        # The seed repo's links must all resolve once blog/ is in scope.
        blog_errors = [e for e in errors if "blog" in e.lower()]
        assert blog_errors == [], (
            f"blog files should not produce errors in a clean repo, got: {blog_errors}"
        )
