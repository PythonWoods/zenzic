# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Zenzic Finding Code Registry.

Every finding Zenzic emits carries a stable machine-readable code of the form
``Zxxx``.  This module is the single source of truth for code assignments.

Schema
------
Z1xx — Link Integrity
    Z101  LINK_BROKEN          — target file not found in the Virtual Site Map
    Z102  ANCHOR_MISSING       — fragment target (#anchor) not defined on the page
    Z103  ORPHAN_LINK          — link target exists but is not in the nav (ORPHAN_BUT_EXISTING)
    Z104  FILE_NOT_FOUND       — link target file missing from the filesystem
    Z105  ABSOLUTE_PATH        — link uses an absolute path (not portable)
    Z106  CIRCULAR_LINK        — link is part of a circular reference cycle
    Z107  CIRCULAR_ANCHOR      — anchor link whose text slugifies to its own fragment

Z2xx — Security (Shield)
    Z201  SHIELD_SECRET        — credential / secret detected (Exit 2)
    Z202  PATH_TRAVERSAL       — path escapes the docs root boundary
    Z203  PATH_TRAVERSAL_FATAL — traversal targeting OS system directories (Exit 3)

Z3xx — Reference Integrity
    Z301  DANGLING_REF         — reference link uses an undefined ID
    Z302  DEAD_DEF             — reference definition never used by any link
    Z303  DUPLICATE_DEF        — reference ID defined more than once

Z4xx — Structure
    Z401  MISSING_DIRECTORY_INDEX — directory lacks an index page (Standalone Mode)
    Z402  ORPHAN_PAGE          — Markdown file not listed in the site navigation
    Z403  MISSING_ALT          — image element has no alt text
    Z404  CONFIG_ASSET_MISSING — infrastructure asset referenced in engine config not found on disk

Z5xx — Content Quality
    Z501  PLACEHOLDER          — page contains stub / TODO content
    Z502  SHORT_CONTENT        — page word count below minimum threshold
    Z503  SNIPPET_ERROR        — fenced code block fails syntax validation
    Z504  QUALITY_REGRESSION   — Sentinel Scorer detected score drop vs saved baseline
    Z505  UNTAGGED_CODE_BLOCK  — fenced code block has no language specifier

Z9xx — Engine / System
    Z901  RULE_ENGINE_ERROR    — plugin rule raised an unexpected exception
    Z902  RULE_TIMEOUT         — plugin rule exceeded the per-file time limit (ReDoS guard)
    Z903  UNUSED_ASSET         — asset file not referenced by any documentation page
    Z904  NAV_CONTRACT         — navigation contract violation
    Z905  BRAND_OBSOLESCENCE   — deprecated brand term found in documentation source
    Z906  NO_FILES_FOUND       — target directory contains no Markdown sources (audit skipped)
    Z907  I18N_PARITY          — base-language doc lacks mirror in a target language, or frontmatter parity mismatch
"""

from __future__ import annotations

from typing import NamedTuple


# ── Exit Code Contract ────────────────────────────────────────────────────────


class ZenzicExitCode:
    """Centralised exit code constants for the Zenzic CLI.

    These values implement the Exit Code Contract:

    * ``SUCCESS`` (0) — all checks passed; documentation is clean.
    * ``QUALITY`` (1) — quality findings (broken links, orphans, …);
      suppressible by ``--exit-zero``.
    * ``SHIELD`` (2) — Shield security breach — credential detected (Z201);
      **never** suppressible.
    * ``SENTINEL`` (3) — Blood Sentinel — system path traversal / fatal
      (Z202/Z203); **never** suppressible.

    Usage in CLI layer::

        from zenzic.core.codes import ZenzicExitCode
        raise typer.Exit(ZenzicExitCode.SHIELD)
    """

    SUCCESS: int = 0
    QUALITY: int = 1
    SHIELD: int = 2
    SENTINEL: int = 3


# ── Canonical code map ────────────────────────────────────────────────────────
# Maps legacy string codes (as emitted by validators / scanner) to the stable
# Zxxx code.  The legacy string is kept as the public code value for now so
# that existing tool integrations continue to work; the Zxxx code is always
# displayed alongside it in the report.

#: Mapping of legacy ``error_type`` / ``issue`` strings to canonical Zxxx codes.
LEGACY_TO_CODE: dict[str, str] = {
    # Link integrity (Z1xx)
    "Z001": "Z101",  # VSMBrokenLinkRule emits Z001 → Z101 LINK_BROKEN
    "Z002": "Z103",  # VSMBrokenLinkRule emits Z002 → Z103 ORPHAN_LINK
    "FILE_NOT_FOUND": "Z104",
    "ANCHOR_MISSING": "Z102",
    "ABSOLUTE_PATH": "Z105",
    "CIRCULAR_LINK": "Z106",
    "LINK_ERROR": "Z101",  # generic catch-all for broken links
    "UNREACHABLE_LINK": "Z101",
    # Security (Z2xx)
    "SHIELD": "Z201",
    "PATH_TRAVERSAL": "Z202",
    "PATH_TRAVERSAL_SUSPICIOUS": "Z203",
    # Reference integrity (Z3xx)
    "DANGLING": "Z301",
    "DEAD_DEF": "Z302",
    "duplicate-def": "Z303",
    "missing-alt": "Z403",
    # Structure (Z4xx)
    "MISSING_DIRECTORY_INDEX": "Z401",
    "ORPHAN": "Z402",
    "CONFIG_ASSET_MISSING": "Z404",
    # Content quality (Z5xx)
    "placeholder-text": "Z501",
    "short-content": "Z502",
    "SNIPPET": "Z503",
    # Engine / system (Z9xx)
    "RULE-ENGINE-ERROR": "Z901",
    "Z009": "Z902",
    "ASSET": "Z903",
    "NAV": "Z904",
    "LINK_URL": "Z101",
}

#: Human-readable name for each code (for report headers).
CODE_NAMES: dict[str, str] = {
    "Z101": "LINK_BROKEN",
    "Z102": "ANCHOR_MISSING",
    "Z103": "ORPHAN_LINK",
    "Z104": "FILE_NOT_FOUND",
    "Z105": "ABSOLUTE_PATH",
    "Z106": "CIRCULAR_LINK",
    "Z107": "CIRCULAR_ANCHOR",
    "Z201": "SHIELD_SECRET",
    "Z202": "PATH_TRAVERSAL",
    "Z203": "PATH_TRAVERSAL_FATAL",
    "Z301": "DANGLING_REF",
    "Z302": "DEAD_DEF",
    "Z303": "DUPLICATE_DEF",
    "Z401": "MISSING_DIRECTORY_INDEX",
    "Z402": "ORPHAN_PAGE",
    "Z403": "MISSING_ALT",
    "Z404": "CONFIG_ASSET_MISSING",
    "Z501": "PLACEHOLDER",
    "Z502": "SHORT_CONTENT",
    "Z503": "SNIPPET_ERROR",
    "Z504": "QUALITY_REGRESSION",
    "Z505": "UNTAGGED_CODE_BLOCK",
    "Z901": "RULE_ENGINE_ERROR",
    "Z902": "RULE_TIMEOUT",
    "Z903": "UNUSED_ASSET",
    "Z904": "NAV_CONTRACT",
    "Z905": "BRAND_OBSOLESCENCE",
    "Z906": "NO_FILES_FOUND",
    "Z907": "I18N_PARITY",
}

#: Short description of each code for SARIF ``shortDescription`` and human display.
#: Single source of truth — never duplicate these strings in other modules.
CODE_DESCRIPTIONS: dict[str, str] = {
    # Z1xx — Link Integrity
    "Z101": "Link target not found in the Virtual Site Map",
    "Z102": "Fragment anchor (#anchor) not defined on the target page",
    "Z103": "Link target exists but is not reachable via site navigation",
    "Z104": "Link target file missing from the filesystem",
    "Z105": "Absolute path detected — use a relative path for portability",
    "Z106": "Circular link chain detected between documentation pages",
    "Z107": "Self-referential anchor link — slug(text) resolves to the same fragment",
    # Z2xx — Security
    "Z201": "Potential credential or secret detected in documentation content",
    "Z202": "Link escapes the documentation root boundary (path traversal)",
    "Z203": "Path traversal targeting OS system directories — fatal security breach",
    # Z3xx — Reference Integrity
    "Z301": "Reference-style link uses an undefined identifier",
    "Z302": "Link definition declared but never referenced",
    "Z303": "Reference identifier defined more than once",
    # Z4xx — Structure
    "Z401": "Directory lacks a required index page",
    "Z402": "Markdown file not listed in the site navigation",
    "Z403": "Image element has no alt text",
    "Z404": "Asset referenced in engine config not found on disk",
    # Z5xx — Content Quality
    "Z501": "Page contains placeholder or stub content",
    "Z502": "Page word count is below the minimum threshold",
    "Z503": "Fenced code block contains a syntax error",
    "Z504": "Documentation quality score regressed below the saved baseline",
    "Z505": "Fenced code block has no language specifier",
    # Z9xx — Engine / System
    "Z901": "Plugin rule raised an unexpected exception",
    "Z902": "Plugin rule exceeded the per-file time limit (ReDoS guard)",
    "Z903": "Asset file not referenced by any documentation page",
    "Z904": "Navigation contract violation detected",
    "Z905": "Deprecated brand term found in documentation source",
    "Z906": "Target directory contains no Markdown sources — audit skipped",
    "Z907": "Translation mirror missing or frontmatter parity violation",
}

#: Default SARIF ``defaultConfiguration.level`` for each code.
#: Z1xx/Z2xx → "error" | Z3xx–Z9xx quality → "warning" | Z906 informational → "note"
#: Individual Finding severity always takes precedence at result level.
CODE_SARIF_LEVELS: dict[str, str] = {
    # Z1xx — Link Integrity: errors (broken links block the user experience)
    "Z101": "error",
    "Z102": "error",
    "Z103": "error",
    "Z104": "error",
    "Z105": "error",
    "Z106": "error",
    "Z107": "error",
    # Z2xx — Security: always errors
    "Z201": "error",
    "Z202": "error",
    "Z203": "error",
    # Z3xx — Reference Integrity: warnings (quality signal, not blocking)
    "Z301": "warning",
    "Z302": "warning",
    "Z303": "warning",
    # Z4xx — Structure: warnings
    "Z401": "warning",
    "Z402": "warning",
    "Z403": "warning",
    "Z404": "warning",
    # Z5xx — Content Quality: warnings
    "Z501": "warning",
    "Z502": "warning",
    "Z503": "warning",
    "Z504": "warning",
    "Z505": "warning",
    # Z9xx — Engine / System: warnings (except Z906 which is informational)
    "Z901": "warning",
    "Z902": "warning",
    "Z903": "warning",
    "Z904": "warning",
    "Z905": "warning",
    "Z906": "note",
    "Z907": "warning",
}


def get_sarif_name(code: str) -> str:
    """Convert a Zxxx code to its SARIF-canonical CamelCase rule name.

    Derives the name deterministically from :data:`CODE_NAMES`:
    ``"LINK_BROKEN"`` → ``"LinkBroken"``.  Falls back to the raw code
    string for unknown codes so the SARIF remains valid even for
    dynamically emitted plugin codes.

    Args:
        code: A canonical Zxxx code string, e.g. ``"Z101"``.

    Returns:
        CamelCase rule name suitable for the SARIF ``rules[].name`` field.
    """
    name = CODE_NAMES.get(code, code)
    return "".join(word.capitalize() for word in name.split("_"))


# ── Core Scanner Registry ─────────────────────────────────────────────────────


class CoreScanner(NamedTuple):
    """Static descriptor for a built-in Zenzic scanner.

    These scanners are compiled into Zenzic itself — always active, not
    configurable or removable via the ``zenzic.rules`` entry-point group.
    """

    codes: str
    """Display code range, e.g. ``"Z201"`` or ``"Z202\u2013203"``."""

    name: str
    """Human-readable scanner name, e.g. ``"The Shield"``."""

    capability: str
    """One-line capability summary shown in ``zenzic inspect capabilities``."""

    primary_exit: int
    """Primary exit code: 1 (quality), 2 (Shield), or 3 (Blood Sentinel)."""

    non_suppressible: bool
    """``True`` when ``--exit-zero`` cannot override this scanner's exit."""


#: Built-in scanners — static, always active, single source of truth for
#: ``zenzic inspect capabilities`` and any future Arsenal introspection.
CORE_SCANNERS: list[CoreScanner] = [
    CoreScanner(
        codes="Z201",
        name="The Shield",
        capability=(
            "Credential & secret detection \u2014 9 families "
            "(AWS, GitHub, GitLab PAT, Stripe, Slack, OpenAI, Google, PEM, hex)"
        ),
        primary_exit=2,
        non_suppressible=True,
    ),
    CoreScanner(
        codes="Z202\u2013203",
        name="Blood Sentinel",
        capability=(
            "Path-traversal boundary enforcement \u2014 rejects any link escaping the docs/ root"
        ),
        primary_exit=3,
        non_suppressible=True,
    ),
    CoreScanner(
        codes="Z101\u2013106",
        name="Link Validator",
        capability=(
            "Broken links, dead anchors, circular refs, "
            "absolute internal links, proactive suggestions"
        ),
        primary_exit=1,
        non_suppressible=False,
    ),
    CoreScanner(
        codes="Z301\u2013303",
        name="Reference Scanner",
        capability="Dangling reference IDs, dead link definitions, duplicate reference keys",
        primary_exit=1,
        non_suppressible=False,
    ),
    CoreScanner(
        codes="Z401\u2013404",
        name="Structure Guard",
        capability=(
            "Directory-index integrity, orphan pages, missing alt text, config asset paths"
        ),
        primary_exit=1,
        non_suppressible=False,
    ),
    CoreScanner(
        codes="Z501\u2013503",
        name="Content Guard",
        capability=("Placeholder / stub text, overly short pages, syntax errors in code snippets"),
        primary_exit=1,
        non_suppressible=False,
    ),
    CoreScanner(
        codes="Z903",
        name="Asset Sentry",
        capability="Unused images and media files not referenced anywhere in the docs tree",
        primary_exit=1,
        non_suppressible=False,
    ),
    CoreScanner(
        codes="Z107",
        name="Circular Anchor Guard",
        capability=(
            "Self-referential anchor links \u2014 detects [text](#fragment) "
            "where slug(text) == fragment"
        ),
        primary_exit=1,
        non_suppressible=False,
    ),
    CoreScanner(
        codes="Z505",
        name="Code Block Sentinel",
        capability="Fenced code blocks without a language specifier (``` or ~~~)",
        primary_exit=1,
        non_suppressible=False,
    ),
    CoreScanner(
        codes="Z905",
        name="Brand Integrity Guard",
        capability=(
            "Deprecated brand term detection \u2014 configurable via [project_metadata], "
            "suppressed per-line with <!-- zenzic:ignore Z905 --> (Markdown) or {/* zenzic:ignore Z905 */} (MDX)"
        ),
        primary_exit=1,
        non_suppressible=False,
    ),
    CoreScanner(
        codes="Z907",
        name="I18N Parity Guard",
        capability=(
            "Cross-language mirror integrity \u2014 every base-language doc must "
            "have a translation in each configured target root, with matching "
            "frontmatter keys (opt-in via [i18n] section, language-agnostic)"
        ),
        primary_exit=1,
        non_suppressible=False,
    ),
]


def normalize(legacy_code: str) -> str:
    """Return the canonical ``Zxxx`` code for *legacy_code*.

    If *legacy_code* already starts with ``Z`` and has exactly 4 characters
    (i.e. it is already a canonical code or a core-rule Zxxx code like
    ``Z001``), it is looked up in the map first; if not found it is returned
    as-is.

    Args:
        legacy_code: Raw code string from a validator, scanner, or rule engine.

    Returns:
        Canonical ``Zxxx`` string.
    """
    return LEGACY_TO_CODE.get(legacy_code, legacy_code)


def label(code: str) -> str:
    """Return ``"Zxxx NAME"`` for display, e.g. ``"Z101 LINK_BROKEN"``.

    Falls back to just the code when no name is registered.
    """
    name = CODE_NAMES.get(code, "")
    return f"{code} {name}".strip()
