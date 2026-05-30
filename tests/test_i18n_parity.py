# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Z602 I18N_PARITY — unit + Hypothesis stress tests.

Validates the language-agnostic parity scanner introduced in v0.5.x
(v0.7.0 / "Quarzo").  Covers:

* Missing target mirrors are flagged (single + multi-language).
* ``i18n-ignore: true`` frontmatter escape hatch suppresses findings.
* ``require_frontmatter_parity`` keys raise warnings on empty translations.
* ``extra_sources`` (multi-instance Docusaurus) aggregates findings.
* Deep directory nesting and unicode/emoji filenames are handled (D13).
* Disabled config returns no findings.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from zenzic.core.exclusion import LayeredExclusionManager
from zenzic.core.scanner import find_i18n_parity
from zenzic.models.config import SYSTEM_EXCLUDED_DIRS, I18nConfig, I18nSource, ZenzicConfig


def _write(path: Path, body: str = "stub\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _fm(title: str | None = None, description: str | None = None, ignore: bool = False) -> str:
    lines = ["---"]
    if title is not None:
        lines.append(f'title: "{title}"')
    if description is not None:
        lines.append(f'description: "{description}"')
    if ignore:
        lines.append("i18n-ignore: true")
    lines.append("---\n")
    return "\n".join(lines) + "Body\n"


def _run_i18n_parity(repo_root: Path, config: ZenzicConfig):
    return find_i18n_parity(
        repo_root,
        config=config,
        exclusion_manager_factory=lambda docs_root: LayeredExclusionManager(
            config,
            repo_root=repo_root,
            docs_root=docs_root,
        ),
    )


# ── Smoke ────────────────────────────────────────────────────────────────────


def test_disabled_returns_empty(tmp_path: Path) -> None:
    config = ZenzicConfig(i18n=I18nConfig(enabled=False))
    assert _run_i18n_parity(tmp_path, config) == []


def test_no_targets_returns_empty(tmp_path: Path) -> None:
    config = ZenzicConfig(i18n=I18nConfig(enabled=True, targets={}))
    assert _run_i18n_parity(tmp_path, config) == []


# ── Missing mirror ──────────────────────────────────────────────────────────


def test_missing_target_mirror_flagged(tmp_path: Path) -> None:
    _write(tmp_path / "docs/index.mdx", _fm(title="Home"))
    _write(tmp_path / "docs/guide.mdx", _fm(title="Guide"))
    _write(tmp_path / "i18n/it/docs/index.mdx", _fm(title="Casa"))
    # guide.mdx has NO Italian mirror

    config = ZenzicConfig(
        i18n=I18nConfig(
            enabled=True,
            base_source=Path("docs"),
            targets={"it": Path("i18n/it/docs")},
            require_frontmatter_parity=[],
        )
    )
    issues = _run_i18n_parity(tmp_path, config)
    assert len(issues) == 1
    assert issues[0].issue_type == "missing_mirror"
    assert issues[0].target_lang == "it"
    assert issues[0].file_path.name == "guide.mdx"


def test_multi_language_aggregates_per_lang(tmp_path: Path) -> None:
    _write(tmp_path / "docs/a.mdx", _fm(title="A"))
    # IT + ES present, FR missing
    _write(tmp_path / "i18n/it/docs/a.mdx", _fm(title="A-IT"))
    _write(tmp_path / "i18n/es/docs/a.mdx", _fm(title="A-ES"))

    config = ZenzicConfig(
        i18n=I18nConfig(
            enabled=True,
            base_source=Path("docs"),
            targets={
                "it": Path("i18n/it/docs"),
                "es": Path("i18n/es/docs"),
                "fr": Path("i18n/fr/docs"),
            },
            require_frontmatter_parity=[],
        )
    )
    issues = _run_i18n_parity(tmp_path, config)
    assert len(issues) == 1
    assert issues[0].target_lang == "fr"


# ── Frontmatter parity ──────────────────────────────────────────────────────


def test_missing_translated_title_warning(tmp_path: Path) -> None:
    _write(tmp_path / "docs/a.mdx", _fm(title="Home", description="Welcome"))
    _write(tmp_path / "i18n/it/docs/a.mdx", _fm(description="Benvenuto"))  # title missing

    config = ZenzicConfig(
        i18n=I18nConfig(
            enabled=True,
            base_source=Path("docs"),
            targets={"it": Path("i18n/it/docs")},
            require_frontmatter_parity=["title", "description"],
        )
    )
    issues = _run_i18n_parity(tmp_path, config)
    assert len(issues) == 1
    assert issues[0].issue_type == "missing_frontmatter"
    assert issues[0].missing_key == "title"


def test_frontmatter_parity_skipped_when_base_key_absent(tmp_path: Path) -> None:
    # If base has no description, target is allowed to omit it.
    _write(tmp_path / "docs/a.mdx", _fm(title="Home"))
    _write(tmp_path / "i18n/it/docs/a.mdx", _fm(title="Casa"))

    config = ZenzicConfig(
        i18n=I18nConfig(
            enabled=True,
            base_source=Path("docs"),
            targets={"it": Path("i18n/it/docs")},
            require_frontmatter_parity=["title", "description"],
        )
    )
    assert _run_i18n_parity(tmp_path, config) == []


# ── Escape hatch ────────────────────────────────────────────────────────────


def test_i18n_ignore_skips_file(tmp_path: Path) -> None:
    _write(tmp_path / "docs/draft.mdx", _fm(title="Draft", ignore=True))
    # No IT mirror, but i18n-ignore should suppress finding.

    config = ZenzicConfig(
        i18n=I18nConfig(
            enabled=True,
            base_source=Path("docs"),
            targets={"it": Path("i18n/it/docs")},
            require_frontmatter_parity=[],
        )
    )
    assert _run_i18n_parity(tmp_path, config) == []


def test_i18n_discovery_skips_venv_sources(tmp_path: Path) -> None:
    _write(
        tmp_path
        / ".venv"
        / "lib"
        / "python3.12"
        / "site-packages"
        / "zenzic"
        / "examples"
        / "matrix"
        / "README.mdx",
        _fm(title="Leaky fixture"),
    )

    config = ZenzicConfig(
        i18n=I18nConfig(
            enabled=True,
            base_source=Path("."),
            targets={"it": Path("i18n/it")},
            require_frontmatter_parity=[],
        )
    )

    assert _run_i18n_parity(tmp_path, config) == []


# ── extra_sources (multi-instance) ──────────────────────────────────────────


def test_extra_sources_aggregated(tmp_path: Path) -> None:
    _write(tmp_path / "docs/index.mdx", _fm(title="User"))
    _write(tmp_path / "i18n/it/docs/index.mdx", _fm(title="Utente"))
    _write(tmp_path / "developers/index.mdx", _fm(title="Dev"))
    # IT mirror missing for /developers — must be flagged.

    config = ZenzicConfig(
        i18n=I18nConfig(
            enabled=True,
            base_source=Path("docs"),
            targets={"it": Path("i18n/it/docs")},
            extra_sources=[
                I18nSource(
                    base_source=Path("developers"),
                    targets={"it": Path("i18n/it/developers")},
                )
            ],
            require_frontmatter_parity=[],
        )
    )
    issues = _run_i18n_parity(tmp_path, config)
    assert len(issues) == 1
    assert issues[0].file_path.parent.name == "developers"


# ── Hypothesis stress (D13) ─────────────────────────────────────────────────

# Restrict to filesystem-safe characters; the goal is to stress nesting and
# unicode, not to fight platform-specific path rules.
_PATH_SEGMENT = st.text(
    alphabet=st.characters(
        whitelist_categories=("Ll", "Lu", "Lo", "Nd"),
        min_codepoint=0x20,
        max_codepoint=0x024F,  # Latin Extended; covers café/résumé without surrogate pairs
    ),
    min_size=1,
    max_size=12,
).filter(
    lambda s: s not in (".", "..")
    and "/" not in s
    and "\\" not in s
    and s not in SYSTEM_EXCLUDED_DIRS
)


@settings(
    max_examples=40,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
@given(
    depth=st.integers(min_value=1, max_value=6),
    segments=st.lists(_PATH_SEGMENT, min_size=1, max_size=6),
)
def test_deep_nesting_detects_missing_mirror(
    tmp_path_factory: pytest.TempPathFactory,
    depth: int,
    segments: list[str],
) -> None:
    """Nested mirrors of arbitrary depth must still be diff-able."""
    root = tmp_path_factory.mktemp("zenzic-i18n-prop")
    nested_parts = segments[:depth]
    rel_dir = Path(*nested_parts)
    base_file = root / "docs" / rel_dir / "page.mdx"
    _write(base_file, _fm(title="T"))
    # IT mirror intentionally missing — Z602 must fire exactly once.

    config = ZenzicConfig(
        i18n=I18nConfig(
            enabled=True,
            base_source=Path("docs"),
            targets={"it": Path("i18n/it/docs")},
            require_frontmatter_parity=[],
        )
    )
    issues = _run_i18n_parity(root, config)
    assert len(issues) == 1
    assert issues[0].issue_type == "missing_mirror"
    assert issues[0].target_lang == "it"
