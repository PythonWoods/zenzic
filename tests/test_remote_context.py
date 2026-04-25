# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""CEO-052 "The Stranger" — remote context regression tests.

Invariant: "The configuration follows the target, not the caller."

When Zenzic is invoked from repository A pointing at repository B,
every decision — engine, docs_dir, exclusions — must reflect B's
configuration exclusively.  A's configuration must never leak into B's scan.
"""

from __future__ import annotations

import os
from pathlib import Path

from zenzic.cli._check import _apply_target
from zenzic.core.scanner import find_repo_root
from zenzic.models.config import ZenzicConfig


# ── find_repo_root(search_from=...) ──────────────────────────────────────────


class TestFindRepoRootSearchFrom:
    """find_repo_root must anchor to search_from, not to CWD."""

    def test_search_from_finds_target_repo_root(self, tmp_path: Path) -> None:
        """Calling from outside repo B still discovers B's root via search_from."""
        repo_a = tmp_path / "repo_a"
        repo_b = tmp_path / "repo_b"
        (repo_a / ".git").mkdir(parents=True)
        (repo_b / ".git").mkdir(parents=True)
        deep_in_b = repo_b / "docs" / "guide"
        deep_in_b.mkdir(parents=True)

        original_cwd = Path.cwd()
        os.chdir(repo_a)
        try:
            # search_from points INTO repo B — root must be repo_b, not repo_a
            result = find_repo_root(search_from=deep_in_b)
            assert result == repo_b.resolve()
        finally:
            os.chdir(original_cwd)

    def test_search_from_overrides_cwd_repo(self, tmp_path: Path) -> None:
        """When CWD is repo A and search_from is inside repo B, repo B wins."""
        repo_a = tmp_path / "repo_a"
        repo_b = tmp_path / "repo_b"
        repo_a.mkdir()
        repo_b.mkdir()
        (repo_a / "zenzic.toml").write_text("[build_context]\nengine = 'mkdocs'\n")
        (repo_a / ".git").mkdir()
        (repo_b / "zenzic.toml").write_text("[build_context]\nengine = 'docusaurus'\n")
        (repo_b / ".git").mkdir()

        original_cwd = Path.cwd()
        os.chdir(repo_a)
        try:
            root_from_cwd = find_repo_root()
            assert root_from_cwd == repo_a.resolve(), "Baseline: CWD finds repo_a"

            root_from_b = find_repo_root(search_from=repo_b)
            assert root_from_b == repo_b.resolve(), "search_from=repo_b must find repo_b"
            assert root_from_b != root_from_cwd, "Roots must differ — configs are isolated"
        finally:
            os.chdir(original_cwd)

    def test_search_from_zenzic_toml_marker(self, tmp_path: Path) -> None:
        """zenzic.toml (not .git) is sufficient as a root marker when using search_from."""
        repo_b = tmp_path / "repo_b"
        (repo_b / "docs").mkdir(parents=True)
        (repo_b / "zenzic.toml").write_text("")

        # CWD is tmp_path (no root marker here)
        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        try:
            result = find_repo_root(search_from=repo_b / "docs")
            assert result == repo_b.resolve()
        finally:
            os.chdir(original_cwd)

    def test_search_from_none_falls_back_to_cwd(self, tmp_path: Path) -> None:
        """Without search_from, existing CWD-based behaviour is unchanged."""
        repo = tmp_path / "repo"
        (repo / ".git").mkdir(parents=True)

        original_cwd = Path.cwd()
        os.chdir(repo)
        try:
            assert find_repo_root(search_from=None) == repo.resolve()
        finally:
            os.chdir(original_cwd)


# ── _apply_target sovereign root guard ───────────────────────────────────────


