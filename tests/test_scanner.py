# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for Zenzic scanner (orphans, placeholders, root discovery)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml
from _helpers import make_mgr

from zenzic.core.adapter import _extract_i18n_locale_dirs, _extract_i18n_locale_patterns
from zenzic.core.scanner import (
    check_placeholder_content,
    find_orphans,
    find_placeholders,
    find_repo_root,
    find_unused_assets,
)
from zenzic.models.config import ZenzicConfig


def test_find_repo_root_success(tmp_path: Path) -> None:
    # Setup mock repo — uses zenzic.toml as the engine-neutral root marker
    repo = tmp_path / "my_repo"
    repo.mkdir()
    (repo / "zenzic.toml").touch()

    deep_dir = repo / "docs" / "nested" / "dir"
    deep_dir.mkdir(parents=True)

    # Change CWD temporarily
    original_cwd = Path.cwd()
    os.chdir(deep_dir)
    try:
        found = find_repo_root()
        assert found == repo.resolve()
    finally:
        os.chdir(original_cwd)


def test_find_repo_root_failure(tmp_path: Path) -> None:
    # A directory with no mkdocs.yml or .git
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    original_cwd = Path.cwd()
    os.chdir(empty_dir)
    try:
        with pytest.raises(RuntimeError, match="Could not locate repo root"):
            find_repo_root()
    finally:
        os.chdir(original_cwd)


def test_find_orphans(tmp_path: Path) -> None:
    repo = tmp_path / "my_repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)

    # Create mkdocs.yml with a simple nav
    nav = {"nav": ["index.md", {"API": "api.md"}, {"Nested": [{"Sub": "nested/page.md"}]}]}
    with (repo / "mkdocs.yml").open("w") as f:
        yaml.dump(nav, f)

    # Create files
    (docs / "index.md").touch()
    (docs / "api.md").touch()
    (docs / "nested").mkdir()
    (docs / "nested/page.md").touch()

    # Create orphans
    (docs / "orphan1.md").touch()
    (docs / "nested/orphan2.md").touch()

    # Excluded directory
    (docs / "includes").mkdir()
    (docs / "includes/snippet.md").touch()

    config = ZenzicConfig(excluded_dirs=["includes"])
    mgr = make_mgr(config, repo_root=repo)
    orphans = find_orphans(docs, mgr, repo_root=repo, config=config)

    orphan_paths = [p.as_posix() for p in orphans]
    assert "orphan1.md" in orphan_paths
    assert "nested/orphan2.md" in orphan_paths
    assert "index.md" not in orphan_paths
    assert "api.md" not in orphan_paths
    assert "includes/snippet.md" not in orphan_paths
    assert len(orphans) == 2


def test_find_placeholders(tmp_path: Path) -> None:
    repo = tmp_path / "my_repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)

    # 1. Short document (< 50 words)
    (docs / "short.md").write_text("This is too short.")

    # 2. Document with placeholder pattern
    long_text = "word " * 60 + "\\n TODO: write this section."
    (docs / "has_todo.md").write_text(long_text)

    # 3. Valid document
    valid_text = "word " * 60 + "\\n This is a complete and valid section."
    (docs / "valid.md").write_text(valid_text)

    config = ZenzicConfig(placeholder_max_words=50, placeholder_patterns=["todo"])
    mgr = make_mgr(config, repo_root=repo)
    findings = find_placeholders(docs, mgr, config=config)

    assert len(findings) == 2

    issues = {f.issue for f in findings}
    assert "short-content" in issues
    assert "placeholder-text" in issues

    file_paths = {f.file_path.name for f in findings}
    assert "short.md" in file_paths
    assert "has_todo.md" in file_paths
    assert "valid.md" not in file_paths


