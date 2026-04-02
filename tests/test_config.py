# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for Zenzic config loading and generator detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from zenzic.core.exceptions import ConfigurationError
from zenzic.models.config import ZenzicConfig


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
    (tmp_path / "zenzic.toml").write_text(toml_content)

    config, loaded = ZenzicConfig.load(tmp_path)
    assert config.docs_dir == Path("my_docs")
    assert config.snippet_min_lines == 5
    assert config.placeholder_max_words == 100
    assert config.placeholder_patterns == ["tbd", "wip"]
    assert config.excluded_dirs == ["includes", "assets", "stylesheets", "overrides", "hooks"]
    assert loaded is True


def test_load_config_invalid_toml_raises(tmp_path: Path) -> None:
    """A malformed zenzic.toml must raise ConfigurationError — not silently fall back."""
    (tmp_path / "zenzic.toml").write_text("invalid [ toml")
    with pytest.raises(ConfigurationError, match="syntax error"):
        ZenzicConfig.load(tmp_path)


def test_load_config_missing_file_uses_defaults(tmp_path: Path) -> None:
    """When zenzic.toml does not exist, defaults are returned silently."""
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
    (tmp_path / "zenzic.toml").write_text(toml_content)
    config, loaded = ZenzicConfig.load(tmp_path)
    assert len(config.custom_rules) == 2
    assert config.custom_rules[0].id == "ZZ001"
    assert config.custom_rules[0].severity == "error"
    assert config.custom_rules[1].id == "ZZ002"
    assert config.custom_rules[1].severity == "warning"
    assert loaded is True


def test_placeholder_patterns_compiled_on_init(tmp_path: Path) -> None:
    """placeholder_patterns_compiled is populated automatically from placeholder_patterns."""
    config = ZenzicConfig(placeholder_patterns=["todo", "wip"])
    assert len(config.placeholder_patterns_compiled) == 2
    assert config.placeholder_patterns_compiled[0].search("this is a TODO item")
    assert config.placeholder_patterns_compiled[1].search("WIP section")


# ─── pyproject.toml support (ISSUE #5) ───────────────────────────────────────


def test_load_config_from_pyproject_toml(tmp_path: Path) -> None:
    """[tool.zenzic] in pyproject.toml is used when zenzic.toml is absent."""
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


def test_load_config_zenzic_toml_wins_over_pyproject(tmp_path: Path) -> None:
    """zenzic.toml takes priority over [tool.zenzic] in pyproject.toml."""
    (tmp_path / "zenzic.toml").write_text("fail_under = 90\n")
    (tmp_path / "pyproject.toml").write_text("[tool.zenzic]\nfail_under = 42\n")
    config, loaded = ZenzicConfig.load(tmp_path)
    assert config.fail_under == 90  # zenzic.toml wins
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
