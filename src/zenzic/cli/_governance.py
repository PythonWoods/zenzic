# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Governance helpers for suppression CAP diagnostics, reporting, and per-file policies."""

from __future__ import annotations

import dataclasses
import sys
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any


if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # PEP 680 backport
from rich.console import Group
from rich.text import Text

from zenzic.core.discovery import iter_markdown_sources
from zenzic.core.exclusion import LayeredExclusionManager
from zenzic.core.reporter import Finding
from zenzic.core.rules import count_inline_suppressions
from zenzic.core.sovereign_context import get_sovereign_context
from zenzic.core.ui import ZenzicPalette, emoji
from zenzic.models.config import ZenzicConfig

from . import _shared


_SOVEREIGN_SUPPRESSION_CAP = 30


@dataclass(frozen=True)
class SuppressionAudit:
    inline_count: int
    per_file_count: int
    cap: int
    inline_hotspots: dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return self.inline_count + self.per_file_count

    @property
    def excess(self) -> int:
        return max(0, self.total - self.cap)

    @property
    def extended_debt(self) -> bool:
        """True when suppressions run under an expanded CAP above sovereign default."""
        return self.total > 0 and self.cap > _SOVEREIGN_SUPPRESSION_CAP

    @property
    def managed_debt(self) -> bool:
        """True when suppressions are in use but within the configured cap."""
        return self.total > 0 and not self.extended_debt

    @property
    def debt_status(self) -> str:
        """Machine-readable debt status for JSON contracts."""
        if self.total <= 0:
            return "CLEAN"
        if self.total > self.cap:
            return "CRITICAL"
        if self.extended_debt:
            return "EXTENDED"
        return "MANAGED"

    def top_offenders(self, *, limit: int = 5) -> list[tuple[str, int]]:
        rows = sorted(
            ((path, count) for path, count in self.inline_hotspots.items() if count > 0),
            key=lambda item: item[1],
            reverse=True,
        )
        if self.per_file_count > 0:
            rows.append((".zenzic.toml [per-file]", self.per_file_count))
        rows.sort(key=lambda item: item[1], reverse=True)
        return rows[:limit]


def collect_inline_suppression_stats(
    docs_root: Path,
    config: ZenzicConfig,
    exclusion_mgr: LayeredExclusionManager,
) -> tuple[int, dict[str, int]]:
    """Count inline suppression directives and hotspot distribution."""
    total = 0
    hotspots: dict[str, int] = {}
    for md_file in iter_markdown_sources(docs_root, config, exclusion_mgr):
        try:
            text = md_file.read_text(encoding="utf-8")
        except OSError:
            continue
        count = count_inline_suppressions(text)
        if count <= 0:
            continue
        total += count
        try:
            rel = str(md_file.relative_to(docs_root))
        except ValueError:
            rel = str(md_file)
        hotspots[rel] = count
    return total, hotspots


def count_per_file_ignores(config: ZenzicConfig) -> int:
    """Count configured per-file suppression entries (pattern+code pairs)."""
    total = 0
    for codes in config.governance.per_file_ignores.values():
        if not isinstance(codes, list):
            continue
        normalized_codes = {
            str(code).upper().strip()
            for code in codes
            if isinstance(code, str) and str(code).upper().startswith("Z")
        }
        total += len(normalized_codes)
    return total


def suppression_remediation_steps() -> list[str]:
    """Canonical remediation steps for suppression CAP governance failures."""
    return [
        "Review hotspots and remove suppressions where possible.",
        "If debt is intentional, update governance.suppression_cap in .zenzic.toml.",
        "Follow the playbook: https://zenzic.dev/developers/how-to/release-governance-protocol",
    ]


