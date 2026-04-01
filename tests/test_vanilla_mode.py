# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for the Adapter Factory: VanillaAdapter, engine routing, and
Zensical Native Enforcement.

Covers:
* VanillaAdapter unit behaviour
* get_adapter engine routing (Multi-Engine Matrix)
* Zensical Identity Violation — ConfigurationError when zensical.toml is absent
* find_orphans integration for vanilla and Zensical repos
"""

from __future__ import annotations

from pathlib import Path

import pytest

from zenzic.core.adapter import (
    BaseAdapter,
    MkDocsAdapter,
    VanillaAdapter,
    ZensicalAdapter,
    get_adapter,
)
from zenzic.core.exceptions import ConfigurationError
from zenzic.core.scanner import find_orphans
from zenzic.models.config import BuildContext, ZenzicConfig


# ── Helpers ───────────────────────────────────────────────────────────────────


def _mkdocs(repo: Path, nav: list[str] | None = None) -> None:
    """Write a minimal mkdocs.yml into *repo*."""
    nav_lines = "\n".join(f"  - '{p}'" for p in (nav or ["index.md"]))
    (repo / "mkdocs.yml").write_text(f"site_name: Test\nnav:\n{nav_lines}\n")


def _zensical(repo: Path, nav: list[str] | None = None) -> None:
    """Write a minimal zensical.toml into *repo*."""
    nav_items = "\n".join(f'  "{p}",' for p in (nav or ["index.md"]))
    (repo / "zensical.toml").write_text(
        f'[project]\nsite_name = "Test"\ndocs_dir = "docs"\nnav = [\n{nav_items}\n]\n'
    )


# ── VanillaAdapter unit tests ─────────────────────────────────────────────────


def test_vanilla_adapter_satisfies_base_adapter_protocol() -> None:
    assert isinstance(VanillaAdapter(), BaseAdapter)


def test_vanilla_is_locale_dir_always_false() -> None:
    a = VanillaAdapter()
    for code in ("it", "fr", "en", ""):
        assert not a.is_locale_dir(code)


def test_vanilla_resolve_asset_always_none(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    assert VanillaAdapter().resolve_asset(docs / "it" / "logo.png", docs) is None


def test_vanilla_is_shadow_of_nav_page_always_false() -> None:
    nav = frozenset({"index.md", "guide/start.md"})
    a = VanillaAdapter()
    assert not a.is_shadow_of_nav_page(Path("it/index.md"), nav)
    assert not a.is_shadow_of_nav_page(Path("fr/guide/start.md"), nav)


def test_vanilla_get_ignored_patterns_empty() -> None:
    assert VanillaAdapter().get_ignored_patterns() == set()


def test_vanilla_get_nav_paths_empty() -> None:
    assert VanillaAdapter().get_nav_paths() == frozenset()


@pytest.mark.parametrize("filename", ["guide.it.md", "page.fr.md", "index.pt.md"])
def test_vanilla_suffix_files_not_treated_as_translations(filename: str) -> None:
    locale = filename.rsplit(".", 2)[1]
    assert not VanillaAdapter().is_locale_dir(locale)
    assert VanillaAdapter().get_ignored_patterns() == set()


# ── get_adapter factory: Multi-Engine Matrix ──────────────────────────────────


def test_get_adapter_no_config_no_locales_returns_vanilla(tmp_path: Path) -> None:
    """Test C: no config files + no locales → VanillaAdapter."""
    adapter = get_adapter(BuildContext(), tmp_path / "docs", tmp_path)
    assert isinstance(adapter, VanillaAdapter)


def test_get_adapter_mkdocs_engine_with_config(tmp_path: Path) -> None:
    """Test A: engine='mkdocs' + mkdocs.yml → MkDocsAdapter."""
    _mkdocs(tmp_path)
    context = BuildContext(engine="mkdocs", locales=["it"])
    adapter = get_adapter(context, tmp_path / "docs", tmp_path)
    assert isinstance(adapter, MkDocsAdapter)
    assert not isinstance(adapter, ZensicalAdapter)


def test_get_adapter_zensical_engine_with_config(tmp_path: Path) -> None:
    """Test B: engine='zensical' + zensical.toml → ZensicalAdapter."""
    _zensical(tmp_path)
    context = BuildContext(engine="zensical", locales=["it"])
    adapter = get_adapter(context, tmp_path / "docs", tmp_path)
    assert isinstance(adapter, ZensicalAdapter)
    assert isinstance(adapter, BaseAdapter)


def test_get_adapter_locales_no_config_uses_engine(tmp_path: Path) -> None:
    """Explicit locales declared in zenzic.toml → routes by engine without doc_config."""
    _mkdocs(tmp_path)
    assert isinstance(
        get_adapter(BuildContext(engine="mkdocs", locales=["it"]), tmp_path / "docs", tmp_path),
        MkDocsAdapter,
    )


def test_get_adapter_unknown_engine_falls_back_to_vanilla(tmp_path: Path) -> None:
    """An unrecognised engine string → VanillaAdapter (no entry point registered)."""
    _mkdocs(tmp_path)
    context = BuildContext(engine="hugo", locales=["it"])
    adapter = get_adapter(context, tmp_path / "docs", tmp_path)
    # Dynamic factory: unknown engines have no entry point → VanillaAdapter.
    assert isinstance(adapter, VanillaAdapter)


# ── Zensical Identity Violation (enforcement) ─────────────────────────────────


def test_zensical_engine_without_zensical_toml_raises(tmp_path: Path) -> None:
    """Identity Violation: engine='zensical' + no zensical.toml → ConfigurationError."""
    context = BuildContext(engine="zensical")
    with pytest.raises(ConfigurationError, match="zensical.toml is missing"):
        get_adapter(context, tmp_path / "docs", tmp_path)


def test_zensical_engine_mkdocs_yml_present_but_no_zensical_toml_raises(
    tmp_path: Path,
) -> None:
    """mkdocs.yml present is NOT a substitute — only zensical.toml counts."""
    _mkdocs(tmp_path)  # mkdocs.yml exists, but no zensical.toml
    context = BuildContext(engine="zensical")
    with pytest.raises(ConfigurationError):
        get_adapter(context, tmp_path / "docs", tmp_path)


def test_zensical_engine_with_zensical_toml_does_not_raise(tmp_path: Path) -> None:
    """No error when both engine='zensical' and zensical.toml are present."""
    _zensical(tmp_path)
    adapter = get_adapter(BuildContext(engine="zensical"), tmp_path / "docs", tmp_path)
    assert isinstance(adapter, ZensicalAdapter)


def test_zensical_adapter_nav_paths_from_toml(tmp_path: Path) -> None:
    """ZensicalAdapter.get_nav_paths reads [project].nav from zensical.toml."""
    _zensical(tmp_path, nav=["index.md", "guide/start.md", "about.md"])
    adapter = get_adapter(BuildContext(engine="zensical"), tmp_path / "docs", tmp_path)
    assert isinstance(adapter, ZensicalAdapter)
    assert adapter.get_nav_paths() == frozenset({"index.md", "guide/start.md", "about.md"})


# ── find_orphans integration ──────────────────────────────────────────────────


def test_find_orphans_no_config_returns_empty(tmp_path: Path) -> None:
    """Vanilla repo (no mkdocs.yml, no zensical.toml) → no orphan check → []."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home")
    (docs / "orphan.md").write_text("# Orphan")
    assert find_orphans(tmp_path) == []


def test_find_orphans_zensical_repo(tmp_path: Path) -> None:
    """Zensical repo with zensical.toml → orphan check uses TOML nav."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home")
    (docs / "orphan.md").write_text("# Unlisted")
    _zensical(tmp_path, nav=["index.md"])

    config = ZenzicConfig.model_validate(
        {"docs_dir": "docs", "build_context": {"engine": "zensical"}}
    )
    orphans = find_orphans(tmp_path, config)
    assert Path("orphan.md") in orphans
    assert Path("index.md") not in orphans


def test_find_orphans_vanilla_suffix_file_appears_as_orphan(tmp_path: Path) -> None:
    """In vanilla mode, guide.it.md is an ordinary page — not silently excluded."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (tmp_path / "mkdocs.yml").write_text("site_name: T\nnav:\n  - Home: index.md\n")
    (docs / "index.md").write_text("# Home")
    (docs / "guide.it.md").write_text("# Guide IT")

    orphans = find_orphans(tmp_path, ZenzicConfig())
    assert Path("guide.it.md") in orphans
