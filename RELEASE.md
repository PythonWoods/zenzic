<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Zenzic v0.6.1rc2 — Obsidian Bastion (Hardened) Release Protocol

**Prepared by:** S-1 (Auditor)
**Date:** 2026-04-16
**Status:** RELEASE CANDIDATE 2 — Security audit completed
**Branch:** `main`
**Codename:** Obsidian Bastion (Hardened) — Post-Stress-Test Seal

> **Tech Lead note:** RC2 follows Operation Obsidian Stress — a controlled
> siege by Red/Blue/Purple teams. The Red Team found 4 Shield bypass vectors
> (Unicode Cf, HTML entities, comment-interleaving, cross-line split). All
> have been sealed. The Purple Team identified 6 documentation drift items
> including a phantom `serve` command. All corrected. 1046 tests pass.

---

## 1. Version Anchors

| Location | Expected | Status |
| :--- | :--- | :---: |
| `src/zenzic/__init__.py` | `0.6.1rc2` | ✅ |
| `pyproject.toml` `[project]` | `0.6.1rc2` | ✅ |
| `pyproject.toml` `[tool.bumpversion]` | `0.6.1rc2` | ✅ |
| `CITATION.cff` | `0.6.1rc2` | ✅ |
| `CHANGELOG.md` top entry | `[0.6.1rc2]` | ✅ |
| `CHANGELOG.it.md` top entry | `[0.6.1rc2]` | ✅ |

**Not tracked** (Clean Harbor):

- `mkdocs.yml` — deleted (docs migrated to `zenzic-doc`)
- `uv.lock` — updated by `uv lock`, not by bumpversion

---

## 2. The Adapter Gate (Core Logic)

### 2a. Docusaurus v3 Adapter (new in v0.6.0a1)

- [x] `DocusaurusAdapter` satisfies the `@runtime_checkable` `BaseAdapter` protocol
- [x] `baseUrl` and `routeBasePath` extraction via static parsing (zero Node.js — Pillar 2)
- [x] Ghost Route mapping for locale entry points (`/it/`, `/`) verified
- [x] `from_repo()` auto-discovers `docusaurus.config.ts` / `.js`
- [x] `classify_route()` marks `_`-prefixed files as `IGNORED`
- [x] Frontmatter `slug:` resolution (absolute and relative)
- [x] `.md` and `.mdx` source file handling
- [x] i18n locale tree discovery (`i18n/{locale}/docusaurus-plugin-content-docs/current/`)
- [x] Dynamic config detection (`async`, `import()`, `require()`) with graceful fallback
- [x] 65 dedicated tests across 12 test classes

### 2b. Metadata-Driven Routing (new in v0.6.0a2)

- [x] `RouteMetadata` dataclass and `get_route_info()` on `BaseAdapter` protocol
- [x] All 4 adapters implement the metadata API
- [x] `build_vsm()` prefers metadata path, falls back to legacy `map_url()` + `classify_route()`
- [x] Shield IO Middleware: `safe_read_line()` scans frontmatter through Shield before parsing

### 2c. Adapter Inventory

| Adapter | LOC | Status |
| :--- | :---: | :---: |
| MkDocs | 698 | ✅ |
| Docusaurus v3 | 589 | ✅ |
| Zensical | 324 | ✅ |
| Vanilla | 92 | ✅ |
| Factory + cache | 164 | ✅ |

---

## 3. The Obsidian Bastion Gate (Layered Exclusion)

- [x] `ExclusionManager` — 4-level hierarchy (L1 System → L2 VCS → L3 Config → L4 CLI)
- [x] L1 System Guardrails immutable (`.git/`, `node_modules/`, etc.)
- [x] L2 VCS Ignore Parser — Pure Python `.gitignore` interpreter with pre-compiled regex
- [x] L3 Config — `excluded_dirs` / `excluded_file_patterns` from `zenzic.toml`
- [x] L4 CLI — `--exclude-dir` / `--include-dir` repeatable flags
- [x] `exclusion_manager` parameter **mandatory** on all scanner/validator entry points
- [x] 57 dedicated tests (677 lines in `test_exclusion.py`)

