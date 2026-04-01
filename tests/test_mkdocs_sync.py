# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""MkDocs 1.6.x compatibility tests for MkDocsAdapter parsing behavior."""

from __future__ import annotations

import pickle
from pathlib import Path

import yaml

from zenzic.core.adapter import (
    MkDocsAdapter,
    _extract_i18n_locale_dirs,
    _extract_i18n_locale_patterns,
    _load_doc_config,
)
from zenzic.core.adapters._mkdocs import _extract_i18n_reconfigure_material
from zenzic.models.config import BuildContext


def test_i18n_extraction_supports_plugins_mapping_syntax() -> None:
    """MkDocs alternate plugins syntax (mapping) must be parsed correctly."""
    cfg = {
        "plugins": {
            "search": {},
            "i18n": {
                "docs_structure": "suffix",
                "reconfigure_material": True,
                "languages": [
                    {"locale": "en", "default": True},
                    {"locale": "it"},
                    {"locale": "fr"},
                ],
            },
        }
    }

    assert _extract_i18n_locale_patterns(cfg) == {"*.it.md", "*.fr.md"}
    # docs_structure=suffix -> no folder locale dirs
    assert _extract_i18n_locale_dirs(cfg) == set()
    # reconfigure_material only meaningful for folder mode
    assert _extract_i18n_reconfigure_material(cfg) is False


def test_i18n_folder_extraction_supports_plugins_mapping_syntax() -> None:
    cfg = {
        "plugins": {
            "i18n": {
                "docs_structure": "folder",
                "reconfigure_material": True,
                "languages": [
                    {"locale": "en", "default": True},
                    {"locale": "it"},
                    {"locale": "fr"},
                ],
            }
        }
    }

    assert _extract_i18n_locale_dirs(cfg) == {"it", "fr"}
    assert _extract_i18n_reconfigure_material(cfg) is True


def test_permissive_loader_handles_env_and_relative_tags(tmp_path: Path) -> None:
    """!ENV and !relative tags should parse without collapsing config to {}."""
    mkdocs_yml = tmp_path / "mkdocs.yml"
    mkdocs_yml.write_text(
        "\n".join(
            [
                "site_name: !ENV [SITE_NAME, Demo Site]",
                "use_directory_urls: !ENV [USE_DIR_URLS, true]",
                "plugins:",
                "  i18n:",
                "    docs_structure: folder",
                "    reconfigure_material: true",
                "    languages:",
                "      - locale: en",
                "        default: true",
                "      - locale: it",
                "markdown_extensions:",
                "  - pymdownx.snippets:",
                "      base_path: !relative $config_dir/includes",
            ]
        ),
        encoding="utf-8",
    )

    cfg = _load_doc_config(tmp_path)

    assert isinstance(cfg, dict)
    assert cfg.get("site_name") == "Demo Site"
    # !relative should remain plain string data for static analysis.
    base_path = cfg["markdown_extensions"][0]["pymdownx.snippets"]["base_path"]
    assert isinstance(base_path, str)
    assert base_path == "$config_dir/includes"


def test_mkdocs_adapter_is_pickleable_for_parallel_execution() -> None:
    """ProcessPool dispatch requires adapter state to be pickleable."""
    cfg = {
        "use_directory_urls": False,
        "nav": [{"Home": "index.md"}, {"Guide": "guide.md"}],
        "plugins": {
            "i18n": {
                "docs_structure": "folder",
                "languages": [
                    {"locale": "en", "default": True},
                    {"locale": "it"},
                ],
            }
        },
    }
    adapter = MkDocsAdapter(BuildContext(), Path("/docs"), cfg)

    data = pickle.dumps(adapter)
    restored = pickle.loads(data)

    assert isinstance(restored, MkDocsAdapter)
    assert restored.map_url(Path("guide.md")) == "/guide.html"
    assert restored.classify_route(Path("it/index.md"), frozenset({"index.md"})) == "REACHABLE"


def test_loader_remains_tolerant_of_unknown_custom_tags(tmp_path: Path) -> None:
    """Unknown tags from third-party plugins must not crash parsing."""
    mkdocs_yml = tmp_path / "mkdocs.yml"
    mkdocs_yml.write_text(
        "\n".join(
            [
                "site_name: Demo",
                "extra:",
                "  custom: !CUSTOM_TAG something",
                "plugins:",
                "  - search",
            ]
        ),
        encoding="utf-8",
    )

    cfg = _load_doc_config(tmp_path)
    assert cfg.get("site_name") == "Demo"
    assert cfg.get("extra", {}).get("custom") == "something"

    # sanity: produced YAML-compatible dict
    yaml.safe_dump(cfg)
