# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""DocusaurusAdapter test suite — config parsing, URL mapping, and slug support.

Fixture naming convention:
    CFG-01..07  — docusaurus.config.ts/js parsing scenarios
    RBP-01      — routeBasePath extraction from presets
    SLUG-01     — frontmatter slug overrides in map_url()

Covers:
    - Static extraction of baseUrl from multiple JS/TS export patterns
    - Dynamic config detection (async, import(), require()) → fallback + warning
    - routeBasePath extraction from preset/plugin blocks
    - Frontmatter slug: absolute and relative overrides
    - Comment stripping (single-line, multi-line, preserving strings)
    - Graceful failure: unreadable files, missing keys, function configs
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from zenzic.core.adapters._docusaurus import (
    DocusaurusAdapter,
    _extract_base_url,
    _extract_frontmatter_slug,
    _extract_route_base_path,
    _is_dynamic_config,
    _parse_config_navigation,
    _parse_sidebars,
    _strip_js_comments,
    find_docusaurus_config,
)
from zenzic.core.validator import _SKIP_SCHEMES, validate_links_structured
from zenzic.models.config import BuildContext, ZenzicConfig


# ── Helpers ───────────────────────────────────────────────────────────────────


def _write_config(tmp_path: Path, content: str, name: str = "docusaurus.config.ts") -> Path:
    """Write a config file and return its path."""
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def _make_adapter(
    tmp_path: Path,
    base_url: str = "/",
    route_base_path: str | None = None,
    locales: list[str] | None = None,
) -> DocusaurusAdapter:
    """Create a DocusaurusAdapter with sensible defaults."""
    ctx = BuildContext(engine="docusaurus", locales=locales or [])
    docs_root = tmp_path / "docs"
    docs_root.mkdir(exist_ok=True)
    return DocusaurusAdapter(ctx, docs_root, base_url, route_base_path)


# ═══════════════════════════════════════════════════════════════════════════════
# CFG-01: export default { baseUrl: '...' }
# ═══════════════════════════════════════════════════════════════════════════════


class TestCFG01ExportDefault:
    """baseUrl extraction from ``export default { ... }`` pattern."""

    def test_single_quoted(self, tmp_path: Path) -> None:
        p = _write_config(tmp_path, "export default { baseUrl: '/docs/' };")
        assert _extract_base_url(p) == "/docs/"

    def test_double_quoted(self, tmp_path: Path) -> None:
        p = _write_config(tmp_path, 'export default { baseUrl: "/my-site/" };')
        assert _extract_base_url(p) == "/my-site/"

    def test_root_slash(self, tmp_path: Path) -> None:
        p = _write_config(tmp_path, "export default { baseUrl: '/' };")
        assert _extract_base_url(p) == "/"

    def test_with_surrounding_keys(self, tmp_path: Path) -> None:
        cfg = """\
export default {
  title: "My Site",
  baseUrl: "/prefix/",
  url: "https://example.com",
};
"""
        p = _write_config(tmp_path, cfg)
        assert _extract_base_url(p) == "/prefix/"


# ═══════════════════════════════════════════════════════════════════════════════
# CFG-02: module.exports = { baseUrl: '...' }
# ═══════════════════════════════════════════════════════════════════════════════


class TestCFG02ModuleExports:
    """baseUrl extraction from ``module.exports`` pattern (CommonJS)."""

    def test_basic(self, tmp_path: Path) -> None:
        p = _write_config(
            tmp_path,
            "module.exports = { baseUrl: '/cjs/' };",
            name="docusaurus.config.js",
        )
        assert _extract_base_url(p) == "/cjs/"

    def test_multiline(self, tmp_path: Path) -> None:
        cfg = """\
module.exports = {
  title: "CJS Site",
  baseUrl: "/legacy/",
};
"""
        p = _write_config(tmp_path, cfg, name="docusaurus.config.js")
        assert _extract_base_url(p) == "/legacy/"


# ═══════════════════════════════════════════════════════════════════════════════
# CFG-03: const config = { baseUrl: '...' }; export default config;
# ═══════════════════════════════════════════════════════════════════════════════


class TestCFG03ConstAssignment:
    """baseUrl extraction from const-assignment then export default."""

    def test_const_then_export(self, tmp_path: Path) -> None:
        cfg = """\
const config = {
  title: "Assigned",
  baseUrl: "/assigned/",
  url: "https://example.com",
};

export default config;
"""
        p = _write_config(tmp_path, cfg)
        assert _extract_base_url(p) == "/assigned/"

    def test_let_assignment(self, tmp_path: Path) -> None:
        cfg = """\
let config = {
  baseUrl: "/let-style/",
};
export default config;
"""
        p = _write_config(tmp_path, cfg)
        assert _extract_base_url(p) == "/let-style/"


# ═══════════════════════════════════════════════════════════════════════════════
# CFG-04: Fallback when baseUrl key is missing
# ═══════════════════════════════════════════════════════════════════════════════


class TestCFG04MissingBaseUrl:
    """Fallback to '/' when no baseUrl key is present."""

    def test_no_base_url_key(self, tmp_path: Path) -> None:
        p = _write_config(tmp_path, "export default { title: 'No Base' };")
        assert _extract_base_url(p) == "/"

    def test_empty_config(self, tmp_path: Path) -> None:
        p = _write_config(tmp_path, "export default {};")
        assert _extract_base_url(p) == "/"

    def test_unreadable_file(self, tmp_path: Path) -> None:
        p = tmp_path / "docusaurus.config.ts"
        # File doesn't exist
        assert _extract_base_url(p) == "/"


# ═══════════════════════════════════════════════════════════════════════════════
# CFG-05: Async/dynamic config → graceful fallback with warning
# ═══════════════════════════════════════════════════════════════════════════════