---

## 4. The Tabula Rasa Gate (Universal Discovery)

- [x] **Every** `rglob()` call removed from the entire codebase
- [x] All file iteration via `walk_files()` / `iter_markdown_sources()` in `discovery.py`
- [x] 168 call sites updated across 13 test files
- [x] No `Optional[ExclusionManager]` — `TypeError` at call time if missing

---

## 5. Security Hardening Gate

- [x] **F2-1:** Lines > 1 MiB truncated before Shield regex matching (ReDoS prevention)
- [x] **F4-1:** `_validate_docs_root()` rejects `docs_dir` escaping repo root (Exit Code 3)
- [x] **Adapter Cache:** Module-level dict keyed by `(engine, docs_root, repo_root)`, thread-safe
- [x] **Shield IO Middleware:** Frontmatter lines scanned before any parser processes them
- [x] **ZRT-006:** Unicode Cf character stripping in Shield normalizer (zero-width bypass)
- [x] **ZRT-006:** HTML entity decoding in Shield normalizer (`&#NNN;` bypass)
- [x] **ZRT-007:** HTML/MDX comment stripping in Shield normalizer (interleaving bypass)
- [x] **ZRT-007:** 1-line lookback buffer `scan_lines_with_lookback()` (split-token bypass)
- [x] **Red Team:** 11 Blood Sentinel jailbreak vectors tested — all blocked
- [x] **Red Team:** DoS resilience verified (10MB lines, 5000 files, 50-level nesting)

---

## 6. Clean Harbor Gate (Repo Hygiene)

- [x] `mkdocs.yml` — physically deleted
- [x] `overrides/` — physically deleted
- [x] `scripts/generate_docs_assets.py` — physically deleted
- [x] `scripts/generate_hero_specimen.py` — physically deleted
- [x] `scripts/generate_social.py` — physically deleted
- [x] `.github/workflows/deploy-docs.yml` — physically deleted
- [x] `.github/workflows/zenzic.yml` — physically deleted
- [x] `docs/` fully migrated to `zenzic-doc` repository
- [x] `noxfile.py` — doc sessions removed
- [x] MkDocs plugin relocated to `zenzic.integrations.mkdocs`

---

## 7. Architectural Purity Gate (Pillar 2)

- [x] `zenzic serve` — removed entirely
- [x] Zero `subprocess.run()`, `os.system()`, or shell calls in codebase
- [x] Docusaurus config parsed as text, not via Node.js
- [x] `.gitignore` interpreted in Pure Python, not via `git check-ignore`
- [x] Core free of engine-specific imports

---

## 8. Quality Gates

- [x] `pytest` — 1046 tests passing, 0 failed
- [x] `ruff check src/` → 0 violations
- [x] `reuse lint` → compliant
- [x] `pip install -e .` → `zenzic --help` outputs usage
- [x] `uv run zenzic --version` → `Zenzic v0.6.1rc2`

---

## 9. Docusaurus Validation (zenzic-doc)

- [x] `zenzic check all --engine docusaurus` → exit code 0
- [x] Zero CONFLICT routes
- [x] `zenzic-doc` has `release-docs.yml` workflow for Cloudflare Pages deploy
- [x] `release-docs.yml` has `deployments: write` permission (fixed in `fix/deploy-permissions`)

---

## 10. Performance Benchmark

| Scenario | Result |
| :--- | :--- |
| 5,000 files, 100 VCS patterns | 626 ms |
| RSS memory delta | 0 MB |

---

## 11. RC2 Gate Decision

- [x] All gates (§§ 2–9) verified
- [x] Benchmark § 10 within acceptable thresholds
- [x] Operation Obsidian Stress completed — 4 Shield bypasses sealed
- [x] Documentation Reality Sync — 6 drift items corrected
- [x] CI pipeline green on `main`

**Decision:** ✅ RC2 approved — `v0.6.1rc2` tagged and published to PyPI

---

*"Il Bastione non si fida dell'assenza di attacchi — si fida della resistenza verificata."*
— Senior Tech Lead
