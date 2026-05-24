# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for Zenzic config loading and generator detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from zenzic.core.exceptions import ConfigurationError
from zenzic.models.config import SYSTEM_EXCLUDED_DIRS, ZenzicConfig


def test_load_config_default(tmp_path: Path) -> None:
    config, loaded = ZenzicConfig.load(tmp_path)
    assert config.docs_dir == Path("docs")
    assert config.snippet_min_lines == 1
    assert loaded is False


def test_load_config_custom(tmp_path: Path) -> None:
    toml_content = """
    docs_dir = "my_docs"
    snippet_min_lines = 5
    placeholder_max_words = 100
    placeholder_patterns = ["tbd", "wip"]
    """
    (tmp_path / ".zenzic.toml").write_text(toml_content)

    config, loaded = ZenzicConfig.load(tmp_path)
    assert config.docs_dir == Path("my_docs")
    assert config.snippet_min_lines == 5
    assert config.placeholder_max_words == 100
    assert config.placeholder_patterns == ["tbd", "wip"]
    # excluded_dirs not set in TOML → inherits system defaults
    assert "includes" in config.excluded_dirs
    assert ".git" in config.excluded_dirs
    assert ".venv" in config.excluded_dirs
    assert "node_modules" in config.excluded_dirs
    assert loaded is True


def test_excluded_dirs_always_contains_system_guardrails(tmp_path: Path) -> None:
    """User-defined excluded_dirs must never remove system guardrails (.git, .venv, etc.)."""
    toml_content = """\
    docs_dir = "docs"
    excluded_dirs = ["custom_stuff"]
    """
    (tmp_path / ".zenzic.toml").write_text(toml_content)

    config, _ = ZenzicConfig.load(tmp_path)
    # User entry is preserved
    assert "custom_stuff" in config.excluded_dirs
    # System guardrails are always present
    for guardrail in SYSTEM_EXCLUDED_DIRS:
        assert guardrail in config.excluded_dirs, f"System guardrail {guardrail!r} missing"


def test_load_config_invalid_toml_raises(tmp_path: Path) -> None:
    """A malformed .zenzic.toml must raise ConfigurationError — not silently fall back."""
    (tmp_path / ".zenzic.toml").write_text("invalid [ toml")
    with pytest.raises(ConfigurationError, match="syntax error"):
        ZenzicConfig.load(tmp_path)


def test_load_config_missing_file_uses_defaults(tmp_path: Path) -> None:
    """When .zenzic.toml does not exist, defaults are returned silently."""
    config, loaded = ZenzicConfig.load(tmp_path)
    assert config.docs_dir == Path("docs")
    assert loaded is False


def test_load_config_custom_rules(tmp_path: Path) -> None:
    """[[custom_rules]] entries are parsed and available as CustomRuleConfig instances."""
    toml_content = """
[[custom_rules]]
id = "ZZ001"
pattern = "internal\\\\.corp"
message = "Internal hostname in docs."
severity = "error"

[[custom_rules]]
id = "ZZ002"
pattern = "(?i)\\\\bDRAFT\\\\b"
message = "Remove DRAFT marker."
severity = "warning"
"""
    (tmp_path / ".zenzic.toml").write_text(toml_content)
    config, loaded = ZenzicConfig.load(tmp_path)
    assert len(config.custom_rules) == 2
    assert config.custom_rules[0].id == "ZZ001"
    assert config.custom_rules[0].severity == "error"
    assert config.custom_rules[1].id == "ZZ002"
    assert config.custom_rules[1].severity == "warning"
    assert loaded is True


def test_load_config_plugins_list(tmp_path: Path) -> None:
    """plugins = [...] is parsed from .zenzic.toml."""
    (tmp_path / ".zenzic.toml").write_text("plugins = ['no-internal-hostname', 'acme-style']\n")
    config, loaded = ZenzicConfig.load(tmp_path)
    assert config.plugins == ["no-internal-hostname", "acme-style"]
    assert loaded is True


def test_placeholder_patterns_compiled_on_init(tmp_path: Path) -> None:
    """placeholder_patterns_compiled is populated automatically from placeholder_patterns."""
    config = ZenzicConfig(placeholder_patterns=["todo", "wip"])
    assert len(config.placeholder_patterns_compiled) == 2
    assert config.placeholder_patterns_compiled[0].search("this is a TODO item")
    assert config.placeholder_patterns_compiled[1].search("WIP section")


# ─── pyproject.toml support (ISSUE #5) ───────────────────────────────────────


def test_load_config_from_pyproject_toml(tmp_path: Path) -> None:
    """[tool.zenzic] in pyproject.toml is used when .zenzic.toml is absent."""
    (tmp_path / "pyproject.toml").write_text(
        "[tool.zenzic]\ndocs_dir = 'my_docs'\nfail_under = 75\n"
    )
    config, loaded = ZenzicConfig.load(tmp_path)
    assert config.docs_dir == Path("my_docs")
    assert config.fail_under == 75
    assert loaded is True