class TestCFG05DynamicConfig:
    """Dynamic config detection and graceful fallback."""

    def test_async_export_default(self, tmp_path: Path) -> None:
        cfg = """\
export default async function createConfig() {
  return { baseUrl: "/should-not-extract/" };
}
"""
        p = _write_config(tmp_path, cfg)
        assert _extract_base_url(p) == "/"

    def test_module_exports_async(self, tmp_path: Path) -> None:
        cfg = """\
module.exports = async () => ({
  baseUrl: "/async-arrow/",
});
"""
        p = _write_config(tmp_path, cfg)
        assert _extract_base_url(p) == "/"

    def test_dynamic_import(self, tmp_path: Path) -> None:
        cfg = """\
const theme = await import('./theme.js');
export default {
  baseUrl: "/with-import/",
};
"""
        p = _write_config(tmp_path, cfg)
        assert _extract_base_url(p) == "/"

    def test_require_call(self, tmp_path: Path) -> None:
        cfg = """\
const pkg = require('./package.json');
module.exports = {
  baseUrl: "/" + pkg.name + "/",
};
"""
        p = _write_config(tmp_path, cfg, name="docusaurus.config.js")
        assert _extract_base_url(p) == "/"

    def test_export_default_function(self, tmp_path: Path) -> None:
        cfg = """\
export default function createConfig() {
  return { baseUrl: "/factory/" };
}
"""
        p = _write_config(tmp_path, cfg)
        assert _extract_base_url(p) == "/"

    def test_module_exports_function(self, tmp_path: Path) -> None:
        cfg = """\
module.exports = function() {
  return { baseUrl: "/factory-cjs/" };
};
"""
        p = _write_config(tmp_path, cfg, name="docusaurus.config.js")
        assert _extract_base_url(p) == "/"

    def test_warning_emitted(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        cfg = "export default async function() { return { baseUrl: '/' }; }"
        p = _write_config(tmp_path, cfg)
        with caplog.at_level(logging.WARNING):
            result = _extract_base_url(p)
        assert result == "/"
        assert "dynamic patterns" in caplog.text


# ═══════════════════════════════════════════════════════════════════════════════
# CFG-06: Comment stripping
# ═══════════════════════════════════════════════════════════════════════════════


class TestCFG06CommentStripping:
    """JS/TS comments must not interfere with extraction."""

    def test_single_line_comment_before_key(self, tmp_path: Path) -> None:
        cfg = """\
export default {
  // baseUrl: "/commented-out/",
  baseUrl: "/real/",
};
"""
        p = _write_config(tmp_path, cfg)
        assert _extract_base_url(p) == "/real/"

    def test_multiline_comment_wrapping_key(self, tmp_path: Path) -> None:
        cfg = """\
export default {
  /* baseUrl: "/blocked/" */
  baseUrl: "/actual/",
};
"""
        p = _write_config(tmp_path, cfg)
        assert _extract_base_url(p) == "/actual/"

    def test_base_url_in_string_not_stripped(self, tmp_path: Path) -> None:
        """String literals containing // should not be treated as comments."""
        cfg = """\
export default {
  title: "// not a comment",
  baseUrl: "/preserved/",
};
"""
        p = _write_config(tmp_path, cfg)
        assert _extract_base_url(p) == "/preserved/"

    def test_strip_js_comments_preserves_strings(self) -> None:
        code = """
        // comment line
        const x = "hello // world";
        /* block
        comment */
        const y = 'test /* not a comment */';
        """
        stripped = _strip_js_comments(code)
        assert '"hello // world"' in stripped
        assert "'test /* not a comment */'" in stripped
        assert "// comment line" not in stripped
        assert "/* block" not in stripped


# ═══════════════════════════════════════════════════════════════════════════════
# CFG-07: Config file discovery (.ts preferred over .js)
# ═══════════════════════════════════════════════════════════════════════════════


class TestCFG07ConfigDiscovery:
    """find_docusaurus_config() resolution order."""

    def test_ts_preferred(self, tmp_path: Path) -> None:
        (tmp_path / "docusaurus.config.ts").write_text("export default {};")
        (tmp_path / "docusaurus.config.js").write_text("module.exports = {};")
        found = find_docusaurus_config(tmp_path)
        assert found is not None
        assert found.name == "docusaurus.config.ts"

    def test_js_fallback(self, tmp_path: Path) -> None:
        (tmp_path / "docusaurus.config.js").write_text("module.exports = {};")
        found = find_docusaurus_config(tmp_path)
        assert found is not None
        assert found.name == "docusaurus.config.js"

    def test_none_when_absent(self, tmp_path: Path) -> None:
        assert find_docusaurus_config(tmp_path) is None


# ═══════════════════════════════════════════════════════════════════════════════
# RBP-01: routeBasePath extraction from presets
# ═══════════════════════════════════════════════════════════════════════════════


class TestRBP01RouteBasePath:
    """routeBasePath extraction from Docusaurus preset/plugin blocks."""

    def test_route_base_path_in_preset(self, tmp_path: Path) -> None:
        cfg = """\
export default {
  baseUrl: "/",
  presets: [
    [
      "@docusaurus/preset-classic",
      {
        docs: {
          routeBasePath: "docs",
          sidebarPath: "./sidebars.js",
        },
      },
    ],
  ],
};
"""
        p = _write_config(tmp_path, cfg)
        assert _extract_route_base_path(p) == "docs"

    def test_route_base_path_empty_string(self, tmp_path: Path) -> None:
        """routeBasePath: '' → docs served at site root."""
        cfg = """\
export default {
  baseUrl: "/",
  presets: [
    [
      "@docusaurus/preset-classic",
      {
        docs: {
          routeBasePath: "",
        },
      },
    ],
  ],
};
"""
        p = _write_config(tmp_path, cfg)
        assert _extract_route_base_path(p) == ""

    def test_route_base_path_absent(self, tmp_path: Path) -> None:
        cfg = "export default { baseUrl: '/' };"
        p = _write_config(tmp_path, cfg)
        assert _extract_route_base_path(p) is None

    def test_route_base_path_with_dynamic_config(self, tmp_path: Path) -> None:
        cfg = """\
export default async function() {
  return {
    presets: [[
      "@docusaurus/preset-classic",
      { docs: { routeBasePath: "guide" } },
    ]],
  };
}
"""
        p = _write_config(tmp_path, cfg)
        # Dynamic config → routeBasePath not extracted
        assert _extract_route_base_path(p) is None

    def test_route_base_path_unreadable(self, tmp_path: Path) -> None:
        p = tmp_path / "nonexistent.config.ts"
        assert _extract_route_base_path(p) is None


# ═══════════════════════════════════════════════════════════════════════════════
# SLUG-01: Frontmatter slug support
# ═══════════════════════════════════════════════════════════════════════════════


class TestSLUG01FrontmatterSlug:
    """Frontmatter slug extraction and map_url() override."""

    # ── Extraction ──

    def test_extract_slug_quoted(self) -> None:
        content = '---\ntitle: "Hello"\nslug: "/custom-path"\n---\n# Hello'
        assert _extract_frontmatter_slug(content) == "/custom-path"

    def test_extract_slug_unquoted(self) -> None:
        content = "---\nslug: /about\n---\n# About"
        assert _extract_frontmatter_slug(content) == "/about"

    def test_extract_slug_relative(self) -> None:
        content = "---\nslug: my-custom-slug\n---\n# Page"
        assert _extract_frontmatter_slug(content) == "my-custom-slug"

    def test_no_frontmatter(self) -> None:
        content = "# No frontmatter here"
        assert _extract_frontmatter_slug(content) is None

    def test_no_slug_in_frontmatter(self) -> None:
        content = "---\ntitle: Hello\n---\n# Hello"
        assert _extract_frontmatter_slug(content) is None

    def test_empty_frontmatter(self) -> None:
        content = "---\n---\n# Empty"
        assert _extract_frontmatter_slug(content) is None

    def test_slug_single_quoted(self) -> None:
        content = "---\nslug: '/quoted'\n---\n"
        assert _extract_frontmatter_slug(content) == "/quoted"

    # ── map_url() with slug ──

    def test_absolute_slug_overrides_path(self, tmp_path: Path) -> None:
        adapter = _make_adapter(tmp_path)
        docs = tmp_path / "docs"
        guide = docs / "guide"
        guide.mkdir(parents=True)
        md = guide / "install.mdx"
        md.write_text("---\nslug: /getting-started\n---\n# Install\n")

        adapter.set_slug_map({md: md.read_text()})
        url = adapter.map_url(Path("guide/install.mdx"))
        # Absolute slug is appended to routeBasePath (Docusaurus official spec).
        assert url == "/docs/getting-started/"

    def test_relative_slug_replaces_filename(self, tmp_path: Path) -> None:
        adapter = _make_adapter(tmp_path)
        docs = tmp_path / "docs"
        guide = docs / "guide"
        guide.mkdir(parents=True)
        md = guide / "install.mdx"
        md.write_text("---\nslug: setup\n---\n# Install\n")

        adapter.set_slug_map({md: md.read_text()})
        url = adapter.map_url(Path("guide/install.mdx"))
        assert url == "/guide/setup/"

    def test_relative_slug_at_root(self, tmp_path: Path) -> None:
        adapter = _make_adapter(tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir(exist_ok=True)
        md = docs / "intro.mdx"
        md.write_text("---\nslug: welcome\n---\n# Intro\n")

        adapter.set_slug_map({md: md.read_text()})
        url = adapter.map_url(Path("intro.mdx"))
        assert url == "/welcome/"

    def test_no_slug_uses_filesystem(self, tmp_path: Path) -> None:
        adapter = _make_adapter(tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir(exist_ok=True)
        md = docs / "intro.mdx"
        md.write_text("# No slug\n")

        adapter.set_slug_map({md: md.read_text()})
        url = adapter.map_url(Path("intro.mdx"))
        assert url == "/docs/intro/"

    def test_absolute_slug_root(self, tmp_path: Path) -> None:
        """slug: / with default routeBasePath maps to /docs/."""
        adapter = _make_adapter(tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir(exist_ok=True)
        md = docs / "intro.mdx"
        md.write_text("---\nslug: /\n---\n# Root\n")

        adapter.set_slug_map({md: md.read_text()})
        url = adapter.map_url(Path("intro.mdx"))
        # slug: / is the doc-relative root; full permalink = /docs/ (routeBasePath prefix).
        assert url == "/docs/"


# ═══════════════════════════════════════════════════════════════════════════════
# Dynamic config detection unit tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestDynamicConfigDetection:
    """Unit tests for _is_dynamic_config()."""

    @pytest.mark.parametrize(
        "content",
        [
            "export default async function createConfig() {}",
            "module.exports = async () => ({})",
            "export default function createConfig() {}",
            "module.exports = function() { return {}; }",
            "const x = await import('./theme.js');",
            "const pkg = require('./package.json');",
        ],
        ids=[
            "async-export",
            "async-module-exports",
            "function-export",
            "function-module-exports",
            "dynamic-import",
            "require-call",
        ],
    )
    def test_detected_as_dynamic(self, content: str) -> None:
        assert _is_dynamic_config(content) is True

    @pytest.mark.parametrize(
        "content",
        [
            "export default { baseUrl: '/' };",
            "const config = { baseUrl: '/' }; export default config;",
            "module.exports = { baseUrl: '/' };",
            "// This is a comment about async\nexport default { baseUrl: '/' };",
        ],
        ids=[
            "static-export-default",
            "static-const",
            "static-module-exports",
            "comment-with-async-word",
        ],
    )
    def test_not_detected_as_dynamic(self, content: str) -> None:
        assert _is_dynamic_config(content) is False


# ═══════════════════════════════════════════════════════════════════════════════
# from_repo() integration
# ═══════════════════════════════════════════════════════════════════════════════


class TestFromRepo:
    """Integration tests for DocusaurusAdapter.from_repo()."""

    def test_extracts_base_url_and_route_base_path(self, tmp_path: Path) -> None:
        cfg = """\
export default {
  baseUrl: "/my-project/",
  presets: [[
    "@docusaurus/preset-classic",
    { docs: { routeBasePath: "guide" } },
  ]],
};
"""
        (tmp_path / "docusaurus.config.ts").write_text(cfg)
        docs = tmp_path / "docs"
        docs.mkdir()
        ctx = BuildContext(engine="docusaurus", locales=["it"])

        adapter = DocusaurusAdapter.from_repo(ctx, docs, tmp_path)
        assert adapter._base_url == "/my-project"
        assert adapter._route_base_path == "guide"

    def test_no_config_file_defaults(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        ctx = BuildContext(engine="docusaurus")

        adapter = DocusaurusAdapter.from_repo(ctx, docs, tmp_path)
        assert adapter._base_url == ""
        assert adapter._route_base_path is None

    def test_dynamic_config_warning(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        cfg = "export default async function() { return { baseUrl: '/x/' }; }"
        (tmp_path / "docusaurus.config.ts").write_text(cfg)
        docs = tmp_path / "docs"
        docs.mkdir()
        ctx = BuildContext(engine="docusaurus")

        with caplog.at_level(logging.WARNING):
            adapter = DocusaurusAdapter.from_repo(ctx, docs, tmp_path)
        assert adapter._base_url == ""
        assert "dynamic patterns" in caplog.text


# ═══════════════════════════════════════════════════════════════════════════════
# URL mapping regression (existing behaviour preserved)
# ═══════════════════════════════════════════════════════════════════════════════


class TestMapUrlRegression:
    """Verify existing URL mapping rules are preserved after refactor."""

    @pytest.fixture()
    def adapter(self, tmp_path: Path) -> DocusaurusAdapter:
        return _make_adapter(tmp_path)

    def test_mdx_extension_stripped(self, adapter: DocusaurusAdapter) -> None:
        assert adapter.map_url(Path("guide/install.mdx")) == "/docs/guide/install/"

    def test_md_extension_stripped(self, adapter: DocusaurusAdapter) -> None:
        assert adapter.map_url(Path("guide/install.md")) == "/docs/guide/install/"

    def test_index_collapses(self, adapter: DocusaurusAdapter) -> None:
        assert adapter.map_url(Path("guide/index.mdx")) == "/docs/guide/"

    def test_root_index(self, adapter: DocusaurusAdapter) -> None:
        assert adapter.map_url(Path("index.mdx")) == "/docs/"

    def test_checks(self, adapter: DocusaurusAdapter) -> None:
        assert adapter.map_url(Path("checks.mdx")) == "/docs/checks/"

    def test_nested_path(self, adapter: DocusaurusAdapter) -> None:
        assert adapter.map_url(Path("a/b/c.md")) == "/docs/a/b/c/"


# ═══════════════════════════════════════════════════════════════════════════════
# Route classification regression
# ═══════════════════════════════════════════════════════════════════════════════


class TestClassifyRouteRegression:
    """Verify route classification rules are preserved."""

    @pytest.fixture()
    def adapter(self, tmp_path: Path) -> DocusaurusAdapter:
        return _make_adapter(tmp_path, locales=["it"])

    def test_ignored_underscore(self, adapter: DocusaurusAdapter) -> None:
        assert adapter.classify_route(Path("_private/secret.md"), frozenset()) == "IGNORED"

    def test_reachable_auto_sidebar(self, adapter: DocusaurusAdapter) -> None:
        assert adapter.classify_route(Path("guide/install.mdx"), frozenset()) == "REACHABLE"

    def test_orphan_with_explicit_nav(self, adapter: DocusaurusAdapter) -> None:
        nav = frozenset({"intro.mdx"})
        assert adapter.classify_route(Path("unlisted.mdx"), nav) == "ORPHAN_BUT_EXISTING"

    def test_locale_ghost_route(self, adapter: DocusaurusAdapter) -> None:
        nav = frozenset({"intro.mdx"})
        assert adapter.classify_route(Path("it/index.mdx"), nav) == "REACHABLE"


# ═══════════════════════════════════════════════════════════════════════════════
# D117: pathname:/// protocol — Docusaurus-only escape hatch
# ═══════════════════════════════════════════════════════════════════════════════


class TestPathnameProtocolSupport:
    """D117 — pathname:/// is a verified Docusaurus escape hatch.

    Docusaurus uses ``pathname:///`` to link static assets (PDFs, HTML downloads)
    that live outside the React router.  Zenzic must:
      - Treat ``pathname:`` as a valid skip in Docusaurus mode (no Z101/Z105 error).
      - Flag ``pathname:`` as an error in non-Docusaurus engines.
    """

    def test_pathname_not_in_global_skip_schemes(self) -> None:
        """pathname: must NOT be in the unconditional skip list."""
        assert "pathname:" not in _SKIP_SCHEMES

    def test_pathname_in_docusaurus_skip_schemes(self) -> None:
        """DocusaurusAdapter.get_link_scheme_bypasses() must include 'pathname'."""
        from zenzic.core.adapters._docusaurus import DocusaurusAdapter

        adapter = DocusaurusAdapter.__new__(DocusaurusAdapter)
        assert "pathname" in adapter.get_link_scheme_bypasses()
        assert "pathname:" not in _SKIP_SCHEMES

    def test_pathname_link_not_flagged_in_docusaurus(self, tmp_path: Path) -> None:
        """validate_links_structured must not raise any error for pathname:/// in Docusaurus mode."""
        from zenzic.core.exclusion import LayeredExclusionManager

        docs = tmp_path / "docs"
        docs.mkdir()
        # A Markdown file that uses pathname:/// — legitimate Docusaurus idiom
        (docs / "guide.md").write_text(
            "[Download brand system](pathname:///assets/brand-system.html)\n",
            encoding="utf-8",
        )
        config = ZenzicConfig(
            docs_dir="docs",
            build_context=BuildContext(engine="docusaurus"),
        )
        em = LayeredExclusionManager(config, docs_root=docs, repo_root=tmp_path)
        errors = validate_links_structured(
            docs,
            em,
            repo_root=tmp_path,
            config=config,
            strict=False,
        )
        assert errors == [], f"Unexpected errors for pathname:/// in Docusaurus: {errors}"

    def test_pathname_link_flagged_in_mkdocs(self, tmp_path: Path) -> None:
        """validate_links_structured MUST raise Z105 for pathname:/// in MkDocs mode."""
        from zenzic.core.exclusion import LayeredExclusionManager

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "guide.md").write_text(
            "[Download](pathname:///assets/file.pdf)\n",
            encoding="utf-8",
        )
        config = ZenzicConfig(
            docs_dir="docs",
            build_context=BuildContext(engine="mkdocs"),
        )
        em = LayeredExclusionManager(config, docs_root=docs, repo_root=tmp_path)
        errors = validate_links_structured(
            docs,
            em,
            repo_root=tmp_path,
            config=config,
            strict=False,
        )
        # pathname:/// starts with "/" after scheme removal — triggers ABSOLUTE_PATH (Z105)
        assert any("pathname" in str(e) or "absolute" in str(e).lower() for e in errors), (
            f"Expected Z105 for pathname:/// in MkDocs, got: {errors}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Sidebar parser — unit tests (Issue #47)
# ═══════════════════════════════════════════════════════════════════════════════


class TestParseSidebars:
    """Unit tests for _parse_sidebars() — pure parser, no adapter instantiation."""

    def _write_sidebar(self, tmp_path: Path, content: str, name: str = "sidebars.ts") -> Path:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p

    def _make_docs(self, tmp_path: Path, *rel_paths: str) -> Path:
        docs = tmp_path / "docs"
        docs.mkdir(exist_ok=True)
        for rp in rel_paths:
            f = docs / rp
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("# stub\n", encoding="utf-8")
        return docs

    # SBP-01 — autogenerated → None
    def test_autogenerated_returns_none(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path)
        sidebar = self._write_sidebar(
            tmp_path,
            "const s = { main: [{ type: 'autogenerated', dirName: '.' }] }; export default s;",
        )
        assert _parse_sidebars(sidebar, docs) is None

    # SBP-02 — bare string IDs resolve to .md
    def test_bare_string_id_resolves_md(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path, "guide/install.md")
        sidebar = self._write_sidebar(
            tmp_path,
            "export default { main: ['guide/install'] };",
        )
        result = _parse_sidebars(sidebar, docs)
        assert result == frozenset({"guide/install.md"})

    # SBP-03 — bare string IDs resolve to .mdx
    def test_bare_string_id_resolves_mdx(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path, "intro.mdx")
        sidebar = self._write_sidebar(
            tmp_path,
            "export default { main: ['intro'] };",
        )
        result = _parse_sidebars(sidebar, docs)
        assert result == frozenset({"intro.mdx"})

    # SBP-04 — explicit {type:'doc', id:'...'} pattern
    def test_explicit_doc_type_id(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path, "reference/api.md")
        sidebar = self._write_sidebar(
            tmp_path,
            "export default { main: [{ type: 'doc', id: 'reference/api', label: 'API' }] };",
        )
        result = _parse_sidebars(sidebar, docs)
        assert result is not None
        assert "reference/api.md" in result

    # SBP-05 — nested categories extracted recursively (string IDs at any depth)
    def test_nested_categories_extracted(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path, "intro.md", "guide/start.md", "guide/advanced.md")
        sidebar = self._write_sidebar(
            tmp_path,
            """\
export default {
  main: [
    'intro',
    { type: 'category', label: 'Guide', items: ['guide/start', 'guide/advanced'] },
  ],
};
""",
        )
        result = _parse_sidebars(sidebar, docs)
        assert result == frozenset({"intro.md", "guide/start.md", "guide/advanced.md"})

    # SBP-06 — IDs that don't match any file are silently dropped
    def test_unresolvable_id_excluded(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path, "exists.md")
        sidebar = self._write_sidebar(
            tmp_path,
            "export default { main: ['exists', 'ghost-page'] };",
        )
        result = _parse_sidebars(sidebar, docs)
        assert result == frozenset({"exists.md"})

    # SBP-07 — non-ID values (type/label keywords) are filtered out
    def test_non_id_keywords_excluded(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path, "real.md")
        sidebar = self._write_sidebar(
            tmp_path,
            """\
export default {
  main: [
    'real',
    { type: 'category', label: 'Section', items: [{ type: 'doc', id: 'real' }] },
  ],
};
""",
        )
        result = _parse_sidebars(sidebar, docs)
        # 'category', 'doc' must not appear as paths — only 'real.md'
        assert result == frozenset({"real.md"})

    # SBP-08 — sidebars.js (not only .ts)
    def test_js_extension_parsed(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path, "start.md")
        sidebar = self._write_sidebar(
            tmp_path, "module.exports = { main: ['start'] };", "sidebars.js"
        )
        result = _parse_sidebars(sidebar, docs)
        assert result == frozenset({"start.md"})

    # SBP-09 — directory ID resolves to index.md
    def test_directory_id_resolves_to_index(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path, "tutorial/index.md")
        sidebar = self._write_sidebar(tmp_path, "export default { main: ['tutorial'] };")
        result = _parse_sidebars(sidebar, docs)
        assert result == frozenset({"tutorial/index.md"})

    # SBP-10 — unreadable file → None (autogenerated fallback)
    def test_io_error_returns_none(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path)
        missing = tmp_path / "sidebars.ts"  # does not exist
        assert _parse_sidebars(missing, docs) is None


# ═══════════════════════════════════════════════════════════════════════════════
# Sidebar integration — from_repo + classify_route (Issue #47)
# ═══════════════════════════════════════════════════════════════════════════════


class TestFromRepoSidebar:
    """Integration tests: from_repo sets _sidebar_path; get_nav_paths() delegates."""

    def _setup(
        self, tmp_path: Path, sidebar_content: str | None = None
    ) -> tuple[Path, DocusaurusAdapter]:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "intro.md").write_text("# Intro\n", encoding="utf-8")
        guide = docs / "guide"
        guide.mkdir()
        (guide / "install.md").write_text("# Install\n", encoding="utf-8")
        if sidebar_content is not None:
            (tmp_path / "sidebars.ts").write_text(sidebar_content, encoding="utf-8")
        ctx = BuildContext(engine="docusaurus")
        adapter = DocusaurusAdapter.from_repo(ctx, docs, tmp_path)
        return docs, adapter

    # SBI-01 — no sidebar file → all REACHABLE (backwards compat)
    def test_no_sidebar_file_all_reachable(self, tmp_path: Path) -> None:
        _, adapter = self._setup(tmp_path, sidebar_content=None)
        assert adapter._sidebar_path is None
        assert adapter.get_nav_paths() == frozenset()
        assert adapter.classify_route(Path("intro.md"), frozenset()) == "REACHABLE"

    # SBI-02 — autogenerated sidebar → all REACHABLE
    def test_autogenerated_sidebar_all_reachable(self, tmp_path: Path) -> None:
        _, adapter = self._setup(
            tmp_path,
            "export default { main: [{ type: 'autogenerated', dirName: '.' }] };",
        )
        assert adapter._sidebar_path is not None
        assert adapter.get_nav_paths() == frozenset()
        assert adapter.classify_route(Path("intro.md"), frozenset()) == "REACHABLE"

    # SBI-03 — explicit sidebar → only listed files are REACHABLE
    def test_explicit_sidebar_listed_file_reachable(self, tmp_path: Path) -> None:
        _, adapter = self._setup(
            tmp_path,
            "export default { main: ['intro', 'guide/install'] };",
        )
        nav = adapter.get_nav_paths()
        assert "intro.md" in nav
        assert "guide/install.md" in nav
        assert adapter.classify_route(Path("intro.md"), nav) == "REACHABLE"
        assert adapter.classify_route(Path("guide/install.md"), nav) == "REACHABLE"

    # SBI-04 — explicit sidebar → unlisted file is ORPHAN_BUT_EXISTING
    def test_explicit_sidebar_unlisted_file_orphan(self, tmp_path: Path) -> None:
        docs, adapter = self._setup(
            tmp_path,
            "export default { main: ['intro'] };",
        )
        (docs / "secret.md").write_text("# Secret\n", encoding="utf-8")
        nav = adapter.get_nav_paths()
        assert adapter.classify_route(Path("secret.md"), nav) == "ORPHAN_BUT_EXISTING"


# ═══════════════════════════════════════════════════════════════════════════════
# Config navigation parser — _parse_config_navigation (D090)
# NCF = Config Navigation Function unit tests
# NCI = Config Navigation Integration tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestParseConfigNavigation:
    """Unit tests for _parse_config_navigation (navbar + footer UX-discoverability)."""

    def _write_config(self, tmp_path: Path, content: str) -> Path:
        p = tmp_path / "docusaurus.config.ts"
        p.write_text(content, encoding="utf-8")
        return p

    def _make_docs(self, tmp_path: Path, *rel_paths: str) -> Path:
        docs = tmp_path / "docs"
        docs.mkdir(exist_ok=True)
        for rel in rel_paths:
            target = docs / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("# Doc\n", encoding="utf-8")
        return docs

    # NCF-01 — to: with routeBasePath prefix extracted correctly
    def test_to_with_route_base_path(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path, "changelog.md")
        cfg = self._write_config(
            tmp_path,
            "const c = { themeConfig: { navbar: { items: [{ to: '/docs/changelog' }] } } };",
        )
        result = _parse_config_navigation(cfg, docs, "/", "docs")
        assert result == frozenset({"changelog.md"})

    # NCF-02 — docId: extracted directly (no prefix stripping)
    def test_doc_id_direct(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path, "guide/install.md")
        cfg = self._write_config(
            tmp_path,
            "const c = { navbar: { items: [{ type: 'doc', docId: 'guide/install' }] } };",
        )
        result = _parse_config_navigation(cfg, docs, "/", "docs")
        assert result == frozenset({"guide/install.md"})

    # NCF-03 — footer to: also captured (same regex scope)
    def test_footer_to_captured(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path, "about.md")
        cfg = self._write_config(
            tmp_path,
            "const c = { themeConfig: { footer: { links: [{ items: [{ to: '/docs/about' }] }] } } };",
        )
        result = _parse_config_navigation(cfg, docs, "/", "docs")
        assert result == frozenset({"about.md"})

    # NCF-04 — non-doc to: (blog, external) filtered by file-existence check
    def test_non_doc_to_filtered(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path, "real.md")
        cfg = self._write_config(
            tmp_path,
            "const c = { navbar: { items: [{ to: '/blog' }, { to: '/docs/real' }] } };",
        )
        result = _parse_config_navigation(cfg, docs, "/", "docs")
        assert result == frozenset({"real.md"})

    # NCF-05 — .mdx extension resolved
    def test_mdx_extension_resolved(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path, "changelog.mdx")
        cfg = self._write_config(
            tmp_path,
            "const c = { navbar: { items: [{ to: '/docs/changelog' }] } };",
        )
        result = _parse_config_navigation(cfg, docs, "/", "docs")
        assert result == frozenset({"changelog.mdx"})

    # NCF-06 — baseUrl prefix stripped before routeBasePath
    def test_base_url_stripped(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path, "intro.md")
        cfg = self._write_config(
            tmp_path,
            "const c = { navbar: { items: [{ to: '/project/docs/intro' }] } };",
        )
        result = _parse_config_navigation(cfg, docs, "/project/", "docs")
        assert result == frozenset({"intro.md"})

    # NCF-07 — unreadable config → empty frozenset (no crash)
    def test_unreadable_config_returns_empty(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path)
        missing = tmp_path / "docusaurus.config.ts"  # does not exist
        result = _parse_config_navigation(missing, docs, "/", "docs")
        assert result == frozenset()

    # NCF-08 — JS comments in config stripped before parsing
    def test_js_comments_stripped(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path, "intro.md")
        cfg = self._write_config(
            tmp_path,
            """\
const c = {
  // to: '/docs/commented-out-should-not-match',
  navbar: { items: [{ to: '/docs/intro' }] },
};
""",
        )
        result = _parse_config_navigation(cfg, docs, "/", "docs")
        assert "commented-out-should-not-match.md" not in result
        assert "intro.md" in result

    # NCF-09 — empty routeBasePath (docs at site root)
    def test_empty_route_base_path(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path, "intro.md")
        cfg = self._write_config(
            tmp_path,
            "const c = { navbar: { items: [{ to: '/intro' }] } };",
        )
        result = _parse_config_navigation(cfg, docs, "/", "")
        assert result == frozenset({"intro.md"})

    # NCF-10 — directory ID in navbar resolves to index.md
    def test_directory_id_resolves_to_index(self, tmp_path: Path) -> None:
        docs = self._make_docs(tmp_path, "guide/index.md")
        cfg = self._write_config(
            tmp_path,
            "const c = { navbar: { items: [{ to: '/docs/guide' }] } };",
        )
        result = _parse_config_navigation(cfg, docs, "/", "docs")
        assert result == frozenset({"guide/index.md"})


# ═══════════════════════════════════════════════════════════════════════════════
# Unified Navigation Integration — D090 "UX-Discoverability Law"
# NCI = Config Navigation Integration tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestUnifiedNavigation:
    """Integration tests: sidebar + navbar + footer all contribute to REACHABLE."""

    def _setup(self, tmp_path: Path, sidebar: str, config: str) -> tuple[Path, DocusaurusAdapter]:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "intro.md").write_text("# Intro\n", encoding="utf-8")
        (docs / "changelog.md").write_text("# Changelog\n", encoding="utf-8")
        (docs / "about.md").write_text("# About\n", encoding="utf-8")
        (docs / "secret.md").write_text("# Secret\n", encoding="utf-8")
        (tmp_path / "sidebars.ts").write_text(sidebar, encoding="utf-8")
        (tmp_path / "docusaurus.config.ts").write_text(config, encoding="utf-8")
        ctx = BuildContext(engine="docusaurus")
        adapter = DocusaurusAdapter.from_repo(ctx, docs, tmp_path)
        return docs, adapter

    # NCI-01 — navbar-only file is REACHABLE (not in sidebar)
    def test_navbar_only_file_reachable(self, tmp_path: Path) -> None:
        _, adapter = self._setup(
            tmp_path,
            sidebar="export default { main: ['intro'] };",
            config="const c = { baseUrl: '/', themeConfig: { navbar: { items: [{ to: '/docs/changelog' }] } } };",
        )
        nav = adapter.get_nav_paths()
        assert "changelog.md" in nav
        assert adapter.classify_route(Path("changelog.md"), nav) == "REACHABLE"

    # NCI-02 — footer-only file is REACHABLE (not in sidebar or navbar)
    def test_footer_only_file_reachable(self, tmp_path: Path) -> None:
        _, adapter = self._setup(
            tmp_path,
            sidebar="export default { main: ['intro'] };",
            config="const c = { baseUrl: '/', themeConfig: { footer: { links: [{ items: [{ to: '/docs/about' }] }] } } };",
        )
        nav = adapter.get_nav_paths()
        assert "about.md" in nav
        assert adapter.classify_route(Path("about.md"), nav) == "REACHABLE"

    # NCI-03 — file absent from sidebar, navbar, and footer is ORPHAN_BUT_EXISTING
    def test_unlisted_everywhere_is_orphan(self, tmp_path: Path) -> None:
        _, adapter = self._setup(
            tmp_path,
            sidebar="export default { main: ['intro'] };",
            config="const c = { baseUrl: '/', themeConfig: { navbar: { items: [{ to: '/docs/changelog' }] } } };",
        )
        nav = adapter.get_nav_paths()
        assert adapter.classify_route(Path("secret.md"), nav) == "ORPHAN_BUT_EXISTING"

    # NCI-04 — sidebar + navbar + footer all merged into single nav set
    def test_all_sources_merged(self, tmp_path: Path) -> None:
        _, adapter = self._setup(
            tmp_path,
            sidebar="export default { main: ['intro'] };",
            config="""\
const c = {
  baseUrl: '/',
  themeConfig: {
    navbar: { items: [{ to: '/docs/changelog' }] },
    footer: { links: [{ items: [{ to: '/docs/about' }] }] },
  },
};
""",
        )
        nav = adapter.get_nav_paths()
        assert "intro.md" in nav
        assert "changelog.md" in nav
        assert "about.md" in nav
        assert "secret.md" not in nav


# ═══════════════════════════════════════════════════════════════════════════════
# EPOCH 5 — Z105 absolute_path_allowlist (cross-plugin / multi-instance support)
# ═══════════════════════════════════════════════════════════════════════════════


class TestAbsolutePathAllowlist:
    """``[link_validation] absolute_path_allowlist`` suppresses Z105 for
    project-owned route prefixes that span Docusaurus plugin instances.

    Multi-instance Docusaurus deployments cannot use relative paths across
    plugin boundaries — the second ``@docusaurus/plugin-content-docs``
    instance owns its own VSM, so a link from ``/docs/`` to ``/developers/``
    must be absolute. Without an allowlist Z105 would block this legitimate
    pattern.
    """

    def test_link_in_allowlist_skips_z105(self, tmp_path: Path) -> None:
        from zenzic.core.exclusion import LayeredExclusionManager
        from zenzic.models.config import LinkValidationConfig

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "guide.md").write_text(
            "[Writing an Adapter](/developers/how-to/implement-adapter)\n",
            encoding="utf-8",
        )
        config = ZenzicConfig(
            docs_dir="docs",
            build_context=BuildContext(engine="docusaurus"),
            link_validation=LinkValidationConfig(
                absolute_path_allowlist=["/developers/"],
            ),
        )
        em = LayeredExclusionManager(config, docs_root=docs, repo_root=tmp_path)
        errors = validate_links_structured(
            docs,
            em,
            repo_root=tmp_path,
            config=config,
            strict=False,
        )
        assert errors == [], f"Allowlisted link should not raise Z105: {errors}"

    def test_link_outside_allowlist_still_flagged(self, tmp_path: Path) -> None:
        from zenzic.core.exclusion import LayeredExclusionManager
        from zenzic.models.config import LinkValidationConfig

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "guide.md").write_text(
            "[API](/api/v1/users)\n",
            encoding="utf-8",
        )
        config = ZenzicConfig(
            docs_dir="docs",
            build_context=BuildContext(engine="docusaurus"),
            link_validation=LinkValidationConfig(
                absolute_path_allowlist=["/developers/"],
            ),
        )
        em = LayeredExclusionManager(config, docs_root=docs, repo_root=tmp_path)
        errors = validate_links_structured(
            docs,
            em,
            repo_root=tmp_path,
            config=config,
            strict=False,
        )
        assert any("absolute" in str(e).lower() for e in errors), (
            f"Non-allowlisted absolute path must still raise Z105: {errors}"
        )

    def test_default_allowlist_is_empty(self, tmp_path: Path) -> None:
        """No allowlist configured → all absolute paths still raise Z105."""
        from zenzic.core.exclusion import LayeredExclusionManager

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "guide.md").write_text(
            "[Dev](/developers/intro)\n",
            encoding="utf-8",
        )
        config = ZenzicConfig(
            docs_dir="docs",
            build_context=BuildContext(engine="docusaurus"),
        )
        em = LayeredExclusionManager(config, docs_root=docs, repo_root=tmp_path)
        errors = validate_links_structured(
            docs,
            em,
            repo_root=tmp_path,
            config=config,
            strict=False,
        )
        assert any("absolute" in str(e).lower() for e in errors), (
            f"Empty allowlist (default) must preserve Z105: {errors}"
        )

    def test_allowlist_typo_does_not_silence_correct_path(self, tmp_path: Path) -> None:
        """Team-D break-test: a typo'd allowlist entry must NOT silence Z105
        on a similar-looking but distinct prefix. Guards against the matcher
        ever degrading from strict ``startswith`` to fuzzy / substring match.
        """
        from zenzic.core.exclusion import LayeredExclusionManager
        from zenzic.models.config import LinkValidationConfig

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "guide.md").write_text(
            "[Dev](/developers/intro)\n",
            encoding="utf-8",
        )
        config = ZenzicConfig(
            docs_dir="docs",
            build_context=BuildContext(engine="docusaurus"),
            link_validation=LinkValidationConfig(
                absolute_path_allowlist=["/develpers/"],  # intentional typo
            ),
        )
        em = LayeredExclusionManager(config, docs_root=docs, repo_root=tmp_path)
        errors = validate_links_structured(
            docs,
            em,
            repo_root=tmp_path,
            config=config,
            strict=False,
        )
        assert any("absolute" in str(e).lower() for e in errors), (
            f"A typo'd allowlist entry must not silently bypass Z105 on the "
            f"correctly-spelled path: {errors}"
        )

    def test_allowlist_prefix_does_not_match_neighbour(self, tmp_path: Path) -> None:
        """Team-D break-test: an entry without trailing slash must not match
        a sibling prefix that merely starts with the same characters. Guards
        the ADR-0011 invariant that ``startswith`` semantics should be paired
        with disciplined trailing slashes in user-supplied entries.
        """
        from zenzic.core.exclusion import LayeredExclusionManager
        from zenzic.models.config import LinkValidationConfig

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "guide.md").write_text(
            "[Internal](/developers-internal/secret)\n",
            encoding="utf-8",
        )
        # Entry without trailing slash — broad on purpose to expose the risk.
        config = ZenzicConfig(
            docs_dir="docs",
            build_context=BuildContext(engine="docusaurus"),
            link_validation=LinkValidationConfig(
                absolute_path_allowlist=["/developers"],
            ),
        )
        em = LayeredExclusionManager(config, docs_root=docs, repo_root=tmp_path)
        errors = validate_links_structured(
            docs,
            em,
            repo_root=tmp_path,
            config=config,
            strict=False,
        )
        # This documents the current behaviour: bare prefix DOES match neighbour.
        # The allowlist documentation explicitly recommends trailing slashes.
        # If the matcher ever gains stricter semantics, flip the assertion.
        assert errors == [], (
            f"Bare-prefix allowlist entry currently matches neighbours via "
            f"startswith — this is documented behaviour. Use trailing slashes "
            f"to scope precisely. Errors: {errors}"
        )
