# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Empirical reproduction script — Phase 85: False Trust Bug (Z104 cross-plugin).

Tests the following invariants after the instance-aware routing fix:

    REPRO-A  map_url() routes extra content root files to the plugin's own
             routeBasePath, not the default docs prefix.
             developers/explanation/foo.mdx → /developers/explanation/foo/
             (NOT /docs/developers/explanation/foo/).

    REPRO-B  A valid link from docs to an existing /developers/ page passes
             with zero findings (no Z104, no false positive).

    REPRO-C  A broken link to a non-existent /developers/ page raises Z104.
             This was the False Trust Bug: before the fix, /developers/ was
             absent from _scanned_vsm_prefixes, causing an unconditional bypass.

    REPRO-D  A _zenzic_core directory at repo root produces zero findings
             after SYSTEM_EXCLUDED_DIRS hardening (ZRT-010 sovereign parity).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from zenzic.core.adapters._docusaurus import DocusaurusAdapter
from zenzic.core.exclusion import LayeredExclusionManager
from zenzic.core.validator import validate_links_structured
from zenzic.models.config import SYSTEM_EXCLUDED_DIRS, BuildContext, ZenzicConfig


# ── Shared fixture ─────────────────────────────────────────────────────────────


@pytest.fixture()
def docusaurus_project(tmp_path: Path) -> dict[str, Path]:
    """Minimal Docusaurus project with a sibling 'developers' plugin instance.

    Structure::

        repo_root/
          docs/
            guide.md          ← source of cross-plugin links
          developers/
            existing-page.md  ← real page, must resolve to /developers/existing-page/
          i18n/it/docusaurus-plugin-content-docs-developers/current/
                              ← triggers adapter detection of the instance
    """
    repo_root = tmp_path
    docs = repo_root / "docs"
    docs.mkdir()

    developers = repo_root / "developers"
    developers.mkdir()

    (developers / "existing-page.md").write_text(
        "# Existing Developer Page\n\nThis page exists.\n",
        encoding="utf-8",
    )

    i18n_developers = (
        repo_root / "i18n" / "it" / "docusaurus-plugin-content-docs-developers" / "current"
    )
    i18n_developers.mkdir(parents=True)

    return {"repo_root": repo_root, "docs": docs, "developers": developers}


# ── REPRO-A: map_url() instance-aware routing ──────────────────────────────────


class TestReproA_MapUrl:
    """REPRO-A — map_url() must use the plugin's routeBasePath for extra content roots."""

    def test_developers_file_maps_to_plugin_prefix(
        self, docusaurus_project: dict[str, Path]
    ) -> None:
        """developers/existing-page.md must map to /developers/existing-page/, not /docs/..."""
        repo_root = docusaurus_project["repo_root"]
        docs = docusaurus_project["docs"]

        adapter = DocusaurusAdapter.from_repo(BuildContext(engine="docusaurus"), docs, repo_root)

        # Simulate how build_vsm constructs `rel` for extra content root files:
        # prefix="developers", inner=Path("existing-page.md")
        rel = Path("developers") / "existing-page.md"
        url = adapter.get_route_info(rel).canonical_url

        assert url == "/developers/existing-page/", (
            f"False Trust Bug: expected '/developers/existing-page/', got '{url}'. "
            f"map_url() must use the plugin's routeBasePath, not the default docs prefix."
        )

    def test_default_docs_file_unaffected(self, docusaurus_project: dict[str, Path]) -> None:
        """A normal docs file must still route under /docs/ (no regression)."""
        repo_root = docusaurus_project["repo_root"]
        docs = docusaurus_project["docs"]

        adapter = DocusaurusAdapter.from_repo(BuildContext(engine="docusaurus"), docs, repo_root)

        url = adapter.get_route_info(Path("guide.md")).canonical_url
        assert url == "/docs/guide/", (
            f"Regression: docs/guide.md must still map to /docs/guide/, got '{url}'."
        )


# ── REPRO-B: valid cross-plugin link — no false positive ──────────────────────


class TestReproB_ValidLink:
    """REPRO-B — a link to an existing /developers/ route must produce zero findings."""

    def test_valid_cross_plugin_link_passes(self, docusaurus_project: dict[str, Path]) -> None:
        """docs/guide.md linking to /developers/existing-page/ → zero errors."""
        repo_root = docusaurus_project["repo_root"]
        docs = docusaurus_project["docs"]

        (docs / "guide.md").write_text(
            "[Existing page](/developers/existing-page/)\n",
            encoding="utf-8",
        )

        config = ZenzicConfig(
            docs_dir="docs",  # type: ignore[arg-type]
            build_context=BuildContext(engine="docusaurus"),
        )
        em = LayeredExclusionManager(config, docs_root=docs, repo_root=repo_root)
        errors = validate_links_structured(
            docs, em, repo_root=repo_root, config=config, strict=False
        )

        z104 = [e for e in errors if e.error_type == "Z104"]
        assert z104 == [], (
            f"False positive: valid link to /developers/existing-page/ must not raise Z104. "
            f"Got: {z104}"
        )


