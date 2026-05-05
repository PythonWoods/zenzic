# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""EPOCH 7b — Virtual Route infrastructure and Docusaurus Tag Generator tests.

Test numbering follows the EPOCH 7b specification:

Test 5 — Reverse-Mapping Invariant:
    ``VirtualRoute`` raises ``ValueError`` when ``source_files`` is empty;
    construction succeeds when ``source_files`` is non-empty.

Test 2 — ``_slugify_tag()`` pure unit:
    Tag strings are slugified to Docusaurus-compatible URL segments.

Test 1 — Docusaurus Tag Generator happy path:
    Tagged blog posts produce ``kind="tag"`` routes plus a ``kind="tag_index"``
    route at ``/{blog_rbp}/tags/``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from zenzic.core.adapters._base import VirtualRoute
from zenzic.core.adapters._docusaurus import DocusaurusAdapter, _slugify_tag
from zenzic.models.config import BuildContext


# ── Sandbox builder ───────────────────────────────────────────────────────────


def _build_sandbox(repo: Path) -> tuple[Path, Path]:
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
    (docs / "intro.md").write_text("# Intro\n\nWelcome.\n", encoding="utf-8")

    return docs, repo


# ── Test 5 — Reverse-Mapping Invariant ───────────────────────────────────────


class TestReverseMappingInvariant:
    """VirtualRoute enforces the Reverse-Mapping Invariant at construction time."""

    def test_empty_source_files_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Reverse-Mapping Invariant"):
            VirtualRoute(
                url="/blog/tags/python/",
                label="tag:python",
                source_files=frozenset(),
                kind="tag",
            )

    def test_non_empty_source_files_ok(self) -> None:
        vr = VirtualRoute(
            url="/blog/tags/python/",
            label="tag:python",
            source_files=frozenset({"blog/post.md"}),
            kind="tag",
        )
        assert vr.url == "/blog/tags/python/"
        assert vr.kind == "tag"
        assert vr.source_files == frozenset({"blog/post.md"})

    def test_tag_index_kind_ok(self) -> None:
        vr = VirtualRoute(
            url="/blog/tags/",
            label="tag_index",
            source_files=frozenset({"blog/post.md"}),
            kind="tag_index",
        )
        assert vr.kind == "tag_index"

    def test_virtual_route_is_frozen(self) -> None:
        vr = VirtualRoute(
            url="/blog/tags/python/",
            label="tag:python",
            source_files=frozenset({"blog/post.md"}),
            kind="tag",
        )
        with pytest.raises((AttributeError, TypeError)):
            vr.url = "/other/"  # type: ignore[misc]


# ── Test 2 — _slugify_tag() pure unit ────────────────────────────────────────


class TestSlugifyTag:
    """Pure unit tests for the ``_slugify_tag()`` module-level helper."""

    def test_special_chars_stripped(self) -> None:
        assert _slugify_tag("C++") == "c"

    def test_unicode_decomposed(self) -> None:
        assert _slugify_tag("Integrità") == "integrita"

    def test_space_to_hyphen(self) -> None:
        assert _slugify_tag("Python 3.10") == "python-310"

    def test_pure_cjk_returns_untagged(self) -> None:
        assert _slugify_tag("データ") == "untagged"

    def test_empty_string_returns_untagged(self) -> None:
        assert _slugify_tag("") == "untagged"

    def test_hyphenated_tag_preserved(self) -> None:
        result = _slugify_tag("machine-learning")
        assert result == "machine-learning"

    def test_leading_trailing_hyphens_stripped(self) -> None:
        result = _slugify_tag("  python  ")
        assert result == "python"


# ── Test 1 — Docusaurus Tag Generator happy path ──────────────────────────────


class TestDocusaurusTagGenerator:
    """DocusaurusAdapter.get_virtual_routes() produces tag + tag_index routes."""

    def test_tagged_post_produces_tag_and_tag_index_routes(
        self, tmp_path: Path
    ) -> None:
        docs, repo = _build_sandbox(tmp_path)
        post = repo / "blog" / "2026-04-12-post.md"
        post.write_text("---\ntags: [python, tutorial]\n---\n# Post\n", encoding="utf-8")

        adapter = DocusaurusAdapter.from_repo(
            BuildContext(engine="docusaurus"), docs, repo
        )
        md = {post.resolve(): post.read_text(encoding="utf-8")}
        vrs = adapter.get_virtual_routes(md)
        by_url = {vr.url: vr for vr in vrs}

        # tag routes
        assert "/blog/tags/python/" in by_url
        assert "/blog/tags/tutorial/" in by_url
        assert by_url["/blog/tags/python/"].kind == "tag"
        assert by_url["/blog/tags/tutorial/"].kind == "tag"
        assert by_url["/blog/tags/python/"].source_files == frozenset(
            {"blog/2026-04-12-post.md"}
        )
        assert by_url["/blog/tags/tutorial/"].source_files == frozenset(
            {"blog/2026-04-12-post.md"}
        )

        # tag_index route
        assert "/blog/tags/" in by_url
        assert by_url["/blog/tags/"].kind == "tag_index"
        assert "blog/2026-04-12-post.md" in by_url["/blog/tags/"].source_files

    def test_untagged_post_produces_no_routes(self, tmp_path: Path) -> None:
        docs, repo = _build_sandbox(tmp_path)
        post = repo / "blog" / "2026-04-12-no-tags.md"
        post.write_text("# Post without tags\n\nNo frontmatter.\n", encoding="utf-8")

        adapter = DocusaurusAdapter.from_repo(
            BuildContext(engine="docusaurus"), docs, repo
        )
        md = {post.resolve(): post.read_text(encoding="utf-8")}
        vrs = adapter.get_virtual_routes(md)

        assert vrs == []

    def test_blog_disabled_returns_empty_list(self, tmp_path: Path) -> None:
        # Adapter without blog discovery (no blog/ dir)
        docs = tmp_path / "docs"
        docs.mkdir()
        (tmp_path / "docusaurus.config.ts").write_text(
            "export default { baseUrl: '/', title: 't' };\n",
            encoding="utf-8",
        )
        (docs / "intro.md").write_text("# Intro\n", encoding="utf-8")

        adapter = DocusaurusAdapter.from_repo(
            BuildContext(engine="docusaurus"), docs, tmp_path
        )
        md: dict[Path, str] = {}
        assert adapter.get_virtual_routes(md) == []

    def test_multiple_posts_same_tag_union_sources(self, tmp_path: Path) -> None:
        docs, repo = _build_sandbox(tmp_path)
        post_a = repo / "blog" / "2026-04-12-post-a.md"
        post_b = repo / "blog" / "2026-04-13-post-b.md"
        post_a.write_text("---\ntags: [python]\n---\n# A\n", encoding="utf-8")
        post_b.write_text("---\ntags: [python]\n---\n# B\n", encoding="utf-8")

        adapter = DocusaurusAdapter.from_repo(
            BuildContext(engine="docusaurus"), docs, repo
        )
        md = {
            post_a.resolve(): post_a.read_text(encoding="utf-8"),
            post_b.resolve(): post_b.read_text(encoding="utf-8"),
        }
        vrs = adapter.get_virtual_routes(md)
        by_url = {vr.url: vr for vr in vrs}

        python_route = by_url["/blog/tags/python/"]
        assert python_route.source_files == frozenset(
            {"blog/2026-04-12-post-a.md", "blog/2026-04-13-post-b.md"}
        )

        tag_index = by_url["/blog/tags/"]
        assert "blog/2026-04-12-post-a.md" in tag_index.source_files
        assert "blog/2026-04-13-post-b.md" in tag_index.source_files
