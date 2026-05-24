# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for the Layered Exclusion system: VCSIgnoreParser + LayeredExclusionManager.

Test-driven development: these tests were written **before** the implementation.
"""

from __future__ import annotations

from pathlib import Path

from zenzic.models.config import SYSTEM_EXCLUDED_DIRS, ZenzicConfig


# ══════════════════════════════════════════════════════════════════════════════
# LayeredExclusionManager
# ══════════════════════════════════════════════════════════════════════════════


class TestLayeredExclusionManagerSystemGuardrails:
    """L1: System guardrails can never be bypassed."""

    def test_system_dirs_always_excluded(self) -> None:
        from zenzic.core.exclusion import LayeredExclusionManager

        config = ZenzicConfig()
        mgr = LayeredExclusionManager(config)
        for d in SYSTEM_EXCLUDED_DIRS:
            assert mgr.should_exclude_dir(d), f"{d} must be excluded"

    def test_system_dirs_not_overridden_by_cli_include(self) -> None:
        from zenzic.core.exclusion import LayeredExclusionManager

        config = ZenzicConfig()
        mgr = LayeredExclusionManager(config, cli_include=[".git"])
        assert mgr.should_exclude_dir(".git")

    def test_system_dirs_not_overridden_by_forced_inclusion(self) -> None:
        from zenzic.core.exclusion import LayeredExclusionManager

        config = ZenzicConfig.model_construct(
            included_dirs=[".git"],
            excluded_dirs=list(SYSTEM_EXCLUDED_DIRS),
        )
        mgr = LayeredExclusionManager(config)
        assert mgr.should_exclude_dir(".git")


class TestLayeredExclusionManagerForcedInclusion:
    """L2: Forced inclusions override VCS and Config exclusions."""

    def test_included_dirs_override_config_exclusion(self) -> None:
        from zenzic.core.exclusion import LayeredExclusionManager

        config = ZenzicConfig.model_construct(
            excluded_dirs=["generated"],
            included_dirs=["generated"],
            excluded_file_patterns=[],
            included_file_patterns=[],
            respect_vcs_ignore=False,
        )
        mgr = LayeredExclusionManager(config)
        assert not mgr.should_exclude_dir("generated")

    def test_included_file_patterns_override_exclusion(self, tmp_path: Path) -> None:
        from zenzic.core.exclusion import LayeredExclusionManager

        config = ZenzicConfig.model_construct(
            excluded_file_patterns=["*.generated.md"],
            included_file_patterns=["api.generated.md"],
            excluded_dirs=[],
            included_dirs=[],
            respect_vcs_ignore=False,
        )
        docs = tmp_path / "docs"
        docs.mkdir()
        target = docs / "api.generated.md"
        target.touch()
        mgr = LayeredExclusionManager(config, docs_root=docs)
        assert not mgr.should_exclude_file(target, docs)

    def test_forced_inclusion_does_not_override_system_guardrails(self) -> None:
        from zenzic.core.exclusion import LayeredExclusionManager

        config = ZenzicConfig.model_construct(
            included_dirs=["node_modules"],
            excluded_dirs=list(SYSTEM_EXCLUDED_DIRS),
        )
        mgr = LayeredExclusionManager(config)
        assert mgr.should_exclude_dir("node_modules")


class TestLayeredExclusionManagerCLIOverrides:
    """L4: CLI --exclude-dir and --include-dir."""

    def test_cli_exclude_dir(self) -> None:
        from zenzic.core.exclusion import LayeredExclusionManager

        config = ZenzicConfig()
        mgr = LayeredExclusionManager(config, cli_exclude=["drafts"])
        assert mgr.should_exclude_dir("drafts")

    def test_cli_include_dir_overrides_config_exclusion(self) -> None:
        from zenzic.core.exclusion import LayeredExclusionManager

        config = ZenzicConfig.model_construct(
            excluded_dirs=["staging"],
            included_dirs=[],
            excluded_file_patterns=[],
            included_file_patterns=[],
            respect_vcs_ignore=False,
        )
        mgr = LayeredExclusionManager(config, cli_include=["staging"])
        assert not mgr.should_exclude_dir("staging")

    def test_cli_exclude_does_not_override_system_guardrails(self) -> None:
        """CLI include cannot rescue a system-excluded dir."""
        from zenzic.core.exclusion import LayeredExclusionManager

        config = ZenzicConfig()
        mgr = LayeredExclusionManager(config, cli_include=[".venv"])
        assert mgr.should_exclude_dir(".venv")


class TestLayeredExclusionManagerVCS:
    """L2 VCS: respect_vcs_ignore integration."""

    def test_vcs_ignored_when_respect_enabled(self, tmp_path: Path) -> None:
        from zenzic.core.exclusion import LayeredExclusionManager

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.draft.md\n")
        config = ZenzicConfig.model_construct(
            respect_vcs_ignore=True,
            excluded_dirs=[],
            included_dirs=[],
            excluded_file_patterns=[],
            included_file_patterns=[],
        )
        docs = tmp_path / "docs"
        docs.mkdir()
        target = docs / "notes.draft.md"
        target.touch()
        mgr = LayeredExclusionManager(config, repo_root=tmp_path, docs_root=docs)
        assert mgr.should_exclude_file(target, docs)

    def test_vcs_not_used_when_respect_disabled(self, tmp_path: Path) -> None:
        from zenzic.core.exclusion import LayeredExclusionManager

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.draft.md\n")
        config = ZenzicConfig.model_construct(
            respect_vcs_ignore=False,
            excluded_dirs=[],
            included_dirs=[],
            excluded_file_patterns=[],
            included_file_patterns=[],
        )
        docs = tmp_path / "docs"
        docs.mkdir()
        target = docs / "notes.draft.md"
        target.touch()
        mgr = LayeredExclusionManager(config, repo_root=tmp_path, docs_root=docs)
        assert not mgr.should_exclude_file(target, docs)

    def test_vcs_enabled_by_default(self, tmp_path: Path) -> None:
        """Default ZenzicConfig() activates VCS integration (new default=True).

        A file matching a .gitignore pattern must be excluded automatically
        when repo_root is provided — no explicit respect_vcs_ignore required.

        Note: dir-only patterns (trailing /) exclude directories during walk via
        should_exclude_dir(). Here we test file-level exclusion using a pattern
        without a trailing slash (matches both files and directories).
        """
        from zenzic.core.exclusion import LayeredExclusionManager

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(".draft\n")  # no trailing slash — matches files and dirs
        docs = tmp_path
        draft_dir = tmp_path / ".draft"
        draft_dir.mkdir()
        target = draft_dir / "backup.md"
        target.touch()
        mgr = LayeredExclusionManager(ZenzicConfig(), repo_root=tmp_path, docs_root=docs)
        # With default=True and a matching .gitignore rule, the file must be excluded
        assert mgr.should_exclude_file(target, docs)

    def test_vcs_dir_excluded_by_default_during_walk(self, tmp_path: Path) -> None:
        """Dir-only .gitignore patterns (trailing /) are excluded via should_exclude_dir.

        This is the production path: walk_files calls should_exclude_dir for each
        directory, so files inside a git-ignored directory are never visited.
        """
        from zenzic.core.exclusion import LayeredExclusionManager

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(".draft/\n")
        mgr = LayeredExclusionManager(ZenzicConfig(), repo_root=tmp_path, docs_root=tmp_path)
        assert mgr.should_exclude_dir(".draft", rel_path=".draft")

    def test_forced_inclusion_overrides_vcs(self, tmp_path: Path) -> None:
        from zenzic.core.exclusion import LayeredExclusionManager

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("api.generated.md\n")
        config = ZenzicConfig.model_construct(
            respect_vcs_ignore=True,
            included_file_patterns=["api.generated.md"],
            excluded_dirs=[],
            included_dirs=[],
            excluded_file_patterns=[],
        )
        docs = tmp_path / "docs"
        docs.mkdir()
        target = docs / "api.generated.md"
        target.touch()
        mgr = LayeredExclusionManager(config, repo_root=tmp_path, docs_root=docs)
        assert not mgr.should_exclude_file(target, docs)


class TestLayeredExclusionManagerConfigExclusion:
    """L3: Config-level excluded_dirs and excluded_file_patterns."""

    def test_config_excluded_dirs(self) -> None:
        from zenzic.core.exclusion import LayeredExclusionManager

        config = ZenzicConfig.model_construct(
            excluded_dirs=["includes", "stylesheets"],
            included_dirs=[],
            excluded_file_patterns=[],
            included_file_patterns=[],
            respect_vcs_ignore=False,
        )
        mgr = LayeredExclusionManager(config)
        assert mgr.should_exclude_dir("includes")
        assert mgr.should_exclude_dir("stylesheets")
        assert not mgr.should_exclude_dir("guides")

    def test_config_excluded_file_patterns(self, tmp_path: Path) -> None:
        from zenzic.core.exclusion import LayeredExclusionManager

        config = ZenzicConfig.model_construct(
            excluded_file_patterns=["*.it.md", "*.fr.md"],
            excluded_dirs=[],
            included_dirs=[],
            included_file_patterns=[],
            respect_vcs_ignore=False,
        )
        docs = tmp_path / "docs"
        docs.mkdir()
        it_file = docs / "index.it.md"
        it_file.touch()
        en_file = docs / "index.md"
        en_file.touch()
        mgr = LayeredExclusionManager(config, docs_root=docs)
        assert mgr.should_exclude_file(it_file, docs)
        assert not mgr.should_exclude_file(en_file, docs)


class TestLayeredExclusionManagerDefaultBehaviour:
    """Default config: everything included except system dirs and config defaults."""

    def test_default_config_includes_normal_dirs(self) -> None:
        from zenzic.core.exclusion import LayeredExclusionManager

        config = ZenzicConfig()
        mgr = LayeredExclusionManager(config)
        assert not mgr.should_exclude_dir("guides")
        assert not mgr.should_exclude_dir("api")

    def test_excluded_dirs_property(self) -> None:
        from zenzic.core.exclusion import LayeredExclusionManager

        config = ZenzicConfig()
        mgr = LayeredExclusionManager(config)
        ed = mgr.excluded_dirs
        assert isinstance(ed, frozenset)
        assert SYSTEM_EXCLUDED_DIRS <= ed


class TestLayeredExclusionManagerPrecedence:
    """Complete precedence chain validation."""

    def test_full_precedence_chain(self, tmp_path: Path) -> None:
        """Verify the complete 7-step precedence chain."""
        from zenzic.core.exclusion import LayeredExclusionManager

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("draft.md\nvcs-excluded.md\n")
        config = ZenzicConfig.model_construct(
            respect_vcs_ignore=True,
            excluded_dirs=["legacy"],
            excluded_file_patterns=["*.old.md"],
            included_dirs=["legacy"],  # forced inclusion overrides config
            included_file_patterns=["keep.old.md"],  # forced inclusion
        )
        docs = tmp_path / "docs"
        docs.mkdir()
        mgr = LayeredExclusionManager(config, repo_root=tmp_path, docs_root=docs)

        # L1: System guardrails always win
        assert mgr.should_exclude_dir(".git")

        # L2 forced: included_dirs overrides config excluded_dirs
        assert not mgr.should_exclude_dir("legacy")

        # L2 forced: included_file_patterns overrides excluded_file_patterns
        keep = docs / "keep.old.md"
        keep.touch()
        assert not mgr.should_exclude_file(keep, docs)

        # L2 VCS: respect_vcs_ignore excludes
        draft = docs / "draft.md"
        draft.touch()
        assert mgr.should_exclude_file(draft, docs)

        # L3 Config: excluded_file_patterns
        other_old = docs / "other.old.md"
        other_old.touch()
        assert mgr.should_exclude_file(other_old, docs)

        # L7: default = included
        normal = docs / "index.md"
        normal.touch()
        assert not mgr.should_exclude_file(normal, docs)

    def test_guardrails_bypass_kills_mutant(self) -> None:
        """A mutant that skips L1 guardrails must fail here."""
        from zenzic.core.exclusion import LayeredExclusionManager

        config = ZenzicConfig.model_construct(
            included_dirs=[".git", ".venv", "node_modules"],
            excluded_dirs=[],
        )
        mgr = LayeredExclusionManager(config, cli_include=[".git"])
        for d in [".git", ".venv", "node_modules"]:
            assert mgr.should_exclude_dir(d), f"Guardrail fail: {d}"

    def test_inclusion_precedence_kills_mutant(self, tmp_path: Path) -> None:
        """A mutant that swaps inclusion/exclusion order must fail here."""
        from zenzic.core.exclusion import LayeredExclusionManager

        config = ZenzicConfig.model_construct(
            excluded_file_patterns=["*.gen.md"],
            included_file_patterns=["api.gen.md"],
            excluded_dirs=[],
            included_dirs=[],
            respect_vcs_ignore=False,
        )
        docs = tmp_path / "docs"
        docs.mkdir()
        api = docs / "api.gen.md"
        api.touch()
        other = docs / "other.gen.md"
        other.touch()
        mgr = LayeredExclusionManager(config, docs_root=docs)
        assert not mgr.should_exclude_file(api, docs), "Forced inclusion must win"
        assert mgr.should_exclude_file(other, docs), "Non-included must be excluded"


# ─── L1a System File Guardrails (CEO-050) ────────────────────────────────────


class TestSystemFileGuardrails:
    """Level 1a: SYSTEM_EXCLUDED_FILE_NAMES / SYSTEM_EXCLUDED_FILE_PATTERNS
    are immutable and cannot be overridden by config or CLI flags."""

    def test_l1a_exact_name_excluded_from_should_exclude_file(self, tmp_path: Path) -> None:
        """package.json must be excluded regardless of where it sits in docs/."""
        from zenzic.core.exclusion import LayeredExclusionManager

        docs = tmp_path / "docs"
        docs.mkdir()
        config = ZenzicConfig()
        mgr = LayeredExclusionManager(config, docs_root=docs)
        assert mgr.should_exclude_file(docs / "package.json", docs)

    def test_l1a_glob_pattern_excluded_from_should_exclude_file(self, tmp_path: Path) -> None:
        """eslint.config.mjs matches the 'eslint.config.*' system pattern."""
        from zenzic.core.exclusion import LayeredExclusionManager

        docs = tmp_path / "docs"
        docs.mkdir()
        mgr = LayeredExclusionManager(ZenzicConfig(), docs_root=docs)
        assert mgr.should_exclude_file(docs / "eslint.config.mjs", docs)

    def test_l1a_lock_file_pattern_excluded(self, tmp_path: Path) -> None:
        """Any *.lock file is excluded by the system pattern."""
        from zenzic.core.exclusion import LayeredExclusionManager

        docs = tmp_path / "docs"
        docs.mkdir()
        mgr = LayeredExclusionManager(ZenzicConfig(), docs_root=docs)
        assert mgr.should_exclude_file(docs / "custom.lock", docs)

    def test_l1a_zenzic_local_override_excluded(self, tmp_path: Path) -> None:
        """.zenzic.local.toml is always excluded from asset checks."""
        from zenzic.core.exclusion import LayeredExclusionManager

        docs = tmp_path / "docs"
        docs.mkdir()
        mgr = LayeredExclusionManager(ZenzicConfig(), docs_root=docs)
        assert mgr.should_exclude_file(docs / ".zenzic.local.toml", docs)

    def test_l1a_shell_wrapper_pattern_excluded(self, tmp_path: Path) -> None:
        """Shell wrapper scripts are infrastructure and must be excluded."""
        from zenzic.core.exclusion import LayeredExclusionManager

        docs = tmp_path / "docs"
        docs.mkdir()
        mgr = LayeredExclusionManager(ZenzicConfig(), docs_root=docs)
        assert mgr.should_exclude_file(docs / "zenzic-action-wrapper.sh", docs)

    def test_l1b_adapter_metadata_excluded(self, tmp_path: Path) -> None:
        """Adapter metadata files (L1b) are excluded when passed to __init__."""
        from zenzic.core.exclusion import LayeredExclusionManager

        docs = tmp_path / "docs"
        docs.mkdir()
        mgr = LayeredExclusionManager(
            ZenzicConfig(),
            docs_root=docs,
            adapter_metadata_files=frozenset({"docusaurus.config.ts"}),
        )
        assert mgr.should_exclude_file(docs / "docusaurus.config.ts", docs)

    def test_l1b_non_metadata_file_not_excluded(self, tmp_path: Path) -> None:
        """A regular doc file is not accidentally excluded by the guardrails."""
        from zenzic.core.exclusion import LayeredExclusionManager

        docs = tmp_path / "docs"
        docs.mkdir()
        mgr = LayeredExclusionManager(
            ZenzicConfig(),
            docs_root=docs,
            adapter_metadata_files=frozenset({"docusaurus.config.ts"}),
        )
        assert not mgr.should_exclude_file(docs / "guide.md", docs)
