# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for the Layered Exclusion system: VCSIgnoreParser + LayeredExclusionManager.

Test-driven development: these tests were written **before** the implementation.
"""

from __future__ import annotations

import time
from pathlib import Path

from zenzic.models.config import SYSTEM_EXCLUDED_DIRS, ZenzicConfig


# ══════════════════════════════════════════════════════════════════════════════
# VCSIgnoreParser
# ══════════════════════════════════════════════════════════════════════════════


class TestVCSIgnoreParserBasics:
    """Blank lines, comments, whitespace-only lines."""

    def test_empty_patterns(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser([], base_dir=None)
        assert not parser.is_excluded("anything.txt", is_dir=False)

    def test_comment_lines_ignored(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["# this is a comment", "*.log"], base_dir=None)
        assert not parser.is_excluded("README.md", is_dir=False)
        assert parser.is_excluded("debug.log", is_dir=False)

    def test_blank_lines_ignored(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["", "  ", "\t", "*.tmp"], base_dir=None)
        assert parser.is_excluded("file.tmp", is_dir=False)
        assert not parser.is_excluded("file.txt", is_dir=False)

    def test_whitespace_only_lines_ignored(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["   ", "*.bak"], base_dir=None)
        assert parser.is_excluded("old.bak", is_dir=False)


class TestVCSIgnoreParserGlob:
    """Star, double-star, question mark, character classes."""

    def test_single_star_matches_filename(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["*.log"], base_dir=None)
        assert parser.is_excluded("error.log", is_dir=False)
        assert parser.is_excluded("sub/dir/error.log", is_dir=False)
        assert not parser.is_excluded("error.txt", is_dir=False)

    def test_single_star_does_not_match_slash(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["dir/*"], base_dir=None)
        assert parser.is_excluded("dir/file.txt", is_dir=False)
        assert not parser.is_excluded("dir/sub/file.txt", is_dir=False)

    def test_double_star_matches_zero_or_more_dirs(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["**/logs"], base_dir=None)
        assert parser.is_excluded("logs", is_dir=True)
        assert parser.is_excluded("a/logs", is_dir=True)
        assert parser.is_excluded("a/b/c/logs", is_dir=True)

    def test_double_star_in_middle(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["a/**/z"], base_dir=None)
        assert parser.is_excluded("a/z", is_dir=False)
        assert parser.is_excluded("a/b/z", is_dir=False)
        assert parser.is_excluded("a/b/c/z", is_dir=False)
        assert not parser.is_excluded("x/a/z", is_dir=False)

    def test_trailing_double_star(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["abc/**"], base_dir=None)
        assert parser.is_excluded("abc/file.txt", is_dir=False)
        assert parser.is_excluded("abc/d/e/file.txt", is_dir=False)
        assert not parser.is_excluded("xyz/file.txt", is_dir=False)

    def test_question_mark_matches_single_non_slash_char(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["file?.txt"], base_dir=None)
        assert parser.is_excluded("file1.txt", is_dir=False)
        assert parser.is_excluded("fileA.txt", is_dir=False)
        assert not parser.is_excluded("file12.txt", is_dir=False)
        assert not parser.is_excluded("file/.txt", is_dir=False)

    def test_character_class(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["file[0-9].txt"], base_dir=None)
        assert parser.is_excluded("file5.txt", is_dir=False)
        assert not parser.is_excluded("fileA.txt", is_dir=False)

    def test_negated_character_class(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["file[!0-9].txt"], base_dir=None)
        assert parser.is_excluded("fileA.txt", is_dir=False)
        assert not parser.is_excluded("file5.txt", is_dir=False)


class TestVCSIgnoreParserNegation:
    """Negation via `!` prefix — last matching rule wins."""

    def test_negation_re_includes(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["*.log", "!important.log"], base_dir=None)
        assert parser.is_excluded("error.log", is_dir=False)
        assert not parser.is_excluded("important.log", is_dir=False)

    def test_double_negation_last_wins(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(
            ["*.log", "!important.log", "important.log"],
            base_dir=None,
        )
        assert parser.is_excluded("important.log", is_dir=False)

    def test_negation_only_no_prior_exclude(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["!keep.txt"], base_dir=None)
        # If nothing was excluded, negation has no exclude to undo.
        assert not parser.is_excluded("keep.txt", is_dir=False)
        assert not parser.is_excluded("other.txt", is_dir=False)

    def test_multiple_negations(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(
            ["*.md", "!README.md", "!CONTRIBUTING.md"],
            base_dir=None,
        )
        assert parser.is_excluded("random.md", is_dir=False)
        assert not parser.is_excluded("README.md", is_dir=False)
        assert not parser.is_excluded("CONTRIBUTING.md", is_dir=False)


class TestVCSIgnoreParserDirOnly:
    """Trailing `/` means the pattern matches directories only."""

    def test_dir_only_pattern_matches_dir(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["build/"], base_dir=None)
        assert parser.is_excluded("build", is_dir=True)
        assert not parser.is_excluded("build", is_dir=False)

    def test_dir_only_pattern_with_glob(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["temp*/"], base_dir=None)
        assert parser.is_excluded("temporary", is_dir=True)
        assert parser.is_excluded("temp123", is_dir=True)
        assert not parser.is_excluded("temp123", is_dir=False)


class TestVCSIgnoreParserAnchored:
    """Leading `/` anchors to the base dir — the pattern cannot float."""

    def test_anchored_pattern_matches_at_root_only(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["/TODO.md"], base_dir=None)
        assert parser.is_excluded("TODO.md", is_dir=False)
        assert not parser.is_excluded("docs/TODO.md", is_dir=False)

    def test_unanchored_pattern_floats(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["TODO.md"], base_dir=None)
        assert parser.is_excluded("TODO.md", is_dir=False)
        assert parser.is_excluded("docs/TODO.md", is_dir=False)

    def test_pattern_with_slash_in_middle_is_implicitly_anchored(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        # Per gitignore spec: a pattern with a slash (except trailing)
        # is matched relative to the base directory.
        parser = VCSIgnoreParser(["doc/frotz/"], base_dir=None)
        assert parser.is_excluded("doc/frotz", is_dir=True)
        assert not parser.is_excluded("a/doc/frotz", is_dir=True)


class TestVCSIgnoreParserEdgeCases:
    """Escaped characters, BOM, spaces in patterns."""

    def test_escaped_hash_is_literal(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["\\#file.txt"], base_dir=None)
        assert parser.is_excluded("#file.txt", is_dir=False)
        assert not parser.is_excluded("file.txt", is_dir=False)

    def test_escaped_exclamation_is_literal(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["\\!important.txt"], base_dir=None)
        assert parser.is_excluded("!important.txt", is_dir=False)

    def test_trailing_spaces_stripped(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["*.log   "], base_dir=None)
        assert parser.is_excluded("test.log", is_dir=False)

    def test_escaped_trailing_space_preserved(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["foo\\ "], base_dir=None)
        assert parser.is_excluded("foo ", is_dir=False)
        assert not parser.is_excluded("foo", is_dir=False)

    def test_from_file_missing_returns_empty(self, tmp_path: Path) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser.from_file(tmp_path / "nonexistent")
        assert not parser.is_excluded("anything", is_dir=False)

    def test_from_file_reads_patterns(self, tmp_path: Path) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n__pycache__/\n# comment\n")
        parser = VCSIgnoreParser.from_file(gitignore)
        assert parser.is_excluded("module.pyc", is_dir=False)
        assert parser.is_excluded("__pycache__", is_dir=True)
        assert not parser.is_excluded("module.py", is_dir=False)

    def test_from_file_bom_prefix(self, tmp_path: Path) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        gitignore = tmp_path / ".gitignore"
        gitignore.write_bytes(b"\xef\xbb\xbf*.log\n")
        parser = VCSIgnoreParser.from_file(gitignore)
        assert parser.is_excluded("test.log", is_dir=False)

    def test_empty_file(self, tmp_path: Path) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("")
        parser = VCSIgnoreParser.from_file(gitignore)
        assert not parser.is_excluded("anything", is_dir=False)


class TestVCSIgnoreParserPerformance:
    """Pre-compiled regexes must handle large pattern sets efficiently."""

    def test_500_patterns_10k_paths(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        patterns = [f"dir{i}/*.log" for i in range(500)]
        parser = VCSIgnoreParser(patterns, base_dir=None)

        paths = [f"dir{i % 500}/file{i}.log" for i in range(10_000)]
        start = time.perf_counter()
        for p in paths:
            parser.is_excluded(p, is_dir=False)
        elapsed_ms = (time.perf_counter() - start) * 1000
        # Must complete in under 500ms (generous — target <100ms)
        assert elapsed_ms < 500, f"Pattern matching took {elapsed_ms:.1f}ms (limit 500ms)"


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


# ══════════════════════════════════════════════════════════════════════════════
# Mutant Killers
# ══════════════════════════════════════════════════════════════════════════════


class TestMutantKillers:
    """Tests designed to kill specific mutants."""

    def test_negation_flip_kills_mutant(self) -> None:
        """A mutant that flips negation logic must fail here."""
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["*.log", "!keep.log"], base_dir=None)
        assert parser.is_excluded("error.log", is_dir=False) is True
        assert parser.is_excluded("keep.log", is_dir=False) is False

    def test_dir_only_false_positive_kills_mutant(self) -> None:
        """A mutant that ignores dir-only trailing slash must fail here."""
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["build/"], base_dir=None)
        assert parser.is_excluded("build", is_dir=True) is True
        assert parser.is_excluded("build", is_dir=False) is False

    def test_double_star_degradation_kills_mutant(self) -> None:
        """A mutant that treats ** as * must fail here."""
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["a/**/z"], base_dir=None)
        assert parser.is_excluded("a/b/c/z", is_dir=False) is True
        # If ** degrades to *, this would fail because * can't match /
        parser2 = VCSIgnoreParser(["a/*/z"], base_dir=None)
        assert parser2.is_excluded("a/b/c/z", is_dir=False) is False

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


# ══════════════════════════════════════════════════════════════════════════════
# Path Traversal Safety
# ══════════════════════════════════════════════════════════════════════════════


class TestPathTraversalSafety:
    """Gitignore patterns must not enable path traversal."""

    def test_dotdot_pattern_rejected(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        # A pattern with ../ should not match files outside base
        parser = VCSIgnoreParser(["../secret"], base_dir=None)
        assert not parser.is_excluded("../secret", is_dir=False)

    def test_absolute_path_pattern_rejected(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["/etc/passwd"], base_dir=None)
        # Anchored to base_dir root, not filesystem root
        assert parser.is_excluded("etc/passwd", is_dir=False)
        # Should not match actual /etc/passwd — rel_path never starts with /
        assert not parser.is_excluded("/etc/passwd", is_dir=False)

    def test_gitignore_with_dotdot_harmless(self, tmp_path: Path) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("../escape\n")
        parser = VCSIgnoreParser.from_file(gitignore)
        # Pattern with ../ is inherently un-matchable since rel_path is within base
        assert not parser.is_excluded("../escape", is_dir=False)

    def test_base_dir_containment(self, tmp_path: Path) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.secret\n")
        parser = VCSIgnoreParser.from_file(gitignore)
        # Only relative paths within base_dir should be checked
        assert parser.is_excluded("data.secret", is_dir=False)
        assert parser.is_excluded("sub/data.secret", is_dir=False)

    def test_symlink_not_resolved_by_parser(self) -> None:
        from zenzic.core.exclusion import VCSIgnoreParser

        parser = VCSIgnoreParser(["*.md"], base_dir=None)
        # Parser works on string paths — it doesn't touch the filesystem
        assert parser.is_excluded("link.md", is_dir=False)


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