def print_suppression_audit_footer(
    suppression_audit: SuppressionAudit,
    *,
    cap_exceeded: bool = False,
    audit_mode: bool = False,
) -> None:
    """Print suppression audit footer in a consistent compact format."""
    tags: list[str] = []
    if suppression_audit.extended_debt:
        tags.append("[yellow][EXTENDED DEBT][/yellow]")
    elif suppression_audit.managed_debt:
        tags.append("[cyan][MANAGED DEBT][/cyan]")
    if cap_exceeded:
        tags.append(f"[{ZenzicPalette.ERROR}][CAP_EXCEEDED][/]")
    suffix = f" {' '.join(tags)}" if tags else ""
    _shared.console.print(
        f"{emoji('lock')} [{ZenzicPalette.DIM}]Suppression Audit:[/] "
        f"{suppression_audit.total}/{suppression_audit.cap} "
        f"(inline: {suppression_audit.inline_count}, per-file: {suppression_audit.per_file_count})"
        f"{suffix}"
    )
    if audit_mode:
        _shared.console.print(
            f"[{ZenzicPalette.DIM}]Sovereign Audit Mode:[/] "
            f"ignored {suppression_audit.total} active suppression directives "
            "(inline + per-file)."
        )


def print_governance_cap_failure(suppression_audit: SuppressionAudit, *, title: str) -> None:
    """Render CAP failure panel."""
    label_width = 31
    value_width = 5

    def _metric_number(label: str, value: int, *, sign: str = "", style: str = "") -> Text:
        rendered = f"{sign}{value:>{value_width}}"
        if style:
            rendered = f"[{style}]{rendered}[/]"
        return Text.from_markup(f"  [{ZenzicPalette.DIM}]{label:<{label_width}}[/] {rendered}")

    _shared.console.print(
        Text.from_markup(
            f"{emoji('sparkles')} [{ZenzicPalette.SUCCESS}]Analysis complete: "
            "All statically-detectable links, credentials, and references verified.[/]"
        )
    )
    _shared.console.print()

    rows: list[Text] = [
        Text.from_markup(
            f"[bold {ZenzicPalette.ERROR}][GOVERNANCE FAILURE][/] "
            f"{emoji('cross')} SUPPRESSION_CAP_EXCEEDED"
        ),
        Text.from_markup(
            f"[{ZenzicPalette.DIM}]Architectural debt limit reached. "
            "Build blocked by fail-hard policy.[/]"
        ),
        Text(),
        Text.from_markup(f"[bold {ZenzicPalette.BRAND}][STATISTICS][/]"),
        _metric_number("Total Active Suppressions:", suppression_audit.total),
        _metric_number("Configured Global CAP:", suppression_audit.cap),
        _metric_number(
            "Excess Debt:", suppression_audit.excess, sign="+", style=ZenzicPalette.ERROR
        ),
        Text(),
        Text.from_markup(f"[bold {ZenzicPalette.BRAND}][BREAKDOWN][/]"),
        _metric_number("Inline Ignores (zenzic:ignore):", suppression_audit.inline_count),
        _metric_number("Per-File Ignores (config):", suppression_audit.per_file_count),
        Text(),
        Text.from_markup(f"[bold {ZenzicPalette.BRAND}][HOTSPOTS - Top Offenders][/]"),
    ]

    offenders = suppression_audit.top_offenders(limit=5)
    if offenders:
        for path, count in offenders:
            rows.append(
                Text.from_markup(
                    f"  [{ZenzicPalette.ERROR}]{count:>{value_width}}[/]  "
                    f"[{ZenzicPalette.DIM}]{path}[/]"
                )
            )
    else:
        rows.append(Text.from_markup(f"  [{ZenzicPalette.DIM}]No hotspots detected.[/]"))

    rows.extend(
        [
            Text(),
            Text.from_markup(f"[bold {ZenzicPalette.BRAND}][REMEDIATION][/]"),
            Text.from_markup(
                "  Consult the Playbook: "
                f"[underline {ZenzicPalette.BRAND}]"
                "https://zenzic.dev/developers/how-to/release-governance-protocol[/]"
            ),
        ]
    )

    _shared.console.print(
        _shared._ui.make_panel(
            Group(*rows),
            title=f"[bold {ZenzicPalette.ERROR}]{title}[/]",
            subtitle="Suppression Audit",
            border_style=ZenzicPalette.ERROR,
        )
    )
    print_suppression_audit_footer(suppression_audit, cap_exceeded=True)


