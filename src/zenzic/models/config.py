# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Zenzic configuration models and generator detection."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


# Severity type shared with the rule engine (avoids a circular import).
Severity = Literal["error", "warning", "info"]


class CustomRuleConfig(BaseModel):
    """A single entry in the ``[[custom_rules]]`` TOML array.

    Each entry declares a regex-based lint rule applied line-by-line to every
    Markdown file under ``docs/``.  The rule engine compiles the pattern once
    at config-load time.

    TOML example::

        [[custom_rules]]
        id = "ZZ-NOINTERNAL"
        pattern = "internal\\.corp\\.example\\.com"
        message = "Internal hostname must not appear in public docs."
        severity = "error"
    """

    id: str = Field(description="Stable unique identifier for this rule (e.g. 'ZZ001').")
    pattern: str = Field(description="Regular-expression string applied to each content line.")
    message: str = Field(description="Human-readable explanation shown in the finding.")
    severity: Severity = Field(
        default="error",
        description="Severity level: 'error' (default), 'warning', or 'info'.",
    )


class BuildContext(BaseModel):
    """Build engine context declared in ``[build_context]`` of ``zenzic.toml``.

    Tells Zenzic which documentation engine produced the site and which locale
    directories are non-default translations.  Used by adapters to resolve
    asset and page paths correctly across locale boundaries.
    """

    engine: str = Field(default="mkdocs", description="Build engine: 'mkdocs' or 'zensical'.")
    default_locale: str = Field(default="en", description="ISO 639-1 code of the default locale.")
    locales: list[str] = Field(
        default=[],
        description="Non-default locale directory names (e.g. ['it', 'fr']).",
    )
    fallback_to_default: bool = Field(
        default=True,
        description=(
            "When True, missing locale-tree assets/pages fall back to the "
            "default-locale tree (mirrors fallback_to_default in mkdocs-i18n). "
            "Set to False to report every missing locale file as an error."
        ),
    )


