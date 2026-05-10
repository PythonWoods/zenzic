# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""guard sub-commands: fast pre-commit secret guard powered by Shield."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import typer
from rich.table import Table

from zenzic.core.scanner import find_repo_root
from zenzic.core.shield import (
    SecurityFinding,
    scan_line_for_forbidden_terms,
    scan_line_for_secrets,
)
from zenzic.core.ui import SentinelPalette
from zenzic.models.config import ZenzicConfig

from . import _shared


guard_app = typer.Typer(
    name="guard",
    help=(
        f"[bold {SentinelPalette.BRAND}]Guard[/] — Fast pre-commit secret guard "
        "for Markdown/MDX files."
    ),
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def _is_doc_source(path: Path) -> bool:
    return path.suffix.lower() in {".md", ".mdx"}


def _scan_file_for_secrets(path: Path, forbidden_patterns: list[str]) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return findings

    for idx, line in enumerate(lines, start=1):
        findings.extend(scan_line_for_secrets(line, path, idx))
        findings.extend(scan_line_for_forbidden_terms(line, forbidden_patterns, path, idx))
    return findings


def _staged_doc_files(repo_root: Path) -> list[Path]:
    """Return staged Markdown/MDX files from git index (fast pre-commit path)."""
    cmd = [
        "git",
        "diff",
        "--cached",
        "--name-only",
        "--diff-filter=ACMRT",
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []

    if proc.returncode != 0:
        return []

    candidates = [repo_root / line.strip() for line in proc.stdout.splitlines() if line.strip()]
    docs = [p.resolve() for p in candidates if p.is_file() and _is_doc_source(p)]
    return sorted(set(docs))


def _resolve_targets(repo_root: Path, paths: list[str], staged: bool) -> list[Path]:
    if staged:
        return _staged_doc_files(repo_root)

    if paths:
        resolved: list[Path] = []
        for raw in paths:
            candidate = Path(raw)
            if not candidate.is_absolute():
                candidate = (repo_root / candidate).resolve()
            if candidate.is_file() and _is_doc_source(candidate):
                resolved.append(candidate)
            elif candidate.is_dir():
                resolved.extend(
                    p.resolve() for p in candidate.rglob("*") if p.is_file() and _is_doc_source(p)
                )
        return sorted(set(resolved))

    config, _ = ZenzicConfig.load(repo_root)
    docs_root = (repo_root / config.docs_dir).resolve()
    if not docs_root.is_dir():
        return []
    return sorted(p.resolve() for p in docs_root.rglob("*") if p.is_file() and _is_doc_source(p))


@guard_app.command(name="scan")
def scan(
    paths: list[str] = typer.Argument(
        None,
        help=(
            "Optional file/directory targets. If omitted, scans docs scope from config; "
            "with --staged scans staged Markdown/MDX files only."
        ),
    ),
    staged: bool = typer.Option(
        False,
        "--staged",
        help="Scan only staged Markdown/MDX files from git index (pre-commit fast path).",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text or json.",
    ),
) -> None:
    """Run Secret Guard using Shield signatures and local forbidden patterns."""
    repo_root = find_repo_root(fallback_to_cwd=True)
    config, _ = ZenzicConfig.load(repo_root)

    targets = _resolve_targets(repo_root, paths or [], staged)
    if not targets:
        if output_format == "json":
            print(json.dumps({"targets": 0, "findings": []}, indent=2))
        else:
            _shared.console.print("[dim]Secret Guard: no Markdown/MDX targets found.[/]")
        return

    findings: list[SecurityFinding] = []
    forbidden_patterns = [p for p in config.forbidden_patterns if isinstance(p, str) and p.strip()]

    for target in targets:
        findings.extend(_scan_file_for_secrets(target, forbidden_patterns))

    if output_format == "json":
        payload = {
            "targets": len(targets),
            "findings": [
                {
                    "file": str(f.file_path),
                    "line": f.line_no,
                    "secret_type": f.secret_type,
                    "match": f.match_text,
                    "context": f.url,
                }
                for f in findings
            ],
        }
        print(json.dumps(payload, indent=2))
        if findings:
            raise typer.Exit(2)
        return

    table = Table(
        title=f"[bold {SentinelPalette.BRAND}]Secret Guard[/]",
        header_style=SentinelPalette.STYLE_BRAND,
        border_style=SentinelPalette.DIM,
    )
    table.add_column("File", overflow="fold")
    table.add_column("Line", justify="right", width=6)
    table.add_column("Type", style=SentinelPalette.ERROR)
    table.add_column("Match", overflow="fold")

    if findings:
        for finding in findings:
            try:
                rel = finding.file_path.resolve().relative_to(repo_root)
                file_cell = str(rel)
            except ValueError:
                file_cell = str(finding.file_path)
            table.add_row(file_cell, str(finding.line_no), finding.secret_type, finding.match_text)
        _shared.console.print(table)
        _shared.console.print(
            f"[bold {SentinelPalette.ERROR}]Secret Guard blocked commit:[/] "
            f"{len(findings)} finding(s) across {len(targets)} file(s)."
        )
        raise typer.Exit(2)

    _shared.console.print(
        f"[bold {SentinelPalette.SUCCESS}]Secret Guard clean:[/] "
        f"{len(targets)} file(s) scanned, no secrets detected."
    )


_GUARD_HOOK_BLOCK = """- id: zenzic-guard
  name: zenzic guard (Secret Guard)
  description: Fast staged-file Shield scan for Markdown/MDX before commit.
  entry: zenzic guard scan --staged
  language: python
  types: [markdown]
  pass_filenames: false
  require_serial: true
"""


@guard_app.command(name="init")
def init_guard(
    path: str = typer.Option(
        ".pre-commit-hooks.yaml",
        "--path",
        help="Path of the pre-commit hooks definition file to create/update.",
        show_default=True,
    ),
) -> None:
    """Create or update .pre-commit-hooks.yaml with native Secret Guard hook."""
    target = Path(path).resolve()
    existing = ""
    if target.is_file():
        existing = target.read_text(encoding="utf-8")

    if "- id: zenzic-guard" in existing:
        _shared.console.print("[dim]Secret Guard hook already present; no changes applied.[/]")
        return

    if existing.strip():
        content = existing.rstrip() + "\n\n" + _GUARD_HOOK_BLOCK
    else:
        spdx_id_label = "SPDX-License-Identifier"
        content = (
            "# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>\n"
            f"# {spdx_id_label}: Apache-2.0\n\n"
            "# Generated by `zenzic guard init`\n"
            "# Native Secret Guard hook for staged Markdown/MDX files.\n\n" + _GUARD_HOOK_BLOCK
        )

    target.write_text(content, encoding="utf-8")
    _shared.console.print(
        f"[bold {SentinelPalette.SUCCESS}]Secret Guard hook installed:[/] {target}"
    )
