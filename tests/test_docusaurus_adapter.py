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
    _strip_js_comments,
    find_docusaurus_config,
)
from zenzic.models.config import BuildContext


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
        assert url == "/getting-started/"

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
        """slug: / should map to root."""
        adapter = _make_adapter(tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir(exist_ok=True)
        md = docs / "intro.mdx"
        md.write_text("---\nslug: /\n---\n# Root\n")

        adapter.set_slug_map({md: md.read_text()})
        url = adapter.map_url(Path("intro.mdx"))
        assert url == "/"


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
