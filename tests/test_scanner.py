# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for Zenzic scanner (orphans, placeholders, root discovery)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from zenzic.core.adapter import _extract_i18n_locale_dirs, _extract_i18n_locale_patterns
from zenzic.core.scanner import (
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
    orphans = find_orphans(repo, config)

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
    findings = find_placeholders(repo, config)

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


def test_find_orphans_no_config(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)
    nav = {"nav": [{"Home": "index.md"}]}
    with (repo / "mkdocs.yml").open("w") as f:
        yaml.dump(nav, f)
    (docs / "index.md").touch()
    (docs / "extra.md").touch()
    # Call without config — triggers the `if config is None` branch
    orphans = find_orphans(repo)
    assert len(orphans) == 1


def test_find_orphans_config_file_missing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    # No mkdocs.yml, no zensical.toml → find_config_file returns None → find_orphans returns []
    orphans = find_orphans(repo)
    assert orphans == []


def test_find_orphans_invalid_yaml(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)
    (repo / "mkdocs.yml").write_text("nav: [: invalid")
    (docs / "page.md").touch()
    # Should not raise; falls back to empty nav and MkDocs semantics treat
    # the site as filesystem-driven rather than synthesizing orphans.
    orphans = find_orphans(repo)
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
    orphans = find_orphans(repo)
    # symlink should not appear in orphans
    assert all(p.name != "linked.md" for p in orphans)


def test_find_orphans_docs_not_exist(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "mkdocs.yml").write_text("nav:\n  - Home: index.md\n")
    orphans = find_orphans(repo)
    assert orphans == []


def test_find_placeholders_no_config(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "stub.md").write_text("TODO: write me")
    findings = find_placeholders(tmp_path)
    assert any(f.issue == "placeholder-text" for f in findings)


def test_find_placeholders_docs_not_exist(tmp_path: Path) -> None:
    findings = find_placeholders(tmp_path)
    assert findings == []


def test_find_placeholders_symlink_skipped(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    real = tmp_path / "real.md"
    real.write_text("TODO: skipped")
    (docs / "linked.md").symlink_to(real)
    findings = find_placeholders(tmp_path, ZenzicConfig(placeholder_patterns=["todo"]))
    assert findings == []


def test_find_unused_assets_no_config(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    assets = docs / "assets"
    assets.mkdir()
    (assets / "img.png").touch()
    (docs / "index.md").write_text("No images here.")
    unused = find_unused_assets(tmp_path)
    assert any(p.name == "img.png" for p in unused)


def test_find_unused_assets_docs_not_exist(tmp_path: Path) -> None:
    unused = find_unused_assets(tmp_path)
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
    orphans = find_orphans(repo, config)
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

    orphans = find_orphans(repo)
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

    orphans = find_orphans(repo)
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
    orphans = find_orphans(repo)
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
    orphans = find_orphans(repo)
    assert orphans == []


def test_extract_i18n_locale_dirs_scenario_vanilla() -> None:
    """Scenario 'Vanilla': mkdocs.yml without any plugin returns empty set.

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

    orphans = find_orphans(repo)
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

    orphans = find_orphans(repo)
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
    unused = find_unused_assets(tmp_path)
    assert any(p.name == "img.png" for p in unused)
