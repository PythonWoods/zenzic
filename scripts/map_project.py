#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""
Sentinel Mapper — CEO-083/085
Scans src/zenzic/ via AST and updates the [CODE MAP] section
in .github/copilot-instructions.md between <!-- MAP_START --> and <!-- MAP_END -->.
"""

import ast
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent
SRC_ROOT = REPO_ROOT / "src" / "zenzic"
LEDGER = REPO_ROOT / "ZENZIC_BRAIN.md"
SHADOW = REPO_ROOT / ".github" / "copilot-instructions.md"

MAP_START = "<!-- MAP_START -->"
MAP_END = "<!-- MAP_END -->"

# Fallback descriptions when a module lacks a module-level docstring.
# Primary source is always ast.get_docstring(tree). This dict is a safety net.
_FALLBACK_NOTES = {
    "main.py": "CLI entry point — registers all Typer groups",
    "rules.py": "SDK facade — re-export from core/rules.py",
    "core/shield.py": "Credential scanner — Blood Sentinel",
    "core/validator.py": "Link / anchor / path-traversal validation",
    "core/scanner.py": "File discovery, word count, placeholder check",
    "core/rules.py": "AdaptiveRuleEngine — parallel/sequential at 50-file threshold",
    "core/reporter.py": "SentinelReporter — Rich rendering of Finding objects",
    "core/codes.py": "Zxxx finding code registry — SINGLE SOURCE OF TRUTH",
    "core/exclusion.py": "LayeredExclusionManager (4 levels)",
    "core/resolver.py": "InMemoryPathResolver (multi-root, cross-locale)",
    "core/adapter.py": "Public re-export of adapters",
    "core/adapters/_factory.py": "get_adapter() factory — Z000 guard permanent",
    "core/adapters/_base.py": "AdapterProtocol — abstract contract",
    "core/adapters/_docusaurus.py": "Docusaurus v3 adapter",
    "core/adapters/_mkdocs.py": "MkDocs adapter",
    "core/adapters/_standalone.py": "StandaloneAdapter — no build system",
    "core/adapters/_utils.py": "",
    "core/adapters/_zensical.py": "",
    "core/discovery.py": "walk_files, iter_markdown_sources",
    "core/scorer.py": "Quality score engine",
    "core/cache.py": "Content-addressable CacheManager",
    "core/exceptions.py": "ConfigurationError, ShieldViolation, PluginContractError",
    "core/ui.py": "SentinelPalette, SentinelUI, make_banner",
    "core/logging.py": "",
    "core/models.py": "",
    "models/config.py": "ZenzicConfig / BuildContext (Pydantic) — 4-level priority",
    "models/vsm.py": "Virtual Site Map: Route, build_vsm, detect_collisions",
    "models/references.py": "Reference integrity: IntegrityReport, ReferenceFinding",
    "cli/_check.py": "check sub-app: links, orphans, snippets, references, assets, all",
    "cli/_standalone.py": "diff, init, score commands",
    "cli/_shared.py": "Shared helpers: _build_exclusion_manager, console",
    "cli/_lab.py": "lab command — 11 Acts, interactive showcase",
    "cli/_clean.py": "",
    "cli/_inspect.py": "",
}

# Integrity rules enforced during mapping (Zenzic Pillar compliance).
_CORE_VIOLATIONS = {
    "subprocess": "PILLAR-2-VIOLATION: subprocess call detected in core",
    "os.system": "PILLAR-2-VIOLATION: os.system call detected in core",
    "os.popen": "PILLAR-2-VIOLATION: os.popen call detected in core",
}


def _module_note(rel: str, tree: ast.Module) -> str:
    """Returns the module description: docstring first, fallback dict, then warning."""
    doc = ast.get_docstring(tree)
    if doc:
        return doc.splitlines()[0].strip()
    fallback = _FALLBACK_NOTES.get(rel, "")
    return fallback if fallback else "[⚠️ UNDOCUMENTED]"


def _detect_violations(rel: str, tree: ast.Module) -> list[str]:
    """Detects Pillar-2 violations in core modules via AST (imports + attribute calls)."""
    if "core/" not in rel:
        return []
    violations = []

    for node in ast.walk(tree):
        # Detect: import subprocess
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "subprocess":
                    violations.append("PILLAR-2-VIOLATION: subprocess call detected in core")
        # Detect: import os (needed for os.system / os.popen)
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "os":
                    pass  # further check via attribute calls below
        # Detect: subprocess.run(), os.system(), os.popen()
        if isinstance(node, ast.Attribute):
            if (
                isinstance(node.value, ast.Name)
                and node.value.id == "subprocess"
                and node.attr in ("run", "call", "Popen", "check_output", "check_call")
            ):
                violations.append("PILLAR-2-VIOLATION: subprocess call detected in core")
            if (
                isinstance(node.value, ast.Name)
                and node.value.id == "os"
                and node.attr in ("system", "popen")
            ):
                violations.append("PILLAR-2-VIOLATION: os.system/popen call detected in core")

    return list(dict.fromkeys(violations))  # deduplicate, preserve order


def extract_module_info(path: Path) -> dict:
    """Extracts classes, public functions, module note, and violations via AST."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return {
            "classes": [],
            "functions": [],
            "note": "[SYNTAX ERROR]",
            "violations": [],
            "error": True,
            "exc": str(exc),
        }

    rel = str(path.relative_to(SRC_ROOT))
    classes = []
    functions = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            classes.append(node.name)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if not node.name.startswith("_"):
                functions.append(node.name)

    return {
        "classes": classes,
        "functions": functions,
        "note": _module_note(rel, tree),
        "violations": _detect_violations(rel, tree),
        "error": False,
    }