class TestApplyTargetSovereignRoot:
    """When target == repo_root, docs_dir must be preserved from config."""

    def test_sovereign_root_preserves_docs_dir(self, tmp_path: Path) -> None:
        """Pointing at repo root must NOT override docs_dir to '.'."""
        repo = tmp_path / "repo"
        docs = repo / "docs"
        docs.mkdir(parents=True)
        (repo / "zenzic.toml").write_text("")
        (repo / ".git").mkdir()
        (docs / "index.md").write_text("# Home\n")

        config = ZenzicConfig(docs_dir=Path("docs"))
        _, single_file, docs_root, _ = _apply_target(repo, config, str(repo))

        assert single_file is None, "Directory mode: single_file must be None"
        assert docs_root == docs.resolve(), (
            "docs_root must point at configured docs_dir, not the repo root"
        )

    def test_sovereign_root_docs_root_excludes_blog(self, tmp_path: Path) -> None:
        """Scan scope when target == repo_root must exclude project-level dirs.

        CEO-052: the fix prevents scanning blog/, scripts/, etc. when the
        explicit target is the project root itself.
        """
        repo = tmp_path / "repo"
        docs = repo / "docs"
        blog = repo / "blog"
        docs.mkdir(parents=True)
        blog.mkdir()
        (repo / ".git").mkdir()
        (repo / "zenzic.toml").write_text("")
        (docs / "index.md").write_text("# Home\n")
        (blog / "2026-post.md").write_text("# Blog Post\n")

        config = ZenzicConfig(docs_dir=Path("docs"))
        _, _, docs_root, _ = _apply_target(repo, config, str(repo))

        # blog/ must NOT be under docs_root
        assert not blog.resolve().is_relative_to(docs_root), (
            "blog/ must be outside docs_root — CEO-052 scope isolation"
        )

    def test_subdirectory_target_still_overrides_docs_dir(self, tmp_path: Path) -> None:
        """When target is a sub-directory (not the root), docs_dir IS overridden."""
        repo = tmp_path / "repo"
        sub = repo / "content"
        sub.mkdir(parents=True)
        (repo / ".git").mkdir()
        (repo / "zenzic.toml").write_text("")
        (sub / "index.md").write_text("# Content\n")

        config = ZenzicConfig(docs_dir=Path("docs"))
        _, _, docs_root, _ = _apply_target(repo, config, str(sub))

        assert docs_root == sub.resolve(), (
            "Sub-directory target should set docs_root to the sub-directory"
        )


# ── Configuration isolation (end-to-end unit) ────────────────────────────────


class TestConfigIsolation:
    """Config loaded for a scan must come exclusively from the target repo."""

    def test_config_loaded_from_target_not_caller(self, tmp_path: Path) -> None:
        """ZenzicConfig.load must read from target repo_root, not CWD's root.

        This is the core CEO-052 invariant: running Zenzic from repo A pointing
        at repo B must load B's zenzic.toml, not A's.
        """
        repo_a = tmp_path / "repo_a"
        repo_b = tmp_path / "repo_b"
        repo_a.mkdir()
        repo_b.mkdir()
        (repo_a / ".git").mkdir()
        (repo_b / ".git").mkdir()

        # A has strict=true, B has strict=false
        (repo_a / "zenzic.toml").write_text("strict = true\n")
        (repo_b / "zenzic.toml").write_text("strict = false\n")

        original_cwd = Path.cwd()
        os.chdir(repo_a)
        try:
            # The sovereign root fix: search_from = repo_b
            root_b = find_repo_root(search_from=repo_b)
            config_b, loaded = ZenzicConfig.load(root_b)

            assert root_b == repo_b.resolve()
            assert loaded is True, "Config file must be found in repo_b"
            assert config_b.strict is False, "B's strict=false must be loaded, not A's strict=true"
        finally:
            os.chdir(original_cwd)

    def test_docs_dir_from_target_config(self, tmp_path: Path) -> None:
        """docs_dir must be read from B's zenzic.toml, not A's."""
        repo_a = tmp_path / "repo_a"
        repo_b = tmp_path / "repo_b"
        repo_a.mkdir()
        repo_b.mkdir()
        (repo_a / ".git").mkdir()
        (repo_b / ".git").mkdir()
        (repo_b / "documentation").mkdir()  # B uses "documentation" not "docs"

        (repo_a / "zenzic.toml").write_text('docs_dir = "docs"\n')
        (repo_b / "zenzic.toml").write_text('docs_dir = "documentation"\n')

        original_cwd = Path.cwd()
        os.chdir(repo_a)
        try:
            root_b = find_repo_root(search_from=repo_b)
            config_b, _ = ZenzicConfig.load(root_b)

            assert str(config_b.docs_dir) == "documentation", (
                "B's docs_dir='documentation' must be used, not A's docs_dir='docs'"
            )
        finally:
            os.chdir(original_cwd)
