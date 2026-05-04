<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

> **Development history (v0.1.0 – v0.6.x):** See the [Changelog Archive](CHANGELOG.archive.md).

## [0.7.0] — 2026-05-XX (Target) — Quartz Maturity (Stable)

> **Legacy Documentation:** Versions prior to v0.7.0 are officially deprecated and do not follow
> the current Diátaxis architecture. For historical reference, see the
> [v0.6.1 GitHub Release](https://github.com/PythonWoods/zenzic/releases/tag/v0.6.1).
> The authoritative source is [zenzic.dev](https://zenzic.dev).

### 💎 Quartz Era (Initial Release)

This release marks Year Zero for the Zenzic ecosystem, establishing a new standard of
deterministic maturity and formal integrity. The codebase achieves structural maturity:
1,342+ tests, 80%+ branch coverage, and a hardened security pipeline.

#### Added

- **Sentinel Seal**: Rigorous 4-Gates validation system (`just verify`) integrated across
  every repository — pre-commit, test-cov, and self-check run identically in local and CI.
- **Cross-Repo Governance**: Branch Parity Rule for Core/Doc synchronisation with automatic
  fallback to `main`. VS Code Multi-Root Workspace configuration for unified development.
- **Z907 I18N Parity**: Language-agnostic translation parity scanner with adaptive parallelism,
  frontmatter key enforcement, and multi-instance Docusaurus support.
- **SARIF 2.1.0 Export**: All `check` commands support `--format sarif` for native GitHub
  Code Scanning integration with inline PR annotations.
- **Cross-Platform CI Matrix**: 3×3 matrix (Ubuntu/Windows/macOS × Python 3.11/3.12/3.13).
- **Engine Auto-Discovery**: `engine = "auto"` resolves the documentation framework
  automatically (Docusaurus → MkDocs → Zensical → Standalone).
- **Base64 Speculative Decoder**: Shield detects credentials encoded as Base64 in YAML
  frontmatter, sealing the S2 attack vector from the Quartz Tribunal.
- **Z107 Circular Anchor**, **Z505 Untagged Code Block**, **Z905 Brand Obsolescence**:
  Three new rule-based checks for structural and brand integrity.
- **Z404 Config Asset Integrity**: Verifies favicon and social card paths across all
  three supported engines (Docusaurus, MkDocs, Zensical).
- **Unified Navigation Discovery**: Docusaurus orphan detection aggregates sidebar,
  navbar, and footer surfaces (UX-Discoverability Law R21).
- **Static Sidebar Parser**: Pure-Python regex parser for `sidebars.ts`/`sidebars.js`.
- **Official GitHub Action**: `PythonWoods/zenzic-action` composite action with SARIF
  upload and configurable quality gates.
- **Determinism Invariant**: Formal contract in `pyproject.toml` — Zenzic ships zero
  AI/ML inference dependencies.

#### Changed

- **Engine-Agnostic Architecture**: MkDocs plugin permanently removed. Zenzic is now a
  Sovereign CLI independent of any documentation framework.
- **CLI Restructuring**: `cli.py` monolith split into a coherent `cli/` package.
  `zenzic plugins` replaced by `zenzic inspect capabilities`.
- **Layer Law Enforcement**: `ui.py` → `core/ui.py`, `lab.py` → `cli/_lab.py`,
  `run_rule()` → `core/rules.py`. Core never imports from CLI layer.
- **Pre-commit Hook**: `zenzic-check-all` replaced by `zenzic-verify` (4-Gates posture).
- **Coverage Format**: Standardised to JSON (`coverage.json`) across justfile and noxfile.

#### Removed

- **Legacy Brand Purge**: Complete removal of all obsolete nomenclature and external
  platform references from active configuration and documentation.
- **MkDocs Plugin**: `zenzic.integrations.mkdocs` physically purged. The `[mkdocs]`
  optional extra no longer exists.
- **`zenzic plugins` command**: Entirely removed. Use `zenzic inspect capabilities`.
- **`scripts/map_project.py`**: Superseded; no remaining callers.

#### Security

- **[ZRT-001]** Shield Blind Spot — YAML Frontmatter Bypass sealed (Dual-Stream architecture).
- **[ZRT-002]** ReDoS + ProcessPoolExecutor Deadlock — Canary prevention + 30s timeout containment.
- **[ZRT-003]** Split-Token Shield Bypass — `_normalize_line_for_shield()` pre-processor.
- **[ZRT-004]** Context-Aware VSM Resolution — `ResolutionContext` dataclass for nested paths.
- **Base64 speculative decoder** seals encoded credential attack vector.
- **`os.path.normcase` portability fix** for cross-platform Shield boundary comparison.
- **4-Gates Standard**: pre-commit → test-cov → self-check, enforced on every push.

#### Migration

Contributors must rerun bootstrap after pulling this release:

```bash
just sync
uvx pre-commit install              # commit-stage hooks
uvx pre-commit install -t pre-push  # 🛡️ Final Guard (just verify)
```

Replace `zenzic plugins list` with `zenzic inspect capabilities`.
Replace `pip install "zenzic[mkdocs]"` with `pip install zenzic`.