def test_find_repo_root_via_git(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    deep = repo / "src" / "pkg"
    deep.mkdir(parents=True)
    original_cwd = Path.cwd()
    os.chdir(deep)
    try:
        assert find_repo_root() == repo.resolve()
    finally:
        os.chdir(original_cwd)


def test_find_repo_root_genesis_fallback(tmp_path: Path) -> None:
    """ZRT-005: fallback_to_cwd=True must return CWD in an empty directory."""
    empty = tmp_path / "brand_new_project"
    empty.mkdir()
    original_cwd = Path.cwd()
    os.chdir(empty)
    try:
        result = find_repo_root(fallback_to_cwd=True)
        assert result == empty.resolve()
    finally:
        os.chdir(original_cwd)


def test_find_repo_root_genesis_fallback_still_raises_without_flag(tmp_path: Path) -> None:
    """ZRT-005: default behaviour (fallback_to_cwd=False) still raises in empty dirs."""
    empty = tmp_path / "no_root"
    empty.mkdir()
    original_cwd = Path.cwd()
    os.chdir(empty)
    try:
        with pytest.raises(RuntimeError, match="Could not locate repo root"):
            find_repo_root()
    finally:
        os.chdir(original_cwd)


def test_find_orphans_no_config(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)
    nav = {"nav": [{"Home": "index.md"}]}
    with (repo / "mkdocs.yml").open("w") as f:
        yaml.dump(nav, f)
    (docs / "index.md").touch()
    (docs / "extra.md").touch()
    # Call without config — triggers the default ZenzicConfig() branch
    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=repo)
    orphans = find_orphans(docs, mgr, repo_root=repo, config=config)
    assert len(orphans) == 1


def test_find_orphans_config_file_missing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    # No mkdocs.yml, no zensical.toml → find_config_file returns None → find_orphans returns []
    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=repo)
    docs_root = repo / config.docs_dir
    orphans = find_orphans(docs_root, mgr, repo_root=repo, config=config)
    assert orphans == []


def test_find_orphans_invalid_yaml(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)
    (repo / "mkdocs.yml").write_text("nav: [: invalid")
    (docs / "page.md").touch()
    # Should not raise; falls back to empty nav and MkDocs semantics treat
    # the site as filesystem-driven rather than synthesizing orphans.
    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=repo)
    orphans = find_orphans(docs, mgr, repo_root=repo, config=config)
    assert orphans == []


def test_find_orphans_symlink_skipped(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)
    nav = {"nav": [{"Home": "index.md"}]}
    with (repo / "mkdocs.yml").open("w") as f:
        yaml.dump(nav, f)
    (docs / "index.md").touch()
    real = tmp_path / "real.md"
    real.touch()
    (docs / "linked.md").symlink_to(real)
    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=repo)
    orphans = find_orphans(docs, mgr, repo_root=repo, config=config)
    # symlink should not appear in orphans
    assert all(p.name != "linked.md" for p in orphans)


def test_find_orphans_docs_not_exist(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "mkdocs.yml").write_text("nav:\n  - Home: index.md\n")
    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=repo)
    docs_root = repo / config.docs_dir
    orphans = find_orphans(docs_root, mgr, repo_root=repo, config=config)
    assert orphans == []


def test_find_placeholders_no_config(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "stub.md").write_text("TODO: write me")
    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=tmp_path)
    findings = find_placeholders(docs, mgr, config=config)
    assert any(f.issue == "placeholder-text" for f in findings)


def test_find_placeholders_docs_not_exist(tmp_path: Path) -> None:
    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=tmp_path)
    docs_root = tmp_path / config.docs_dir
    findings = find_placeholders(docs_root, mgr, config=config)
    assert findings == []