def read_project_name_from_toml(path: Path) -> str | None:
    """Read [project].name from a TOML file when available."""
    if not path.exists():
        return None
    try:
        data: dict[str, Any] = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    project = data.get("project")
    if isinstance(project, dict):
        raw = project.get("name")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return None


def resolve_governance_panel_title(repo_root: Path) -> str:
    """Resolve governance panel title from project metadata with safe fallback."""
    zenzic_name = read_project_name_from_toml(repo_root / ".zenzic.toml")
    pyproject_name = read_project_name_from_toml(repo_root / "pyproject.toml")
    app_name = zenzic_name or pyproject_name
    if not app_name:
        return "ZENZIC GOVERNANCE"
    return f"{app_name} Governance"


def build_cap_exceeded_json_payload(suppression_audit: SuppressionAudit) -> dict[str, object]:
    """Build structured JSON payload for CAP failures with explicit remediation."""
    return {
        "error": "SUPPRESSION_CAP_EXCEEDED",
        "severity": "error",
        "message": (
            f"Suppression cap exceeded: {suppression_audit.total}/{suppression_audit.cap}. "
            "Architectural debt limit reached."
        ),
        "suppression_count": suppression_audit.total,
        "suppression_cap": suppression_audit.cap,
        "suppression_debt_pts": suppression_audit.excess,
        "debt_status": suppression_audit.debt_status,
        "statistics": {
            "active_suppressions": suppression_audit.total,
            "configured_global_cap": suppression_audit.cap,
            "excess_debt": suppression_audit.excess,
            "inline_ignores": suppression_audit.inline_count,
            "per_file_ignores": suppression_audit.per_file_count,
        },
        "hotspots": [
            {"path": path, "count": count}
            for path, count in suppression_audit.top_offenders(limit=5)
        ],
        "remediation": suppression_remediation_steps(),
        "playbook": "https://zenzic.dev/developers/how-to/release-governance-protocol",
    }


def build_cap_exceeded_sarif_payload(
    suppression_audit: SuppressionAudit, *, version: str
) -> dict[str, object]:
    """Build SARIF payload for CAP failures with error severity and remediation guidance."""
    message = (
        f"SUPPRESSION_CAP_EXCEEDED: {suppression_audit.total}/{suppression_audit.cap}. "
        "Architectural debt limit reached. "
        "Remediation: "
        + " ".join(f"{i}. {step}" for i, step in enumerate(suppression_remediation_steps(), 1))
    )
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "zenzic",
                        "version": version,
                        "informationUri": "https://zenzic.dev",
                        "rules": [
                            {
                                "id": "SUPPRESSION_CAP_EXCEEDED",
                                "name": "Governance Suppression CAP Exceeded",
                                "shortDescription": {"text": "Global suppression cap exceeded."},
                                "defaultConfiguration": {"level": "error"},
                                "helpUri": (
                                    "https://zenzic.dev/developers/how-to/"
                                    "release-governance-protocol"
                                ),
                            }
                        ],
                    }
                },
                "results": [
                    {
                        "ruleId": "SUPPRESSION_CAP_EXCEEDED",
                        "level": "error",
                        "message": {"text": message},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {
                                        "uri": ".zenzic.toml",
                                        "uriBaseId": "%SRCROOT%",
                                    },
                                    "region": {"startLine": 1},
                                }
                            }
                        ],
                        "properties": {
                            "governance": {
                                "active_suppressions": suppression_audit.total,
                                "configured_global_cap": suppression_audit.cap,
                                "excess_debt": suppression_audit.excess,
                                "inline_ignores": suppression_audit.inline_count,
                                "per_file_ignores": suppression_audit.per_file_count,
                                "hotspots": [
                                    {"path": path, "count": count}
                                    for path, count in suppression_audit.top_offenders(limit=5)
                                ],
                                "remediation": suppression_remediation_steps(),
                            }
                        },
                    }
                ],
            }
        ],
    }


