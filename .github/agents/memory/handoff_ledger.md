<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# ZENZIC: ARCHITECTURAL HANDOFF LEDGER

**TIMESTAMP:** 2026-06-13
**TARGET AUDIENCE:** NEW AI INSTANCE (MAKER/ORCHESTRATOR)

> **THE GOLDEN RULE OF MEMORY (OUROBOROS PROTOCOL):**
> At the conclusion of every sprint, bugfix, or architectural shift, the acting AI Agent MUST update this handoff_ledger.md file. Furthermore, this exact file MUST be synchronized identically across ALL THREE repositories (zenzic, zenzic-doc, zenzic-action). Failure to update and sync the ledger is classified as Tier 0 Technical Debt (Amnesia).

## 1. CURRENT STATE (CRISTALLIZZATO)

- **Versioning Law:** `zenzic` and `zenzic-doc` MUST share the exact same SemVer (e.g., v0.10.x). `zenzic-action` has an independent lifecycle (e.g., v1.x.y) but its `action.yml` default MUST point to the latest Core version.
- **Core Engine:** `v0.12.0-prep`
- **Documentation:** `v0.12.0-prep`
- **GitHub Action:** `v1.4.0` (Floating tag `@v1` forced to this commit)
- **Documentation:** Diátaxis framework strictly enforced. Legacy `<ZenzicOutput>` eradicated, 100% `<ZenzicTerminal>` usage.
- **Governance:** Enterprise-grade. DCO (`-s`) and Cryptographic Signatures (`-S`) are mandatory and enforced by GitHub Branch Protection. PRs require an approved Issue (Issue-First Policy).

## 2. ARCHITECTURAL BOUNDARIES

- **Ontological Incompatibility (Docusaurus Eradicated):** Zenzic strictly targets Pure Static Documentation Engines (e.g., MkDocs, Sphinx, Zensical). SPA/MDX frameworks that generate DOM elements at runtime via JavaScript/React (e.g., Docusaurus) are ontologically out-of-scope, as they mathematically prevent zero-false-positive static analysis. Support for Docusaurus has been completely removed in v0.12.0.

## 3. RECENT ARCHITECTURAL WINS (Do not regress)

- **External Air-Gap Policy:** AI Agents are strictly forbidden from executing upstream contributions to third-party repositories. The AI drafts the payload; the Human Tech Lead executes the submission.
- **Python 3.12+ RE2 Compatibility:** Custom `translate_glob_to_re2` implemented.
- **DX Redesign:** Visual Progress Bar and `--breakdown` flag implemented.
- **Path-Aware Exclusion Engine:** `excluded_dirs` now supports `.gitignore` slash semantics for `repo_root`-relative targeting.

- **AST Parser Fixes:** Z104 ignores footnotes (`[^1]:`). Z102 strips attribute lists (`{...}`) and supports explicit block anchors. Z302 tracks image nodes.
- **YAML Validator:** `_PermissiveSafeLoader` tolerates PyYAML custom tags (`!!python/name:`, `!ENV`) to support MkDocs configurations without throwing Z503.
- **CLI DX:** `--ci` is a macro-flag that implicitly sets `no_header = True`.
- **Z501 (Scunthorpe):** Default placeholder patterns are strictly `\bTODO\b` and `\bFIXME\b` using explicit RE2 word boundaries.

## 4. ACTIVE TARGET: Next Sprint

The next development cycle MUST focus exclusively on the following target:

- [x] Surgical Eradication of Docusaurus completed (v0.12.0).
- [ ] Tactical Bridge: zenzic-doc will migrate to MkDocs Material to immediately restore CI linting and ADR-020 (i18n) compliance.
- [ ] Strategic Goal: Final migration to Zensical is deferred until Zensical achieves i18n parity.

## 5. KNOWN TECHNICAL DEBT (Backlog)

- **OBOE (Off-By-One Error):** The snippet validator calculates error line numbers as `Block Start Line + Snippet Error Line`. There is a known +1 offset error (e.g., TOML error reported on line 220 instead of 219). Needs fixing in the AST node line extraction.