# ── REPRO-C: broken cross-plugin link — Z104 must fire ────────────────────────


class TestReproC_BrokenLink:
    """REPRO-C — a link to a non-existent /developers/ route must raise Z104.

    This is the core False Trust Bug: before the fix, /developers/ was absent
    from _scanned_vsm_prefixes (because VSM keys were /docs/developers/...),
    granting an unconditional bypass to all /developers/X links regardless of
    whether they existed.
    """

    def test_broken_cross_plugin_link_raises_Z104(
        self, docusaurus_project: dict[str, Path]
    ) -> None:
        """docs/guide.md linking to /developers/ghost-page/ → Z104 (page does not exist)."""
        repo_root = docusaurus_project["repo_root"]
        docs = docusaurus_project["docs"]

        (docs / "guide.md").write_text(
            "[Ghost page](/developers/ghost-page/)\n",
            encoding="utf-8",
        )

        config = ZenzicConfig(
            docs_dir="docs",  # type: ignore[arg-type]
            build_context=BuildContext(engine="docusaurus"),
        )
        em = LayeredExclusionManager(config, docs_root=docs, repo_root=repo_root)
        errors = validate_links_structured(
            docs, em, repo_root=repo_root, config=config, strict=False
        )

        z104 = [e for e in errors if e.error_type == "Z104"]
        assert z104, (
            "False Trust Bug still active: a broken link to /developers/ghost-page/ "
            "must raise Z104, but no Z104 was emitted. "
            f"All errors: {errors}"
        )

    def test_Z104_message_names_the_missing_route(
        self, docusaurus_project: dict[str, Path]
    ) -> None:
        """Z104 error message must reference the ghost route for actionable output."""
        repo_root = docusaurus_project["repo_root"]
        docs = docusaurus_project["docs"]

        (docs / "guide.md").write_text(
            "[Ghost](/developers/ghost-page/)\n",
            encoding="utf-8",
        )

        config = ZenzicConfig(
            docs_dir="docs",  # type: ignore[arg-type]
            build_context=BuildContext(engine="docusaurus"),
        )
        em = LayeredExclusionManager(config, docs_root=docs, repo_root=repo_root)
        errors = validate_links_structured(
            docs, em, repo_root=repo_root, config=config, strict=False
        )

        z104 = [e for e in errors if e.error_type == "Z104"]
        assert z104, "Expected Z104 error — see REPRO-C main test."
        assert "ghost-page" in z104[0].message.lower() or "/developers/" in z104[0].message, (
            f"Z104 message must reference the missing route. Got: {z104[0].message}"
        )


# ── REPRO-D: _zenzic_core excluded at engine level (ZRT-010) ─────────────────


class TestReproD_SystemExcludedDirs:
    """REPRO-D — _zenzic_core at repo root must be fully excluded with zero findings."""

    def test_zenzic_core_in_SYSTEM_EXCLUDED_DIRS(self) -> None:
        """_zenzic_core must be registered in SYSTEM_EXCLUDED_DIRS constant."""
        assert "_zenzic_core" in SYSTEM_EXCLUDED_DIRS, (
            "_zenzic_core is missing from SYSTEM_EXCLUDED_DIRS. "
            "ZRT-010 sovereign parity requires engine-level exclusion."
        )

    def test_zenzic_core_directory_produces_zero_findings(self, tmp_path: Path) -> None:
        """Presence of _zenzic_core/ at repo root must not produce any scan findings."""
        repo_root = tmp_path
        docs = repo_root / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("# Home\n", encoding="utf-8")

        # Simulate the CI artefact: a sibling core checkout with internal links
        core_dir = repo_root / "_zenzic_core"
        core_dir.mkdir()
        (core_dir / "README.md").write_text(
            "[Internal link](/docs/some-page/)\n",
            encoding="utf-8",
        )

        config = ZenzicConfig(
            docs_dir="docs",  # type: ignore[arg-type]
            build_context=BuildContext(engine="docusaurus"),
        )
        em = LayeredExclusionManager(config, docs_root=docs, repo_root=repo_root)
        errors = validate_links_structured(
            docs, em, repo_root=repo_root, config=config, strict=False
        )

        assert errors == [], (
            f"_zenzic_core/ must be fully excluded by SYSTEM_EXCLUDED_DIRS. Got: {errors}"
        )
