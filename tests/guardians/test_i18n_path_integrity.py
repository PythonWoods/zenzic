# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Guardians — i18n Path Integrity (Direttiva CEO 124/125).

Three invariants the multi-root Shield must enforce simultaneously:

  INT-001  Cross-locale relative links (i18n/it/ → i18n/it/) are PASS.
           The Shield must recognise locale directories as authorised roots
           so that a file linking to its sibling translation is not treated
           as a path-traversal attack.

  INT-002  A locale file linking to ../../../../etc/passwd is FATAL.
           Admitting locale roots must never disable security: targets that
           resolve outside every authorised root are PATH_TRAVERSAL_SUSPICIOUS
           and must exit with code 3.

  INT-003  A same-page anchor mismatch inside a locale file is ERROR.
           Translators frequently update link text but forget the heading's
           {#id} attribute.  Locale files are always validated for intra-file
           anchors regardless of the validate_same_page_anchors config flag.

Bonus — INT-004  @site/static/ assets resolve correctly from locale files.
           known_assets is built from repo_root (not just docs_root) so that
           Docusaurus @site/ aliases work from anywhere in the tree.
"""

from __future__ import annotations

from pathlib import Path

from _helpers import make_mgr

from zenzic.core.validator import validate_links_structured
from zenzic.models.config import BuildContext, ZenzicConfig


# ─── helpers ─────────────────────────────────────────────────────────────────


def _locale_root(tmp_path: Path, locale: str = "it") -> Path:
    """Return the canonical Docusaurus locale source root and create it."""
    root = tmp_path / "i18n" / locale / "docusaurus-plugin-content-docs" / "current"
    root.mkdir(parents=True)
    return root


def _run(
    tmp_path: Path,
    locale_root: Path,
    locale: str = "it",
) -> list:
    """Run validate_links_structured with a single locale root."""
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")

    config = ZenzicConfig(build_context=BuildContext(engine="docusaurus", locales=[locale]))
    mgr = make_mgr(config, repo_root=tmp_path)
    return validate_links_structured(
        docs,
        mgr,
        repo_root=tmp_path,
        config=config,
        locale_roots=[(locale_root, locale)],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# INT-001 — Cross-locale relative link: sibling file in same locale dir → PASS
# ═══════════════════════════════════════════════════════════════════════════════


class TestCrossLocaleRelativeLink:
    """A file in i18n/it/ linking to a sibling in i18n/it/ must resolve cleanly."""

    def test_relative_link_to_sibling_passes(self, tmp_path: Path) -> None:
        locale_root = _locale_root(tmp_path)
        (locale_root / "intro.md").write_text(
            "# Introduzione\n\n[Vai alla guida](guide.md)\n",
            encoding="utf-8",
        )
        (locale_root / "guide.md").write_text("# Guida\n", encoding="utf-8")

        errors = _run(tmp_path, locale_root)
        assert errors == [], f"Expected no errors; got: {[e.message for e in errors]}"

    def test_relative_link_with_anchor_to_sibling_passes(self, tmp_path: Path) -> None:
        locale_root = _locale_root(tmp_path)
        (locale_root / "intro.md").write_text(
            "# Intro\n\n[Vai all'installazione](guide.md#installazione)\n",
            encoding="utf-8",
        )
        (locale_root / "guide.md").write_text(
            "# Guida\n\n## Installazione\n",
            encoding="utf-8",
        )

        errors = _run(tmp_path, locale_root)
        assert errors == [], f"Expected no errors; got: {[e.message for e in errors]}"

    def test_relative_link_into_subdirectory_passes(self, tmp_path: Path) -> None:
        locale_root = _locale_root(tmp_path)
        (locale_root / "tutorial").mkdir()
        (locale_root / "index.md").write_text(
            "# Home IT\n\n[Tutorial](tutorial/step1.md)\n",
            encoding="utf-8",
        )
        (locale_root / "tutorial" / "step1.md").write_text(
            "# Passo 1\n",
            encoding="utf-8",
        )

        errors = _run(tmp_path, locale_root)
        assert errors == [], f"Expected no errors; got: {[e.message for e in errors]}"


# ═══════════════════════════════════════════════════════════════════════════════
# INT-002 — Path traversal to OS system path from locale file: FATAL
# ═══════════════════════════════════════════════════════════════════════════════


class TestLocalePathTraversalBlocked:
    """Admitting locale roots must never open a path-traversal hole."""

    def test_traversal_to_etc_passwd_is_suspicious(self, tmp_path: Path) -> None:
        locale_root = _locale_root(tmp_path)
        (locale_root / "evil.md").write_text(
            "[credenziali](../../../../etc/passwd)\n",
            encoding="utf-8",
        )

        errors = _run(tmp_path, locale_root)
        types = [e.error_type for e in errors]
        assert "PATH_TRAVERSAL_SUSPICIOUS" in types, (
            f"Expected PATH_TRAVERSAL_SUSPICIOUS; got error_types: {types}"
        )

    def test_traversal_to_proc_is_suspicious(self, tmp_path: Path) -> None:
        locale_root = _locale_root(tmp_path)
        (locale_root / "evil.md").write_text(
            "[info](../../../../proc/version)\n",
            encoding="utf-8",
        )

        errors = _run(tmp_path, locale_root)
        types = [e.error_type for e in errors]
        assert "PATH_TRAVERSAL_SUSPICIOUS" in types, (
            f"Expected PATH_TRAVERSAL_SUSPICIOUS; got error_types: {types}"
        )

    def test_traversal_to_parent_repo_is_traversal(self, tmp_path: Path) -> None:
        """Escaping the locale root to a non-system path is still PATH_TRAVERSAL."""
        locale_root = _locale_root(tmp_path)
        (locale_root / "escape.md").write_text(
            # This resolves to somewhere outside every authorised root
            # but without targeting an OS system directory.
            "[fuori](../../../../../some-other-repo/README.md)\n",
            encoding="utf-8",
        )

        errors = _run(tmp_path, locale_root)
        types = [e.error_type for e in errors]
        assert any(t.startswith("PATH_TRAVERSAL") for t in types), (
            f"Expected a PATH_TRAVERSAL* error; got error_types: {types}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# INT-003 — Intra-file anchor mismatch in locale file: ERROR (always, no opt-in)
# ═══════════════════════════════════════════════════════════════════════════════


class TestLocaleIntraFileAnchorValidation:
    """Same-page anchor links in locale files are always validated."""

    def test_anchor_mismatch_is_error(self, tmp_path: Path) -> None:
        """Translator updated [link text](#contesto) but left heading as {#context}."""
        locale_root = _locale_root(tmp_path)
        (locale_root / "page.md").write_text(
            "## Il Contesto { #context }\n\n[Vai al contesto](#contesto)\n",
            encoding="utf-8",
        )

        errors = _run(tmp_path, locale_root)
        types = [e.error_type for e in errors]
        assert "ANCHOR_MISSING" in types, (
            f"Expected ANCHOR_MISSING for #contesto vs {{#context}}; got error_types: {types}"
        )

    def test_correct_anchor_passes(self, tmp_path: Path) -> None:
        """When the anchor matches the heading id, no error is raised."""
        locale_root = _locale_root(tmp_path)
        (locale_root / "page.md").write_text(
            "## Il Contesto { #contesto }\n\n[Vai al contesto](#contesto)\n",
            encoding="utf-8",
        )

        errors = _run(tmp_path, locale_root)
        assert errors == [], f"Expected no errors; got: {[e.message for e in errors]}"

    def test_anchor_validation_ignores_validate_same_page_anchors_flag(
        self, tmp_path: Path
    ) -> None:
        """validate_same_page_anchors=False must NOT disable validation for locale files."""
        locale_root = _locale_root(tmp_path)
        (locale_root / "page.md").write_text(
            "## Architettura\n\n[Vai qui](#architettura-italiana)\n",
            encoding="utf-8",
        )

        docs = tmp_path / "docs"
        docs.mkdir(exist_ok=True)
        (docs / "index.md").write_text("# Home\n", encoding="utf-8")

        # Explicitly disabled in config — must still fire for locale files.
        config = ZenzicConfig(
            validate_same_page_anchors=False,
            build_context=BuildContext(engine="docusaurus", locales=["it"]),
        )
        mgr = make_mgr(config, repo_root=tmp_path)
        errors = validate_links_structured(
            docs,
            mgr,
            repo_root=tmp_path,
            config=config,
            locale_roots=[(locale_root, "it")],
        )
        types = [e.error_type for e in errors]
        assert "ANCHOR_MISSING" in types, (
            "validate_same_page_anchors=False must not suppress anchor "
            f"validation in locale files; got error_types: {types}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# INT-004 — @site/static/ assets from locale files resolve correctly
# ═══════════════════════════════════════════════════════════════════════════════


class TestSiteAliasFromLocaleFile:
    """@site/static/ links must resolve even when the link is inside i18n/."""

    def test_site_static_asset_found_from_locale_file(self, tmp_path: Path) -> None:
        """known_assets covers repo_root so @site/static/ assets are found."""
        static = tmp_path / "static"
        static.mkdir()
        (static / "logo.png").write_bytes(b"\x89PNG")

        locale_root = _locale_root(tmp_path)
        (locale_root / "page.md").write_text(
            "# Pagina\n\n![Logo](@site/static/logo.png)\n",
            encoding="utf-8",
        )

        errors = _run(tmp_path, locale_root)
        assert errors == [], f"Expected no errors; got: {[e.message for e in errors]}"

    def test_site_static_asset_missing_is_reported(self, tmp_path: Path) -> None:
        """A missing @site/static/ asset from a locale file must produce FILE_NOT_FOUND."""
        locale_root = _locale_root(tmp_path)
        (locale_root / "page.md").write_text(
            "# Pagina\n\n![Fantasma](@site/static/ghost.png)\n",
            encoding="utf-8",
        )

        errors = _run(tmp_path, locale_root)
        types = [e.error_type for e in errors]
        assert "FILE_NOT_FOUND" in types, (
            f"Expected FILE_NOT_FOUND for missing @site/static/ghost.png; got error_types: {types}"
        )