def test_find_placeholders_symlink_skipped(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    real = tmp_path / "real.md"
    real.write_text("TODO: skipped")
    (docs / "linked.md").symlink_to(real)
    config = ZenzicConfig(placeholder_patterns=["todo"])
    mgr = make_mgr(config, repo_root=tmp_path)
    findings = find_placeholders(docs, mgr, config=config)
    assert findings == []


def test_placeholder_mdx_comments_excluded_from_word_count() -> None:
    """MDX {/* … */} and HTML <!-- … --> comments must not count as prose words.

    Regression: docs/community/license.mdx had <10 visible words but was not
    flagged because its {/* … */} comment block (70+ words) inflated the count.
    """
    # Only 4 visible prose words — far below the default threshold of 50.
    # The comment contains >60 words and must be ignored.
    text = """\
---
sidebar_label: "License"
description: "Licensing information."
---

# License

{/*
This page uses the pymdownx snippets extension to include the root LICENSE file
directly — single source of truth, no divergence possible.

Below, we add some extra explanation text about how this license applies to the
Zenzic documentation and source code, as required to provide more context to our users
and to pass internal minimum content validation checks within our own linting loops.
*/}

See LICENSE file.
"""
    config = ZenzicConfig(placeholder_max_words=50)
    findings = check_placeholder_content(text, "community/license.mdx", config)
    assert any(f.issue == "short-content" for f in findings), (
        "Page with MDX-comment-inflated word count must still be flagged as short-content"
    )


def test_short_content_pointer_skips_frontmatter() -> None:
    """Z502 short-content finding must point to the first content line, not to frontmatter.

    Regression (D048 Bug 1): line_no was hardcoded to 1, causing the red arrow ``❱``
    to point at the opening ``---`` of the frontmatter block, misleading users into
    thinking frontmatter words were being counted as content.
    """
    text = """\
---
icon: ShieldCheck
sidebar_label: Licenza
title: Licenza Apache 2.0
description: Informazioni sulla licenza.
---

# Licenza

LICENZA
"""
    config = ZenzicConfig(placeholder_max_words=50)
    findings = check_placeholder_content(text, "community/license.mdx", config)
    short = [f for f in findings if f.issue == "short-content"]
    assert short, "Page with 3 visible words must trigger short-content"
    # The finding must NOT point at line 1 (the opening ``---``).
    assert short[0].line_no > 1, (
        f"short-content finding points at line {short[0].line_no} — "
        "expected a line past the frontmatter block"
    )


def test_short_content_pointer_skips_spdx_comments() -> None:
    """Z502 short-content finding must skip leading SPDX HTML comments when computing line_no.

    Regression (D072 — The Ghost Content Fix): ``_first_content_line`` was anchored to
    ``\\A`` via the frontmatter regex and returned line 1 whenever the file opened with
    ``<!-- SPDX … -->`` comments, causing the red arrow ``❱`` to point at the licence
    header instead of the first prose word.
    """
    # 5 SPDX comment lines + blank + 10-line frontmatter + blank + single word.
    # REUSE-IgnoreStart
    text = (
        "<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->\n"
        "<!-- SPDX-License-Identifier: Apache-2.0 -->\n"
        "<!-- SPDX-FileCopyrightText: 2024 Contributor A -->\n"
        "<!-- SPDX-License-Identifier: MIT -->\n"
        "<!-- Internal audit marker: approved -->\n"
        "\n"
        "---\n"
        "title: SPDX Trap\n"
        "sidebar_label: Trap\n"
        "description: Regression test for comment-aware pointer.\n"
        "icon: lock\n"
        "draft: true\n"
        "tags: [test, spdx]\n"
        "keywords: [regression]\n"
        "version: 0.7.0\n"
        "---\n"
        "\n"
        "FINE\n"
    )
    # REUSE-IgnoreEnd
    config = ZenzicConfig(placeholder_max_words=50)
    findings = check_placeholder_content(text, "spdx-trap.md", config)
    short = [f for f in findings if f.issue == "short-content"]
    assert short, "File with single word 'FINE' must trigger short-content"
    assert short[0].detail == "Page has only 1 words (minimum 50)."
    # The pointer must land on the line containing "FINE", not on any comment or frontmatter.
    target_line = text.splitlines()[short[0].line_no - 1]
    assert target_line.strip() == "FINE", (
        f"short-content pointer at line {short[0].line_no} is {target_line!r}; "
        "expected the line containing 'FINE'"
    )


def test_short_content_pointer_skips_multiline_html_comment() -> None:
    """_first_content_line must traverse a multi-line HTML comment (in_html=True path).

    Covers the ``in_html`` continuation branch — lines 209-213, 221 in scanner.py.
    When ``<!--`` and ``-->`` appear on different lines the walker must consume
    every continuation line before recognising prose content.
    """
    # REUSE-IgnoreStart
    text = (
        "<!--\n"
        " SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>\n"
        " SPDX-License-Identifier: Apache-2.0\n"
        "-->\n"
        "\n"
        "Brief.\n"
    )
    # REUSE-IgnoreEnd
    config = ZenzicConfig(placeholder_max_words=50)
    findings = check_placeholder_content(text, "multi-html.mdx", config)
    short = [f for f in findings if f.issue == "short-content"]
    assert short, "Single-word prose must trigger short-content"
    target_line = text.splitlines()[short[0].line_no - 1]
    assert target_line.strip() == "Brief.", (
        f"Pointer at line {short[0].line_no} is {target_line!r}; expected 'Brief.'"
    )


def test_short_content_pointer_skips_multiline_mdx_comment() -> None:
    """_first_content_line must traverse a multi-line MDX comment (in_mdx=True path).

    Covers the ``in_mdx`` continuation branch — lines 214-218, 226 in scanner.py.
    When ``{/*`` and ``*/`` appear on different lines the walker must consume
    every continuation line before recognising prose content.
    """
    # REUSE-IgnoreStart
    text = (
        "{/*\n"
        " SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>\n"
        " SPDX-License-Identifier: Apache-2.0\n"
        "*/}\n"
        "\n"
        "Note.\n"
    )
    # REUSE-IgnoreEnd
    config = ZenzicConfig(placeholder_max_words=50)
    findings = check_placeholder_content(text, "multi-mdx.mdx", config)
    short = [f for f in findings if f.issue == "short-content"]
    assert short, "Single-word prose must trigger short-content"
    target_line = text.splitlines()[short[0].line_no - 1]
    assert target_line.strip() == "Note.", (
        f"Pointer at line {short[0].line_no} is {target_line!r}; expected 'Note.'"
    )


def test_short_content_pointer_unclosed_frontmatter() -> None:
    """_first_content_line handles frontmatter with no closing ``---`` (EOF branch).

    Covers the ``if i < n:`` False branch at line 239 in scanner.py — when the
    frontmatter opening ``---`` is found but EOF is reached before the closing ``---``.
    The function must not raise; it returns the line after the last consumed line.
    """
    text = "---\ntitle: Unclosed\nsidebar_label: Unclosed\n"
    config = ZenzicConfig(placeholder_max_words=50)
    findings = check_placeholder_content(text, "unclosed-fm.mdx", config)
    # Unclosed frontmatter is not stripped by _FRONTMATTER_RE → word count > 0 but < 50
    short = [f for f in findings if f.issue == "short-content"]
    assert short, "Near-empty file must trigger short-content"
    assert short[0].line_no >= 1


def test_find_unused_assets_no_config(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    assets = docs / "assets"
    assets.mkdir()
    (assets / "img.png").touch()
    (docs / "index.md").write_text("No images here.")
    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=tmp_path)
    unused = find_unused_assets(docs, mgr, config=config)
    assert any(p.name == "img.png" for p in unused)


def test_find_unused_assets_docs_not_exist(tmp_path: Path) -> None:
    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=tmp_path)
    docs_root = tmp_path / config.docs_dir
    unused = find_unused_assets(docs_root, mgr, config=config)
    assert unused == []


