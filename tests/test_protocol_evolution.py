# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Protocol compliance audit and Hypothesis stress tests for Metadata-Driven Routing.

This module validates:
1. ``runtime_checkable`` Protocol compliance for all 4 adapters.
2. ``RouteMetadata`` dataclass invariants.
3. ``get_route_info()`` contract: every adapter returns valid metadata.
4. ``build_metadata_cache()`` / ``extract_frontmatter_*()`` correctness.
5. ``safe_read_line()`` Shield middleware integration.
6. Hypothesis stress tests on ``get_route_info()`` with extreme paths.
7. Pickle safety: adapter instances survive pickle round-trip.
"""

from __future__ import annotations

import pickle
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

from zenzic.core.adapters._base import BaseAdapter, RouteMetadata
from zenzic.core.adapters._docusaurus import DocusaurusAdapter
from zenzic.core.adapters._mkdocs import MkDocsAdapter
from zenzic.core.adapters._utils import (
    build_metadata_cache,
    extract_frontmatter_draft,
    extract_frontmatter_slug,
    extract_frontmatter_tags,
    extract_frontmatter_unlisted,
)
from zenzic.core.adapters._vanilla import VanillaAdapter
from zenzic.core.adapters._zensical import ZensicalAdapter
from zenzic.core.shield import ShieldViolation, safe_read_line
from zenzic.models.config import BuildContext


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_context(**overrides: object) -> BuildContext:
    """Create a minimal BuildContext for testing."""
    defaults: dict[str, object] = {
        "engine": "vanilla",
        "default_locale": "en",
        "locales": [],
        "fallback_to_default": True,
    }
    defaults.update(overrides)
    return BuildContext(**defaults)


# ── Strategies ────────────────────────────────────────────────────────────────

# Path segments: ASCII letters, digits, hyphens, underscores.
_path_segment = st.text(
    alphabet=st.sampled_from(list("abcdefghijklmnopqrstuvwxyz0123456789-_")),
    min_size=1,
    max_size=30,
)

# Relative paths: 1-4 segments + .md extension.
_rel_path = st.lists(_path_segment, min_size=1, max_size=4).map(
    lambda parts: Path("/".join(parts) + ".md")
)

# Paths with directory traversal attempts.
_traversal_path = st.sampled_from(
    [
        Path("../../etc/passwd"),
        Path("../../../root/.ssh/id_rsa"),
        Path("../__init__.py"),
        Path("docs/../../../etc/shadow"),
        Path("a/b/c/d/e/f/g/h/i/j/k/l.md"),  # deep nesting
    ]
)

# Long paths (stress test).
_long_path = st.lists(_path_segment, min_size=10, max_size=20).map(
    lambda parts: Path("/".join(parts) + ".md")
)

# Special character paths.
_special_path = st.sampled_from(
    [
        Path("file with spaces.md"),
        Path("über-guide.md"),
        Path("guide_v2.0.md"),
        Path("_private/secret.md"),
        Path("__pycache__/module.md"),
        Path(".hidden/page.md"),
        Path("index.md"),
        Path("README.md"),
    ]
)


# ── Protocol Compliance ──────────────────────────────────────────────────────


class TestProtocolCompliance:
    """Every adapter must satisfy the BaseAdapter protocol (PEP 544)."""

    def test_vanilla_satisfies_protocol(self) -> None:
        assert isinstance(VanillaAdapter(), BaseAdapter)

    def test_mkdocs_satisfies_protocol(self) -> None:
        ctx = _make_context(engine="mkdocs")
        adapter = MkDocsAdapter(ctx, Path("/docs"))
        assert isinstance(adapter, BaseAdapter)

    def test_docusaurus_satisfies_protocol(self) -> None:
        ctx = _make_context(engine="docusaurus")
        adapter = DocusaurusAdapter(ctx, Path("/docs"))
        assert isinstance(adapter, BaseAdapter)

    def test_zensical_satisfies_protocol(self, tmp_path: Path) -> None:
        """ZensicalAdapter requires zensical.toml to construct via from_repo."""
        ctx = _make_context(engine="zensical")
        # Direct construction with empty config.
        adapter = ZensicalAdapter(ctx, tmp_path, {})
        assert isinstance(adapter, BaseAdapter)


# ── RouteMetadata Invariants ─────────────────────────────────────────────────


class TestRouteMetadataInvariants:
    """RouteMetadata dataclass must be well-formed."""

    def test_defaults(self) -> None:
        meta = RouteMetadata(canonical_url="/", status="REACHABLE")
        assert meta.slug is None
        assert meta.route_base_path == "/"
        assert meta.is_proxy is False

    def test_with_slug(self) -> None:
        meta = RouteMetadata(
            canonical_url="/custom/",
            status="REACHABLE",
            slug="/custom",
        )
        assert meta.slug == "/custom"

    def test_proxy_route(self) -> None:
        meta = RouteMetadata(
            canonical_url="/it/",
            status="REACHABLE",
            is_proxy=True,
        )
        assert meta.is_proxy is True

    def test_conflict_status(self) -> None:
        meta = RouteMetadata(canonical_url="/page/", status="CONFLICT")
        assert meta.status == "CONFLICT"


# ── get_route_info Contract ──────────────────────────────────────────────────


class TestGetRouteInfoContract:
    """get_route_info() must return valid RouteMetadata for all adapters."""

    def test_vanilla_returns_reachable(self) -> None:
        adapter = VanillaAdapter()
        meta = adapter.get_route_info(Path("guide.md"))
        assert isinstance(meta, RouteMetadata)
        assert meta.status == "REACHABLE"
        assert meta.canonical_url == "/guide/"

    def test_vanilla_index_collapses(self) -> None:
        adapter = VanillaAdapter()
        meta = adapter.get_route_info(Path("index.md"))
        assert meta.canonical_url == "/"

    def test_mkdocs_returns_metadata(self) -> None:
        ctx = _make_context(engine="mkdocs")
        adapter = MkDocsAdapter(ctx, Path("/docs"))
        meta = adapter.get_route_info(Path("guide/install.md"))
        assert isinstance(meta, RouteMetadata)
        assert meta.canonical_url == "/guide/install/"
        assert meta.status == "REACHABLE"

    def test_docusaurus_returns_metadata(self) -> None:
        ctx = _make_context(engine="docusaurus")
        adapter = DocusaurusAdapter(ctx, Path("/docs"))
        meta = adapter.get_route_info(Path("guide/install.mdx"))
        assert isinstance(meta, RouteMetadata)
        assert meta.canonical_url == "/guide/install/"
        assert meta.status == "REACHABLE"

    def test_docusaurus_with_slug(self) -> None:
        ctx = _make_context(engine="docusaurus")
        adapter = DocusaurusAdapter(ctx, Path("/docs"))
        adapter._slug_map = {"about.mdx": "/about"}
        meta = adapter.get_route_info(Path("about.mdx"))
        assert meta.slug == "/about"

    def test_zensical_returns_metadata(self, tmp_path: Path) -> None:
        ctx = _make_context(engine="zensical")
        adapter = ZensicalAdapter(ctx, tmp_path, {})
        meta = adapter.get_route_info(Path("page.md"))
        assert isinstance(meta, RouteMetadata)
        assert meta.canonical_url == "/page/"
        assert meta.status == "REACHABLE"


# ── Hypothesis: get_route_info stress tests ──────────────────────────────────


class TestGetRouteInfoHypothesis:
    """Stress test get_route_info() with extreme inputs."""

    @given(rel=_rel_path)
    @settings()
    def test_vanilla_never_crashes(self, rel: Path) -> None:
        adapter = VanillaAdapter()
        meta = adapter.get_route_info(rel)
        assert isinstance(meta, RouteMetadata)
        assert meta.status == "REACHABLE"
        assert isinstance(meta.canonical_url, str)

    @given(rel=_rel_path)
    @settings()
    def test_mkdocs_never_crashes(self, rel: Path) -> None:
        ctx = _make_context(engine="mkdocs")
        adapter = MkDocsAdapter(ctx, Path("/docs"))
        meta = adapter.get_route_info(rel)
        assert isinstance(meta, RouteMetadata)
        assert isinstance(meta.canonical_url, str)
        assert meta.status in ("REACHABLE", "ORPHAN_BUT_EXISTING", "IGNORED")

    @given(rel=_rel_path)
    @settings()
    def test_docusaurus_never_crashes(self, rel: Path) -> None:
        ctx = _make_context(engine="docusaurus")
        adapter = DocusaurusAdapter(ctx, Path("/docs"))
        meta = adapter.get_route_info(rel)
        assert isinstance(meta, RouteMetadata)
        assert isinstance(meta.canonical_url, str)
        assert meta.status in ("REACHABLE", "ORPHAN_BUT_EXISTING", "IGNORED")

    @given(rel=_special_path)
    @settings()
    def test_special_paths_never_crash(self, rel: Path) -> None:
        for adapter in [
            VanillaAdapter(),
            MkDocsAdapter(_make_context(engine="mkdocs"), Path("/docs")),
            DocusaurusAdapter(_make_context(engine="docusaurus"), Path("/docs")),
        ]:
            meta = adapter.get_route_info(rel)
            assert isinstance(meta, RouteMetadata)

    @given(rel=_long_path)
    @settings()
    def test_deep_nesting_never_crashes(self, rel: Path) -> None:
        adapter = VanillaAdapter()
        meta = adapter.get_route_info(rel)
        assert isinstance(meta, RouteMetadata)
        assert meta.canonical_url.startswith("/")


# ── Pickle Safety (multiprocessing) ──────────────────────────────────────────


class TestPickleSafety:
    """Adapters must survive pickle round-trip for parallel processing."""

    def test_vanilla_pickle(self) -> None:
        adapter = VanillaAdapter()
        restored = pickle.loads(pickle.dumps(adapter))
        meta = restored.get_route_info(Path("test.md"))
        assert meta.canonical_url == "/test/"

    def test_mkdocs_pickle(self) -> None:
        ctx = _make_context(engine="mkdocs")
        adapter = MkDocsAdapter(ctx, Path("/docs"), {}, config_file_found=False)
        restored = pickle.loads(pickle.dumps(adapter))
        meta = restored.get_route_info(Path("test.md"))
        assert meta.canonical_url == "/test/"

    def test_docusaurus_pickle(self) -> None:
        ctx = _make_context(engine="docusaurus")
        adapter = DocusaurusAdapter(ctx, Path("/docs"))
        adapter._slug_map = {"about.mdx": "/about"}
        restored = pickle.loads(pickle.dumps(adapter))
        assert restored._slug_map == {"about.mdx": "/about"}
        meta = restored.get_route_info(Path("about.mdx"))
        assert meta.slug == "/about"


# ── Centralized Frontmatter Extraction ───────────────────────────────────────


class TestFrontmatterExtraction:
    """Engine-agnostic frontmatter extraction utilities."""

    def test_slug_basic(self) -> None:
        content = "---\ntitle: Test\nslug: /custom\n---\n\nBody"
        assert extract_frontmatter_slug(content) == "/custom"

    def test_slug_relative(self) -> None:
        content = "---\nslug: custom-name\n---\n\nBody"
        assert extract_frontmatter_slug(content) == "custom-name"

    def test_slug_missing(self) -> None:
        content = "---\ntitle: Test\n---\n\nBody"
        assert extract_frontmatter_slug(content) is None

    def test_slug_no_frontmatter(self) -> None:
        content = "Just plain text\n"
        assert extract_frontmatter_slug(content) is None

    def test_draft_true(self) -> None:
        content = "---\ndraft: true\n---\n\nBody"
        assert extract_frontmatter_draft(content) is True

    def test_draft_false(self) -> None:
        content = "---\ndraft: false\n---\n\nBody"
        assert extract_frontmatter_draft(content) is False

    def test_draft_missing(self) -> None:
        content = "---\ntitle: Test\n---\n\nBody"
        assert extract_frontmatter_draft(content) is False

    def test_unlisted_true(self) -> None:
        content = "---\nunlisted: true\n---\n\nBody"
        assert extract_frontmatter_unlisted(content) is True

    def test_unlisted_false(self) -> None:
        content = "---\nunlisted: false\n---\n\nBody"
        assert extract_frontmatter_unlisted(content) is False

    def test_tags_inline(self) -> None:
        content = "---\ntags: [python, docs, linter]\n---\n\nBody"
        assert extract_frontmatter_tags(content) == ["python", "docs", "linter"]

    def test_tags_flow(self) -> None:
        content = "---\ntags:\n- python\n- docs\n---\n\nBody"
        assert extract_frontmatter_tags(content) == ["python", "docs"]

    def test_tags_empty(self) -> None:
        content = "---\ntitle: Test\n---\n\nBody"
        assert extract_frontmatter_tags(content) == []


class TestBuildMetadataCache:
    """build_metadata_cache() must produce correct FileMetadata."""

    def test_single_file_with_slug(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        content = "---\nslug: /custom\ndraft: true\ntags: [a, b]\n---\n\nBody"
        md_contents = {docs / "page.md": content}
        cache = build_metadata_cache(md_contents, docs, shield_enabled=False)
        assert "page.md" in cache
        meta = cache["page.md"]
        assert meta.slug == "/custom"
        assert meta.draft is True
        assert meta.tags == ["a", "b"]

    def test_shield_catches_secret_in_frontmatter(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        # Embed a fake OpenAI key in frontmatter.
        fake_key = "sk-" + "a" * 48
        content = f"---\ntitle: Test\napi_key: {fake_key}\n---\n\nBody"
        md_contents = {docs / "page.md": content}
        with pytest.raises(ShieldViolation) as exc_info:
            build_metadata_cache(md_contents, docs, shield_enabled=True)
        assert exc_info.value.finding.secret_type == "openai-api-key"

    def test_shield_disabled_allows_secret(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        fake_key = "sk-" + "a" * 48
        content = f"---\ntitle: Test\napi_key: {fake_key}\n---\n\nBody"
        md_contents = {docs / "page.md": content}
        # Should NOT raise when Shield is disabled.
        cache = build_metadata_cache(md_contents, docs, shield_enabled=False)
        assert "page.md" in cache


# ── Shield Middleware ────────────────────────────────────────────────────────


class TestShieldMiddleware:
    """safe_read_line() must raise ShieldViolation on secrets."""

    def test_clean_line_passes_through(self) -> None:
        result = safe_read_line("slug: /custom-path", Path("test.md"), 1)
        assert result == "slug: /custom-path"

    def test_secret_raises_violation(self) -> None:
        fake_key = "sk-" + "a" * 48
        with pytest.raises(ShieldViolation) as exc_info:
            safe_read_line(f"key: {fake_key}", Path("test.md"), 5)
        assert exc_info.value.finding.secret_type == "openai-api-key"
        assert exc_info.value.finding.line_no == 5

    def test_github_token_raises(self) -> None:
        fake_token = "ghp_" + "a" * 36
        with pytest.raises(ShieldViolation):
            safe_read_line(f"token: {fake_token}", Path("test.md"), 1)

    def test_normal_frontmatter_safe(self) -> None:
        lines = [
            "title: My Page",
            "slug: /about",
            "draft: false",
            "tags: [python, docs]",
        ]
        for i, line in enumerate(lines):
            result = safe_read_line(line, Path("test.md"), i + 1)
            assert result == line


# ── Vanilla Adapter — No Spurious Warnings ───────────────────────────────────


class TestVanillaNoSpuriousWarnings:
    """VanillaAdapter must not emit warnings on pure Markdown repos."""

    def test_no_warnings_on_classify(self, capsys: pytest.CaptureFixture[str]) -> None:
        adapter = VanillaAdapter()
        adapter.classify_route(Path("page.md"), frozenset())
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_no_warnings_on_get_route_info(self, capsys: pytest.CaptureFixture[str]) -> None:
        adapter = VanillaAdapter()
        adapter.get_route_info(Path("page.md"))
        captured = capsys.readouterr()
        assert captured.err == ""