def test_load_config_pyproject_build_context(tmp_path: Path) -> None:
    """[tool.zenzic.build_context] is parsed correctly from pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text(
        "[tool.zenzic]\n"
        "[tool.zenzic.build_context]\n"
        "engine = 'zensical'\n"
        "default_locale = 'en'\n"
        "locales = ['it']\n"
    )
    config, loaded = ZenzicConfig.load(tmp_path)
    assert config.build_context.engine == "zensical"
    assert config.build_context.locales == ["it"]
    assert loaded is True


def test_load_config_pyproject_custom_rules(tmp_path: Path) -> None:
    """[[tool.zenzic.custom_rules]] entries are parsed from pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text(
        "[tool.zenzic]\n"
        "[[tool.zenzic.custom_rules]]\n"
        'id = "ZZ-PY"\n'
        'pattern = "TODO"\n'
        'message = "No TODOs."\n'
        'severity = "warning"\n'
    )
    config, loaded = ZenzicConfig.load(tmp_path)
    assert len(config.custom_rules) == 1
    assert config.custom_rules[0].id == "ZZ-PY"
    assert config.custom_rules[0].severity == "warning"
    assert loaded is True


def test_load_config_pyproject_plugins_list(tmp_path: Path) -> None:
    """plugins list is parsed from [tool.zenzic] in pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text(
        "[tool.zenzic]\nplugins = ['no-internal-hostname', 'acme-style']\n"
    )
    config, loaded = ZenzicConfig.load(tmp_path)
    assert config.plugins == ["no-internal-hostname", "acme-style"]
    assert loaded is True


def test_load_config_zenzic_toml_wins_over_pyproject(tmp_path: Path) -> None:
    """.zenzic.toml takes priority over [tool.zenzic] in pyproject.toml."""
    (tmp_path / ".zenzic.toml").write_text("fail_under = 90\n")
    (tmp_path / "pyproject.toml").write_text("[tool.zenzic]\nfail_under = 42\n")
    config, loaded = ZenzicConfig.load(tmp_path)
    assert config.fail_under == 90  # .zenzic.toml wins
    assert loaded is True


def test_load_config_pyproject_without_tool_zenzic_uses_defaults(tmp_path: Path) -> None:
    """pyproject.toml without [tool.zenzic] falls back to built-in defaults."""
    (tmp_path / "pyproject.toml").write_text("[tool.other]\nfoo = 'bar'\n")
    config, loaded = ZenzicConfig.load(tmp_path)
    assert config.docs_dir == Path("docs")
    assert loaded is False


def test_load_config_invalid_pyproject_raises(tmp_path: Path) -> None:
    """A malformed pyproject.toml raises ConfigurationError — not silent fallback."""
    (tmp_path / "pyproject.toml").write_text("invalid [ toml")
    with pytest.raises(ConfigurationError, match="syntax error"):
        ZenzicConfig.load(tmp_path)


# ─── _apply_local_toml coverage ──────────────────────────────────────────────


def test_apply_local_toml_overrides_core_fields(tmp_path: Path) -> None:
    """[core] section in .zenzic.local.toml overrides docs_dir, strict, exit_zero, fail_under."""
    (tmp_path / ".zenzic.toml").write_text("docs_dir = 'docs'\n")
    (tmp_path / ".zenzic.local.toml").write_text(
        "[core]\ndocs_dir = 'local_docs'\nstrict = true\nexit_zero = true\nfail_under = 42\n"
    )
    config, _ = ZenzicConfig.load(tmp_path)
    assert config.docs_dir.as_posix() == "local_docs"
    assert config.strict is True
    assert config.exit_zero is True
    assert config.fail_under == 42


def test_apply_local_toml_overrides_build_context(tmp_path: Path) -> None:
    """[build_context] in .zenzic.local.toml is merged into config.build_context."""

    (tmp_path / ".zenzic.toml").write_text("docs_dir = 'docs'\n")
    (tmp_path / ".zenzic.local.toml").write_text(
        "[build_context]\nengine = 'mkdocs'\ndefault_locale = 'it'\n"
    )
    config, _ = ZenzicConfig.load(tmp_path)
    assert config.build_context.engine == "mkdocs"
    assert config.build_context.default_locale == "it"


def test_apply_local_toml_malformed_silently_skipped(tmp_path: Path) -> None:
    """A malformed .zenzic.local.toml is silently ignored — no exception raised."""
    (tmp_path / ".zenzic.toml").write_text("docs_dir = 'docs'\n")
    (tmp_path / ".zenzic.local.toml").write_text("invalid [ toml !!!")
    config, loaded = ZenzicConfig.load(tmp_path)
    assert config.docs_dir == Path("docs")
    assert loaded is True


def test_apply_local_toml_legacy_dev_toml_raises(tmp_path: Path) -> None:
    """.zenzic.dev.toml (legacy) must raise ConfigurationError."""
    (tmp_path / ".zenzic.dev.toml").write_text("# legacy\n")
    with pytest.raises(ConfigurationError, match="no longer supported"):
        ZenzicConfig.load(tmp_path)


def test_apply_local_toml_forbidden_patterns_merged(tmp_path: Path) -> None:
    """forbidden_patterns from [core], [governance], and top-level are merged additively."""
    (tmp_path / ".zenzic.toml").write_text("forbidden_patterns = ['secret-a']\n")
    (tmp_path / ".zenzic.local.toml").write_text(
        "forbidden_patterns = ['secret-b']\n[core]\nforbidden_patterns = ['secret-c']\n[governance]\nforbidden_patterns = ['secret-d']\n"
    )
    config, _ = ZenzicConfig.load(tmp_path)
    assert "secret-a" in config.forbidden_patterns
    assert "secret-b" in config.forbidden_patterns
    assert "secret-c" in config.forbidden_patterns
    assert "secret-d" in config.forbidden_patterns


def test_apply_local_toml_overrides_governance(tmp_path: Path) -> None:
    """[governance] in .zenzic.local.toml merges into config.governance."""
    (tmp_path / ".zenzic.toml").write_text(
        "docs_dir = 'docs'\n[governance]\nbrand_obsolescence = ['GlobalTerm']\n"
    )
    (tmp_path / ".zenzic.local.toml").write_text(
        "[governance]\nbrand_obsolescence = ['OldName']\nsuppression_cap = 10\n"
    )
    config, _ = ZenzicConfig.load(tmp_path)
    assert "OldName" in config.governance.brand_obsolescence
    assert "GlobalTerm" in config.governance.brand_obsolescence  # ADDITIVE: global preserved
    assert config.governance.suppression_cap == 10


def test_apply_local_toml_brand_obsolescence_additive(tmp_path: Path) -> None:
    """Local brand_obsolescence extends global — cannot remove global terms."""
    (tmp_path / ".zenzic.toml").write_text(
        "docs_dir = 'docs'\n[governance]\nbrand_obsolescence = ['TermA', 'TermB']\n"
    )
    (tmp_path / ".zenzic.local.toml").write_text("[governance]\nbrand_obsolescence = ['TermC']\n")
    config, _ = ZenzicConfig.load(tmp_path)
    assert "TermA" in config.governance.brand_obsolescence
    assert "TermB" in config.governance.brand_obsolescence
    assert "TermC" in config.governance.brand_obsolescence
    # No duplicates
    assert config.governance.brand_obsolescence.count("TermA") == 1


def test_apply_local_toml_overrides_i18n(tmp_path: Path) -> None:
    """[i18n] in .zenzic.local.toml merges into config.i18n."""
    (tmp_path / ".zenzic.toml").write_text("docs_dir = 'docs'\n")
    (tmp_path / ".zenzic.local.toml").write_text("[i18n]\nenabled = true\nbase_lang = 'fr'\n")
    config, _ = ZenzicConfig.load(tmp_path)
    assert config.i18n.enabled is True
    assert config.i18n.base_lang == "fr"


# ─── _build_from_data coverage ───────────────────────────────────────────────


def test_build_from_data_unknown_section_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Unknown dict-valued keys in .zenzic.toml emit a warning."""
    import logging

    (tmp_path / ".zenzic.toml").write_text("[unknown_section]\nfoo = 'bar'\n")
    with caplog.at_level(logging.WARNING, logger="zenzic"):
        ZenzicConfig.load(tmp_path)
    assert any("unknown section" in r.message for r in caplog.records)