def test_find_orphans_excluded_file_patterns(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)
    nav = {"nav": [{"Home": "index.md"}]}
    with (repo / "mkdocs.yml").open("w") as f:
        yaml.dump(nav, f)
    (docs / "index.md").touch()
    (docs / "index.it.md").touch()  # i18n locale variant — should not be an orphan
    config = ZenzicConfig(excluded_file_patterns=["*.it.md"])
    mgr = make_mgr(config, repo_root=repo)
    orphans = find_orphans(docs, mgr, repo_root=repo, config=config)
    assert orphans == []


def test_find_orphans_respects_mkdocs_route_classification(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    docs = repo / "docs"
    (docs / "guide").mkdir(parents=True)
    nav = {"nav": [{"Docs": [{"Overview": "guide/index.md"}]}]}
    with (repo / "mkdocs.yml").open("w") as f:
        yaml.dump(nav, f)

    (docs / "guide" / "index.md").write_text("# Overview\n")
    (docs / "guide" / "orphan.md").write_text("# Orphan\n")

    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=repo)
    orphans = find_orphans(docs, mgr, repo_root=repo, config=config)
    orphan_paths = {p.as_posix() for p in orphans}

    assert "guide/index.md" not in orphan_paths
    assert "guide/orphan.md" in orphan_paths


