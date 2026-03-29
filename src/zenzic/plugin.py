# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Native MkDocs plugin for Zenzic documentation quality checks."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from mkdocs.config import base, config_options as c
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import PluginError
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files
from mkdocs.structure.nav import Navigation
from mkdocs.structure.pages import Page

from zenzic.core.scanner import (
    calculate_orphans,
    calculate_unused_assets,
    check_asset_references,
    check_placeholder_content,
)
from zenzic.core.validator import check_snippet_content
from zenzic.models.config import ZenzicConfig


log = logging.getLogger("mkdocs.plugins.zenzic")


class ZenzicPluginConfig(base.Config):
    """Configuration schema for the Zenzic MkDocs plugin."""

    strict = c.Type(bool, default=False)
    fail_on_error = c.Type(bool, default=True)
    checks = c.Type(list, default=["orphans", "snippets", "placeholders", "assets"])
    source = c.Optional(c.Type(str))


class ZenzicPlugin(BasePlugin[ZenzicPluginConfig]):
    """MkDocs plugin that runs Zenzic documentation quality checks during the build.

    Example ``mkdocs.yml`` configuration::

        plugins:
          - zenzic:
              source: docs/        # optional; defaults to MkDocs docs_dir
              strict: false
              fail_on_error: true
              checks: [orphans, snippets, placeholders, assets]
    """

    # Instance state accumulated across hooks
    _repo_root: Path
    _zenzic_config: ZenzicConfig
    _issues: list[str]
    _all_assets: set[str]
    _used_assets: set[str]

    # ── on_config ──────────────────────────────────────────────────────────────

    def on_config(self, config: MkDocsConfig, **kwargs: Any) -> MkDocsConfig | None:
        """Initialise per-build state and resolve the docs directory."""
        self._issues = []
        self._all_assets = set()
        self._used_assets = set()

        config_file = config.config_file_path
        self._repo_root = Path(config_file).parent if config_file else Path.cwd()

        source: str | None = self.config.source
        if source:
            docs_dir = Path(source)
            if not docs_dir.is_absolute():
                docs_dir = self._repo_root / docs_dir
        else:
            docs_dir = Path(config.docs_dir)

        # repo_root / absolute_path == absolute_path in pathlib, so this is safe
        # regardless of whether docs_dir is relative or absolute.
        _cfg, _ = ZenzicConfig.load(self._repo_root)
        self._zenzic_config = _cfg.model_copy(update={"docs_dir": docs_dir})
        return None

    # ── on_files ───────────────────────────────────────────────────────────────

    def on_files(self, files: Files, config: MkDocsConfig, **kwargs: Any) -> Files | None:
        """Collect all media files known to MkDocs for the asset check."""
        if "assets" in set(self.config.checks):
            self._all_assets = {f.src_uri for f in files.media_files()}
        return None

    # ── on_nav ─────────────────────────────────────────────────────────────────

    def on_nav(
        self, nav: Navigation, config: MkDocsConfig, files: Files, **kwargs: Any
    ) -> Navigation | None:
        """Detect orphaned pages using MkDocs-native nav and file objects."""
        if "orphans" not in set(self.config.checks):
            return None

        try:
            nav_uris = {page.file.src_uri for page in nav.pages}
            all_md = {f.src_uri for f in files if f.src_uri.endswith(".md")}

            for path in calculate_orphans(all_md, nav_uris):
                self._issues.append(f"[orphan] {path}")
                log.warning("Zenzic [orphan]: %s — not listed in nav", path)
        except Exception as exc:
            log.error("Zenzic internal error in on_nav: %s", exc)

        return None

    # ── on_page_markdown ───────────────────────────────────────────────────────

    def on_page_markdown(
        self,
        markdown: str,
        page: Page,
        config: MkDocsConfig,
        files: Files,
        **kwargs: Any,
    ) -> str | None:
        """Run content-level checks on each page's raw markdown.

        MkDocs passes each page's markdown after loading but before rendering,
        so we analyse the text in-memory without touching the disk.
        """
        enabled = set(self.config.checks)
        src_uri = page.file.src_uri

        try:
            if "snippets" in enabled:
                for err in check_snippet_content(markdown, src_uri, self._zenzic_config):
                    self._issues.append(f"[snippet] {err.file_path}:{err.line_no}")
                    log.warning(
                        "Zenzic [snippet]: %s:%d — %s", err.file_path, err.line_no, err.message
                    )

            if "placeholders" in enabled:
                for p in check_placeholder_content(markdown, src_uri, self._zenzic_config):
                    self._issues.append(f"[placeholder] {p.file_path}:{p.line_no}")
                    log.warning(
                        "Zenzic [placeholder]: %s:%d [%s] — %s",
                        p.file_path,
                        p.line_no,
                        p.issue,
                        p.detail,
                    )

            if "assets" in enabled:
                import posixpath

                page_dir = posixpath.dirname(src_uri)
                self._used_assets |= check_asset_references(markdown, page_dir)

        except Exception as exc:
            log.error("Zenzic internal error in on_page_markdown (page: %s): %s", src_uri, exc)

        return None

    # ── on_post_build ──────────────────────────────────────────────────────────

    def on_post_build(self, config: MkDocsConfig, **kwargs: Any) -> None:
        """Finalize the asset check and raise if any issues were accumulated."""
        try:
            if "assets" in set(self.config.checks):
                for path in calculate_unused_assets(self._all_assets, self._used_assets):
                    self._issues.append(f"[unused-asset] {path}")
                    log.warning("Zenzic [unused-asset]: %s", path)
        except Exception as exc:
            log.error("Zenzic internal error in on_post_build: %s", exc)

        # Intentional linting failure — evaluated unconditionally so that issues
        # already accumulated before any crash are still reported.
        if self._issues and self.config.fail_on_error:
            raise PluginError(
                f"Zenzic: {len(self._issues)} documentation quality issue(s) found. "
                "Run 'zenzic check all' for details, or set fail_on_error: false to continue."
            )