def test_build_from_data_unknown_scalar_key_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Unknown scalar keys in .zenzic.toml emit a warning."""
    import logging

    (tmp_path / ".zenzic.toml").write_text("totally_unknown_key = 42\n")
    with caplog.at_level(logging.WARNING, logger="zenzic"):
        ZenzicConfig.load(tmp_path)
    assert any("unknown key" in r.message for r in caplog.records)


def test_build_from_data_legacy_obsolete_names_migrated(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """[project_metadata].obsolete_names is migrated to [governance].brand_obsolescence."""
    import logging

    (tmp_path / ".zenzic.toml").write_text(
        "[project_metadata]\nobsolete_names = ['OldBrand', 'AnotherOld']\n"
    )
    with caplog.at_level(logging.WARNING, logger="zenzic"):
        config, _ = ZenzicConfig.load(tmp_path)
    assert "OldBrand" in config.governance.brand_obsolescence
    assert "AnotherOld" in config.governance.brand_obsolescence
    assert any("Deprecated" in r.message for r in caplog.records)


def test_build_from_data_i18n_with_extra_sources(tmp_path: Path) -> None:
    """[i18n] with extra_sources is parsed correctly."""
    (tmp_path / ".zenzic.toml").write_text(
        "[i18n]\n"
        "enabled = true\n"
        "base_lang = 'en'\n"
        "[[i18n.extra_sources]]\n"
        "base_source = 'developers'\n"
        "[i18n.extra_sources.targets]\n"
        "it = 'i18n/it/docusaurus-plugin-content-docs-developers/current'\n"
    )
    config, _ = ZenzicConfig.load(tmp_path)
    assert config.i18n.enabled is True
    assert len(config.i18n.extra_sources) == 1
    assert config.i18n.extra_sources[0].base_source == Path("developers")