def test_unlisted_file_detection(tmp_path: Path) -> None:
    """A file on disk but absent from nav must be reported as an orphan.

    Regression guard: mkdocs.yml can include Python-tagged YAML values such as
    !!python/name in markdown_extensions. These must not cause nav parsing to
    collapse to an empty dict, otherwise every file is incorrectly marked
    REACHABLE.
    """
    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)

    (repo / "mkdocs.yml").write_text(
        "\n".join(
            [
                "site_name: Test Docs",
                "nav:",
                "  - Home: index.md",
                "markdown_extensions:",
                "  - pymdownx.superfences:",
                "      custom_fences:",
                "        - name: mermaid",
                "          class: mermaid",
                "          format: !!python/name:pymdownx.superfences.fence_code_format",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    (docs / "spy.md").write_text("# Spy\n", encoding="utf-8")

    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=repo)
    orphans = find_orphans(docs, mgr, repo_root=repo, config=config)
    orphan_paths = {p.as_posix() for p in orphans}

    assert "spy.md" in orphan_paths
    assert "index.md" not in orphan_paths


def test_extract_i18n_locale_patterns_suffix_mode() -> None:
    doc_config = {
        "plugins": [
            {
                "i18n": {
                    "docs_structure": "suffix",
                    "languages": [
                        {"locale": "en", "default": True},
                        {"locale": "it"},
                        {"locale": "fr"},
                    ],
                }
            }
        ]
    }
    patterns = _extract_i18n_locale_patterns(doc_config)
    assert patterns == {"*.it.md", "*.fr.md"}


def test_extract_i18n_locale_patterns_folder_mode() -> None:
    # docs_structure: folder — locale files are in subdirs, not suffix-named
    doc_config = {
        "plugins": [
            {
                "i18n": {
                    "docs_structure": "folder",
                    "languages": [{"locale": "en", "default": True}, {"locale": "it"}],
                }
            }
        ]
    }
    patterns = _extract_i18n_locale_patterns(doc_config)
    assert patterns == set()


def test_extract_i18n_locale_patterns_no_plugin() -> None:
    assert _extract_i18n_locale_patterns({}) == set()
    assert _extract_i18n_locale_patterns({"plugins": ["search"]}) == set()


def test_find_orphans_i18n_auto_detect_mkdocs(tmp_path: Path) -> None:
    """i18n plugin in mkdocs.yml; nav also from mkdocs.yml."""
    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)
    mkdocs_content = {
        "nav": [{"Home": "index.md"}],
        "plugins": [
            {
                "i18n": {
                    "docs_structure": "suffix",
                    "languages": [
                        {"locale": "en", "default": True},
                        {"locale": "it"},
                        {"locale": "fr"},
                    ],
                }
            }
        ],
    }
    with (repo / "mkdocs.yml").open("w") as f:
        yaml.dump(mkdocs_content, f)
    (docs / "index.md").touch()
    (docs / "index.it.md").touch()
    (docs / "index.fr.md").touch()
    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=repo)
    orphans = find_orphans(docs, mgr, repo_root=repo, config=config)
    assert orphans == []


# ─── S4-1: _extract_i18n_locale_dirs (folder mode) ───────────────────────────


def test_extract_i18n_locale_dirs_folder_mode() -> None:
    """Non-default locale dirs returned when docs_structure is 'folder'."""
    doc_config = {
        "plugins": [
            {
                "i18n": {
                    "docs_structure": "folder",
                    "languages": [
                        {"locale": "en", "default": True},
                        {"locale": "it"},
                        {"locale": "fr"},
                    ],
                }
            }
        ]
    }
    assert _extract_i18n_locale_dirs(doc_config) == {"it", "fr"}


def test_extract_i18n_locale_dirs_suffix_mode_returns_empty() -> None:
    """Suffix mode is handled by _extract_i18n_locale_patterns — dirs returns empty."""
    doc_config = {
        "plugins": [
            {
                "i18n": {
                    "docs_structure": "suffix",
                    "languages": [
                        {"locale": "en", "default": True},
                        {"locale": "it"},
                    ],
                }
            }
        ]
    }
    assert _extract_i18n_locale_dirs(doc_config) == set()


def test_extract_i18n_locale_dirs_no_plugin() -> None:
    """Returns empty set when no i18n plugin is configured."""
    assert _extract_i18n_locale_dirs({}) == set()
    assert _extract_i18n_locale_dirs({"plugins": ["search"]}) == set()


def test_extract_i18n_locale_dirs_defensive_none_inputs() -> None:
    """Never raises — returns empty set for malformed / missing keys.

    Regression guard for projects without i18n: _extract_i18n_locale_dirs
    must be safe to call on any dict, including one with None-valued keys.
    """
    assert _extract_i18n_locale_dirs({"plugins": None}) == set()
    assert _extract_i18n_locale_dirs({"plugins": [{"i18n": None}]}) == set()
    assert _extract_i18n_locale_dirs({"plugins": [{"i18n": {"docs_structure": "folder"}}]}) == set()
    assert (
        _extract_i18n_locale_dirs(
            {"plugins": [{"i18n": {"docs_structure": "folder", "languages": None}}]}
        )
        == set()
    )