# ── Per-file ignore and directory policy filters ──────────────────────────────


def _apply_per_file_ignores(findings: list[Finding], config: ZenzicConfig) -> list[Finding]:
    """Filter findings using governance.per_file_ignores patterns.

    Security constraint
    -------------------
    Findings whose code is in ``NON_SUPPRESSIBLE_CODES`` (credential and path
    traversal findings) are always forwarded unchanged; they cannot be silenced
    by ``per_file_ignores`` or any governance mechanism.

    Sovereign audit
    ---------------
    When the Sovereign Audit context is active (``--audit`` flag) the entire
    filter is bypassed: all findings are returned verbatim so reviewers see the
    complete picture.

    Args:
        findings:  List of :class:`~zenzic.models.output.Finding` instances
                   produced by the current scan.
        config:    Loaded :class:`~zenzic.models.config.ZenzicConfig`; the
                   ``governance.per_file_ignores`` mapping is read from here.

    Returns:
        A filtered list of :class:`~zenzic.models.output.Finding` instances
        with suppressed entries removed.
    """
    from zenzic.core.codes import NON_SUPPRESSIBLE_CODES

    if get_sovereign_context().force_audit:
        return findings

    if not config.governance.per_file_ignores:
        return findings

    normalized_map: dict[str, set[str]] = {}
    for pattern, codes in config.governance.per_file_ignores.items():
        if not isinstance(pattern, str) or not isinstance(codes, list):
            continue
        normalized_codes = {
            str(code).upper().strip()
            for code in codes
            if isinstance(code, str) and str(code).upper().startswith("Z")
        }
        if normalized_codes:
            normalized_map[pattern] = normalized_codes

    if not normalized_map:
        return findings

    filtered: list[Finding] = []
    for finding in findings:
        code = finding.code.upper().strip()
        if code in NON_SUPPRESSIBLE_CODES:
            filtered.append(finding)
            continue

        suppressed = any(
            fnmatch(finding.rel_path, pattern) and code in codes
            for pattern, codes in normalized_map.items()
        )
        if suppressed:
            continue
        filtered.append(finding)
    return filtered


def _apply_directory_policies(findings: list[Finding], config: ZenzicConfig) -> list[Finding]:
    """Filter or label findings using governance.directory_policies patterns (ADR-084).

    In normal mode, matched findings are silently dropped with ZERO suppression
    debt cost.  In --audit (sovereign) mode, they are kept but prefixed with
    ``[POLICY_EXEMPTION]`` so reviewers can see what is strategically exempt.
    Security findings (NON_SUPPRESSIBLE_CODES) always bypass this filter.
    """
    from zenzic.core.codes import NON_SUPPRESSIBLE_CODES

    if not config.governance.directory_policies:
        return findings

    normalized_map: dict[str, set[str]] = {}
    for pattern, codes in config.governance.directory_policies.items():
        if not isinstance(pattern, str) or not isinstance(codes, list):
            continue
        normalized_codes = {
            str(code).upper().strip()
            for code in codes
            if isinstance(code, str) and str(code).upper().startswith("Z")
        }
        if normalized_codes:
            normalized_map[pattern] = normalized_codes

    if not normalized_map:
        return findings

    audit_mode = get_sovereign_context().force_audit
    filtered: list[Finding] = []
    for finding in findings:
        code = finding.code.upper().strip()
        if code in NON_SUPPRESSIBLE_CODES:
            filtered.append(finding)
            continue
        is_exempt = any(
            fnmatch(finding.rel_path, pattern) and code in codes
            for pattern, codes in normalized_map.items()
        )
        if is_exempt:
            if audit_mode:
                filtered.append(
                    dataclasses.replace(
                        finding,
                        message=f"[POLICY_EXEMPTION] {finding.message}",
                    )
                )
            # else: silently drop (zero debt)
        else:
            filtered.append(finding)
    return filtered
