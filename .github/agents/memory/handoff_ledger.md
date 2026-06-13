<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# ZENZIC: ARCHITECTURAL HANDOFF LEDGER

**TIMESTAMP:** 2026-06-10
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

- **Dynamic Sidebar Categories:** Zenzic operates strictly via static AST/I/O analysis (Pure Python). It cannot evaluate `sidebars.js/ts` to dynamically inject generated `/category/` routes into the VSM. Links to these virtual routes will yield Z101. Users should suppress Z101 on these specific links via `.zenzic.local.toml`.
  - See ADR-080-inversion-of-control.md for the permanent strategic solution (The Bridge Architecture).
- **React Runtime Invisibility:** Zenzic's AST parser cannot see DOM nodes (e.g., `id` attributes) generated dynamically by React components (like `<APITable>`). Links targeting these nodes will yield `Z102`.
- **MDX Bundler Invisibility:** Zenzic parses files in isolation. It does not resolve MDX `import` statements to aggregate anchors from partials into the parent file. Links targeting partial anchors will yield `Z102`.

## 3. RECENT ARCHITECTURAL WINS (Do not regress)

- **Docusaurus Native Routing Emulation:** Full support for `routeBasePath` concatenation, Frontmatter `slug` absolute/relative parsing, and Blog Date Extraction to map Docusaurus URLs into the Virtual Site Map without false positive broken links.
- **External Air-Gap Policy:** AI Agents are strictly forbidden from executing upstream contributions to third-party repositories. The AI drafts the payload; the Human Tech Lead executes the submission.
- **Python 3.12+ RE2 Compatibility:** Custom `translate_glob_to_re2` implemented.
- **DX Redesign:** Visual Progress Bar and `--breakdown` flag implemented.
- **Path-Aware Exclusion Engine:** `excluded_dirs` now supports `.gitignore` slash semantics for `repo_root`-relative targeting.
- **Monorepo Scalability:** Docusaurus dynamic root resolution implemented and baseline established.
- **AST Parser Fixes:** Z104 ignores footnotes (`[^1]:`). Z102 strips attribute lists (`{...}`) and supports explicit block anchors. Z302 tracks image nodes.
- **YAML Validator:** `_PermissiveSafeLoader` tolerates PyYAML custom tags (`!!python/name:`, `!ENV`) to support MkDocs configurations without throwing Z503.
- **CLI DX:** `--ci` is a macro-flag that implicitly sets `no_header = True`.
- **Z501 (Scunthorpe):** Default placeholder patterns are strictly `\bTODO\b` and `\bFIXME\b` using explicit RE2 word boundaries.

## 4. ACTIVE TARGET: Next Sprint

The next development cycle MUST focus exclusively on the following target:

- [ ] Implement ADR-080 (The Bridge Architecture) via `docusaurus-plugin-zenzic`.

## 5. KNOWN TECHNICAL DEBT (Backlog)

- **OBOE (Off-By-One Error):** The snippet validator calculates error line numbers as `Block Start Line + Snippet Error Line`. There is a known +1 offset error (e.g., TOML error reported on line 220 instead of 219). Needs fixing in the AST node line extraction.