def test_i18n_languages_is_null(tmp_path: Path) -> None:
    """Scenario: i18n plugin with 'languages: null' in YAML must not raise.

    YAML snippet::

        plugins:
          - i18n:
              languages: null

    Zenzic must return set() and find_orphans must not crash.
    This is the exact YAML pattern the Tech Lead flagged.
    """
    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)

    # Build the YAML that triggered the bug: languages: null (not a list)
    yaml_content = (
        "nav:\n  - Home: index.md\n"
        "plugins:\n  - i18n:\n      docs_structure: folder\n      languages: null\n"
    )
    (repo / "mkdocs.yml").write_text(yaml_content)
    (docs / "index.md").touch()

    # _extract_i18n_locale_dirs must return empty set — not raise TypeError
    import yaml as _yaml

    from zenzic.core.adapter import _PermissiveYamlLoader

    doc_config = _yaml.load(yaml_content, Loader=_PermissiveYamlLoader) or {}
    assert _extract_i18n_locale_dirs(doc_config) == set()

    # find_orphans end-to-end must also not crash
    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=repo)
    orphans = find_orphans(docs, mgr, repo_root=repo, config=config)
    assert orphans == []


def test_extract_i18n_locale_dirs_scenario_standalone() -> None:
    """Scenario 'Standalone': mkdocs.yml without any plugin returns empty set.

    Zenzic must be a safe drop-in for projects that have not yet adopted i18n.
    """
    assert _extract_i18n_locale_dirs({}) == set()
    assert _extract_i18n_locale_dirs({"plugins": ["search", "minify"]}) == set()
    assert (
        _extract_i18n_locale_dirs({"site_name": "My Docs", "nav": [{"Home": "index.md"}]}) == set()
    )


def test_extract_i18n_locale_dirs_scenario_broken_config() -> None:
    """Scenario 'Broken Config': malformed i18n block never raises — always set().

    Zenzic does not correct user configuration; it only avoids crashing.
    Edge cases covered:
    - languages is a scalar string instead of a list
    - languages contains non-dict items (ints, nulls)
    - locale key is present but empty string
    - docs_structure key is absent entirely
    """
    # languages: "it"  (scalar string instead of list)
    assert (
        _extract_i18n_locale_dirs(
            {"plugins": [{"i18n": {"docs_structure": "folder", "languages": "it"}}]}
        )
        == set()
    )

    # languages list contains non-dict items
    assert (
        _extract_i18n_locale_dirs(
            {"plugins": [{"i18n": {"docs_structure": "folder", "languages": [None, 42, "it"]}}]}
        )
        == set()
    )

    # locale key present but empty string
    assert (
        _extract_i18n_locale_dirs(
            {
                "plugins": [
                    {
                        "i18n": {
                            "docs_structure": "folder",
                            "languages": [{"locale": "", "default": False}],
                        }
                    }
                ]
            }
        )
        == set()
    )

    # docs_structure key absent — treated as non-folder
    assert (
        _extract_i18n_locale_dirs({"plugins": [{"i18n": {"languages": [{"locale": "it"}]}}]})
        == set()
    )


def test_extract_i18n_locale_dirs_default_locale_excluded() -> None:
    """The default locale is never returned — only non-default translations."""
    doc_config = {
        "plugins": [
            {
                "i18n": {
                    "docs_structure": "folder",
                    "languages": [{"locale": "en", "default": True}],
                }
            }
        ]
    }
    assert _extract_i18n_locale_dirs(doc_config) == set()


def test_find_orphans_folder_i18n_excludes_locale_dirs(tmp_path: Path) -> None:
    """Files inside non-default locale dirs are NOT flagged as orphans (folder mode)."""
    repo = tmp_path / "repo"
    docs = repo / "docs"
    (docs / "it").mkdir(parents=True)

    mkdocs_config = {
        "nav": [{"Home": "index.md"}],
        "plugins": [
            {
                "i18n": {
                    "docs_structure": "folder",
                    "languages": [
                        {"locale": "en", "default": True},
                        {"locale": "it"},
                    ],
                }
            }
        ],
    }
    with (repo / "mkdocs.yml").open("w") as f:
        yaml.dump(mkdocs_config, f)

    (docs / "index.md").touch()
    (docs / "it" / "index.md").touch()  # Italian mirror — must NOT be flagged
    (docs / "orphan.md").touch()  # genuine orphan

    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=repo)
    orphans = find_orphans(docs, mgr, repo_root=repo, config=config)
    orphan_posix = [p.as_posix() for p in orphans]

    assert "orphan.md" in orphan_posix
    assert "it/index.md" not in orphan_posix
    assert len(orphans) == 1