def build_code_map() -> str:
    """Builds the Markdown [CODE MAP] block."""
    lines = [
        "### Mappa Moduli",
        "",
        "> Auto-generato da `scripts/map_project.py` via AST (CEO-083 — Sentinel Mapper Protocol).",
        "> Aggiornare con `just map-update` dopo ogni modifica a `src/`.",
        "",
        "| File | Classi | Funzioni pubbliche | Note |",
        "|------|--------|--------------------|------|",
    ]

    all_py = sorted(SRC_ROOT.rglob("*.py"))
    all_py = [
        p
        for p in all_py
        if p.name != "__init__.py" and "test" not in p.parts and "__pycache__" not in str(p)
    ]

    violation_summary: list[str] = []

    for abs_path in all_py:
        rel = str(abs_path.relative_to(SRC_ROOT))
        info = extract_module_info(abs_path)

        classes_str = ", ".join(f"`{c}`" for c in info["classes"]) or "—"
        funcs_str = ", ".join(f"`{f}`" for f in info["functions"]) or "—"
        note = info["note"]

        if info["violations"]:
            violation_tags = " ".join(f"**[{v}]**" for v in info["violations"])
            note = f"{note} {violation_tags}" if note != "[⚠️ UNDOCUMENTED]" else violation_tags
            violation_summary.extend(info["violations"])

        lines.append(f"| `{rel}` | {classes_str} | {funcs_str} | {note} |")

    lines.append("")
    lines.append("### Mappa Concetti → File")
    lines.append("")
    lines.append("| Concetto | File |")
    lines.append("|----------|------|")
    concept_map = [
        ("Shield / credential scan", "`src/zenzic/core/shield.py`"),
        ("Link validation", "`src/zenzic/core/validator.py`"),
        ("Exit codes (Zxxx)", "`src/zenzic/core/codes.py`"),
        ("CLI entry point", "`src/zenzic/main.py`"),
        ("Adapter factory (Z000 guard)", "`src/zenzic/core/adapters/_factory.py`"),
        ("Exclusion layers (4-level)", "`src/zenzic/core/exclusion.py`"),
        ("Virtual Site Map (VSM)", "`src/zenzic/models/vsm.py`"),
        ("Quality score", "`src/zenzic/core/scorer.py`"),
        ("Config priority (Pydantic)", "`src/zenzic/models/config.py`"),
        ("File discovery", "`src/zenzic/core/discovery.py`"),
        ("Rich UI / banners", "`src/zenzic/core/ui.py`"),
        ("SARIF / text reporter", "`src/zenzic/core/reporter.py`"),
    ]
    for concept, file in concept_map:
        lines.append(f"| {concept} | {file} |")

    return "\n".join(lines), violation_summary


def update_ledger(code_map: str) -> None:
    """Replaces the block between MAP_START and MAP_END in the ledger."""
    text = LEDGER.read_text(encoding="utf-8")
    start_idx = text.find(MAP_START)
    end_idx = text.find(MAP_END)

    if start_idx == -1 or end_idx == -1:
        print(
            f"[ERROR] Tags {MAP_START!r} or {MAP_END!r} not found in {LEDGER}.\n"
            "Add the tags to ZENZIC_BRAIN.md before running map-update.",
            file=sys.stderr,
        )
        sys.exit(1)

    new_block = f"{MAP_START}\n{code_map}\n{MAP_END}"
    new_text = text[:start_idx] + new_block + text[end_idx + len(MAP_END) :]
    LEDGER.write_text(new_text, encoding="utf-8")
    print(f"[CODE MAP] updated in {LEDGER.name}")


def shadow_sync() -> None:
    """Copies ZENZIC_BRAIN.md → .github/copilot-instructions.md for IDE compatibility."""
    content = LEDGER.read_text(encoding="utf-8")
    SHADOW.parent.mkdir(parents=True, exist_ok=True)
    SHADOW.write_text(content, encoding="utf-8")
    print(f"[SHADOW] {SHADOW.relative_to(REPO_ROOT)} synced from {LEDGER.name}")


def main() -> None:
    if not SRC_ROOT.exists():
        print(f"[ERROR] src/zenzic/ not found in {REPO_ROOT}", file=sys.stderr)
        sys.exit(1)

    code_map, violations = build_code_map()
    update_ledger(code_map)
    shadow_sync()

    n = code_map.count("\n| `")
    print(f"[OK] {n} modules mapped.")

    if violations:
        print(f"\n[⚠️  VIOLATIONS DETECTED] {len(violations)} Pillar compliance issue(s):")
        for v in violations:
            print(f"  - {v}")
        sys.exit(2)


if __name__ == "__main__":
    main()
