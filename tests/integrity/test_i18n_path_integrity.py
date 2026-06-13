# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""i18n Path Integrity checks (Direttiva CEO 124/125).

Three invariants the multi-root credential scanner must enforce simultaneously:

  INT-001  Cross-locale relative links (i18n/it/ → i18n/it/) are PASS.
           The credential scanner must recognise locale directories as authorised roots
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


def _locale_root(tmp_path: Path, locale: str = "it") -> Path:
    """Return the canonical Docusaurus locale source root and create it."""
    root = tmp_path / "i18n" / locale / "docusaurus-plugin-content-docs" / "current"
    root.mkdir(parents=True)
    return root


def _run(tmp_path: Path, locale_root: Path, locale: str = "it") -> list:
    """Run validate_links_structured with a single locale root."""
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    config = ZenzicConfig(build_context=BuildContext(engine="docusaurus", locales=[locale]))
    mgr = make_mgr(config, repo_root=tmp_path)
    return validate_links_structured(
        docs, mgr, repo_root=tmp_path, config=config, locale_roots=[(locale_root, locale)]
    )