def test_find_orphans_folder_i18n_nested_file_excluded(tmp_path: Path) -> None:
    """Files nested inside a locale dir (e.g. it/guide/install.md) are also excluded."""
    repo = tmp_path / "repo"
    docs = repo / "docs"
    (docs / "it" / "guide").mkdir(parents=True)

    with (repo / "mkdocs.yml").open("w") as f:
        yaml.dump(
            {
                "nav": [{"Home": "index.md"}],
                "plugins": [
                    {
                        "i18n": {
                            "docs_structure": "folder",
                            "languages": [
                                {"locale": "en", "default": True},
                                {"locale": "it"},
                            ],
                        }
                    }
                ],
            },
            f,
        )

    (docs / "index.md").touch()
    (docs / "it" / "index.md").touch()
    (docs / "it" / "guide" / "install.md").touch()

    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=repo)
    orphans = find_orphans(docs, mgr, repo_root=repo, config=config)
    assert orphans == []


# ─────────────────────────────────────────────────────────────────────────────


def test_find_unused_assets_symlink_skipped(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    real = tmp_path / "real.md"
    real.write_text("![img](assets/img.png)")
    (docs / "linked.md").symlink_to(real)
    assets = docs / "assets"
    assets.mkdir()
    (assets / "img.png").touch()
    # symlinked md file is skipped → img.png has no references → unused
    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=tmp_path)
    unused = find_unused_assets(docs, mgr, config=config)
    assert any(p.name == "img.png" for p in unused)


# ─── find_unused_assets — L1 System File Guardrails (CEO-050) ────────────────


def test_find_unused_assets_skips_system_infrastructure_files(tmp_path: Path) -> None:
    """System infrastructure files must never appear as Z903 findings.

    Regression (D050): when docs_root == project root, toolchain files like
    package.json were included in the asset walk and emitted spurious Z903
    warnings. The Level 1a guardrail in find_unused_assets must filter them.
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Hello\n")
    # Infra files that must be silently skipped
    (docs / "package.json").write_text("{}")
    (docs / "pyproject.toml").write_text("[project]")
    (docs / "yarn.lock").write_text("")
    (docs / "eslint.config.mjs").write_text("export default {};")

    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=tmp_path)
    unused = find_unused_assets(docs, mgr, config=config)

    infra_names = {p.name for p in unused}
    assert "package.json" not in infra_names, "package.json must be shielded (L1a)"
    assert "pyproject.toml" not in infra_names, "pyproject.toml must be shielded (L1a)"
    assert "yarn.lock" not in infra_names, "yarn.lock must be shielded (L1a)"
    assert "eslint.config.mjs" not in infra_names, "eslint.config.mjs must be shielded (L1a)"


def test_find_unused_assets_skips_adapter_metadata_files(tmp_path: Path) -> None:
    """Adapter metadata files must be excluded via the adapter_metadata_files param.

    Regression (D050): docusaurus.config.ts in docs_root triggered Z903 when
    the Docusaurus adapter's metadata files were not passed to find_unused_assets.
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Hello\n")
    (docs / "docusaurus.config.ts").write_text("export default {};")
    (docs / "sidebars.ts").write_text("export default {};")
    (docs / "logo.png").write_bytes(b"\x89PNG")  # unreferenced — should be reported

    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=tmp_path)
    adapter_meta = frozenset({"docusaurus.config.ts", "sidebars.ts"})
    unused = find_unused_assets(docs, mgr, config=config, adapter_metadata_files=adapter_meta)

    unused_names = {p.name for p in unused}
    assert "docusaurus.config.ts" not in unused_names, "adapter config must be shielded (L1b)"
    assert "sidebars.ts" not in unused_names, "adapter sidebar must be shielded (L1b)"
    assert "logo.png" in unused_names, "genuine unused asset must still be reported"