class ZenzicConfig(BaseModel):
    """Configuration model for Zenzic, typically loaded from zenzic.toml."""

    docs_dir: Path = Field(
        default=Path("docs"), description="Path to docs directory relative to repo root."
    )
    excluded_dirs: list[str] = Field(
        default=["includes", "assets", "stylesheets", "overrides", "hooks"],
        description="Directories inside docs/ to exclude from orphan and snippet checks.",
    )
    snippet_min_lines: int = Field(
        default=1,
        description="Minimum lines for a code block to be checked (skip trivial one-liners).",
    )
    placeholder_max_words: int = Field(
        default=50,
        description="Pages with fewer than this many words are flagged as placeholders.",
    )
    placeholder_patterns: list[str] = Field(
        default=[
            # English
            "coming soon",
            "work in progress",
            "wip",
            "todo",
            "to do",
            "stub",
            "placeholder",
            "fixme",
            "tbd",
            "to be written",
            "to be completed",
            "to be added",
            "under construction",
            "not yet written",
            "draft",
            # Italiano
            "da completare",
            "in costruzione",
            "in lavorazione",
            "da scrivere",
            "da aggiungere",
            "bozza",
            "prossimamente",
        ],
        description="Case-insensitive strings that flag a page as a placeholder.",
    )
    excluded_assets: list[str] = Field(
        default=[],
        description=(
            "Asset paths (relative to docs_dir) excluded from the unused-assets check. "
            "Use this for files that are referenced by mkdocs.yml or theme templates "
            "rather than by Markdown pages — e.g. favicons, logos, social preview images."
        ),
    )
    excluded_asset_dirs: list[str] = Field(
        default=["overrides"],
        description=(
            "Directories inside docs/ whose non-markdown files are excluded from the "
            "unused-assets check. Use this for theme override directories whose files "
            "are consumed by the build tool rather than referenced from Markdown pages."
        ),
    )
    excluded_file_patterns: list[str] = Field(
        default=[],
        description=(
            "Filename glob patterns excluded from the orphan check. "
            "Use this for locale-suffixed files produced by i18n plugins "
            "(e.g. '*.it.md', '*.fr.md') that are managed by the plugin and "
            "therefore intentionally absent from nav."
        ),
    )
    excluded_build_artifacts: list[str] = Field(
        default=[],
        description=(
            "Glob patterns (relative to docs_dir) for assets generated at build time. "
            "Links to paths matching these patterns are not flagged as broken even when "
            "the file does not exist on disk at lint time — e.g. PDFs produced by the "
            "to-pdf plugin or ZIP archives assembled by CI. "
            'Example: ["pdf/*.pdf", "assets/bundle.zip"]'
        ),
    )
    validate_same_page_anchors: bool = Field(
        default=False,
        description=(
            "When True, same-page anchor links (#section) are validated against the "
            "headings present in the source file. A link like [text](#missing) is "
            "reported as broken when no heading in the file produces that slug. "
            "Disabled by default because single-page anchor IDs can also be generated "
            "by HTML attributes, custom plugins, or build-time macros that are invisible "
            "at source-scan time."
        ),
    )
    excluded_external_urls: list[str] = Field(
        default=[],
        description=(
            "External URLs (or URL prefixes) excluded from the broken-link check. "
            "A URL is skipped when it starts with any entry in this list. "
            "Use this for URLs that are valid but not yet publicly reachable at lint time "
            "(e.g. a GitHub repo not yet created, an internal service behind a firewall). "
            'Example: ["https://github.com/PythonWoods/zenzic"]'
        ),
    )
    build_context: BuildContext = Field(
        default_factory=BuildContext,
        description="Build engine context for locale-aware path resolution.",
    )
    fail_under: int = Field(
        default=0,
        description=(
            "Minimum quality score (0–100). If the score falls below this value, "
            "zenzic score exits with code 1. 0 means no threshold (observational mode). "
            "The --fail-under CLI flag overrides this value when explicitly provided."
        ),
    )
    custom_rules: list[CustomRuleConfig] = Field(
        default=[],
        description=(
            "Project-specific lint rules declared inline in zenzic.toml.  "
            "Each entry applies a regex pattern line-by-line to every .md file.  "
            "Example:  [[custom_rules]]  id='ZZ001'  pattern='TODO'  "
            "message='Remove before publish.'  severity='warning'"
        ),
    )
    # Pre-compiled regex patterns for placeholder detection.
    # Populated automatically from placeholder_patterns in model_post_init.
    # Excluded from serialisation — never written to or read from TOML.
    placeholder_patterns_compiled: list[re.Pattern[str]] = Field(
        default_factory=list,
        exclude=True,
        repr=False,
    )

    def model_post_init(self, __context: Any) -> None:
        """Pre-compile placeholder patterns once after construction."""
        self.placeholder_patterns_compiled = [
            re.compile(re.escape(p), re.IGNORECASE) for p in self.placeholder_patterns
        ]

    @classmethod
    def load(cls, repo_root: Path) -> tuple[ZenzicConfig, bool]:
        """Load configuration from zenzic.toml.

        Falls back to defaults when the file does not exist.  Raises
        :class:`~zenzic.core.exceptions.ConfigurationError` with a Rich-
        formatted message when the file exists but contains a TOML syntax error
        — silent fallback would hide user mistakes.

        Args:
            repo_root: Repository root that may contain ``zenzic.toml``.

        Returns:
            A ``(config, loaded_from_file)`` tuple.  ``loaded_from_file`` is
            ``True`` when ``zenzic.toml`` was found and parsed, ``False`` when
            built-in defaults are in use.

        Raises:
            :class:`~zenzic.core.exceptions.ConfigurationError`: When
                ``zenzic.toml`` is present but cannot be parsed.
        """
        from zenzic.core.exceptions import ConfigurationError  # deferred to avoid circular import

        config_path = repo_root / "zenzic.toml"
        if not config_path.is_file():
            return cls(), False

        try:
            with config_path.open("rb") as f:
                data = tomllib.load(f)
        except tomllib.TOMLDecodeError as exc:
            raise ConfigurationError(
                f"[bold red]zenzic.toml[/] contains a syntax error and cannot be loaded.\n"
                f"  [dim]{config_path}[/]\n\n"
                f"  [red]{exc}[/]\n\n"
                "Fix the TOML syntax error and re-run Zenzic.",
                context={"config_path": str(config_path)},
            ) from exc

        # Only pass known fields to Pydantic
        known_fields = cls.model_fields.keys()
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        # Promote [build_context] sub-table into a BuildContext instance.
        if "build_context" in data and isinstance(data["build_context"], dict):
            filtered_data["build_context"] = BuildContext(
                **{k: v for k, v in data["build_context"].items() if k in BuildContext.model_fields}
            )
        # Promote [[custom_rules]] array into CustomRuleConfig instances.
        if "custom_rules" in data and isinstance(data["custom_rules"], list):
            filtered_data["custom_rules"] = [
                CustomRuleConfig(
                    **{k: v for k, v in r.items() if k in CustomRuleConfig.model_fields}
                )
                for r in data["custom_rules"]
                if isinstance(r, dict)
            ]
        return cls(**filtered_data), True
