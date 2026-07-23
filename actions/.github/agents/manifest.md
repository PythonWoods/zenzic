# ZENZIC: ARCHITECTURAL MANIFESTO & ENGINEERING LEDGER

**CLASSIFICATION:** SYSTEM CONSTITUTION (TIER 0)
**TARGET:** ENGINEERING ONBOARDING (AI / HUMAN TEAMS)
A: STATUS: LOCKED (Ecosystem v0.10.x)

## 1. PRODUCT IDENTITY (VISION & MISSION)

**Definition:** Zenzic is an *Engine-agnostic Markdown static analyzer & credential scanner*.
**Mission:** Apply the same mathematical, structural, and security rigor to technical documentation as is reserved for compiled source code. Prevent Documentation Drift and the exposure of secrets (Supply Chain Leaks) directly at the Continuous Integration (CI) boundary.
**Vision:** Guarantee the absolute integrity of the documentation tree through a deterministic engine, free from heuristic-derived false positives, and independent of complex configurations.

---

## 2. THE FIVE PILLARS (CORE PILLARS)

Every line of code written in Zenzic must obey these five axioms. If a PR violates a Pillar, it is rejected with Exit Code 1.

1. **ABSOLUTE DETERMINISM:** Given the same input, the output is identical. The engine does not query LLMs and does not use probabilistic logic. External network calls are governed by a local atomic cache to eliminate CI fluctuation.
2. **ZERO-CONFIG DEFAULT:** The engine operates out-of-the-box. It automatically detects the build engine (Docusaurus, MkDocs, Zensical) via *Auto-Discovery* and applies system exclusions natively.
3. **ZERO SUBPROCESS (PURE PYTHON):** The ecosystem operates entirely within the Python runtime (≥ 3.10). No dependencies on Node.js, precompiled binaries, or external shell calls (`os.system`).
4. **ZERO TECHNICAL DEBT (ZERO-DBT):** No workarounds are tolerated. If a test fails, fix the code, do not disable the test. Dead code and duplicated UI components are strictly forbidden.
5. **RADICAL UNAWARENESS (ADR-075):** Zenzic ignores the existence of external consumers. Its sole task is to emit standardized payloads (JSON / SARIF / GitHub Annotations).

---

## 3. GOLDEN RULES AND INVIOLABLE CONSTRAINTS (ADRs)

### ADR-012: Namespace Contract (The Code Registry)

Error codes (Z-Codes) are the public API of Zenzic.

- `Z1xx - Z9xx`: Exclusively reserved for the Core Engine.
- `<plugin-id>:code`: Reserved for official Adapters/Plugins.
- `ZZ-*`: Reserved for Custom Rules. Validation enforces the `ZZ-` prefix to prevent *Namespace Hijacking*.

### ADR-013: RE2 Rigor (ReDoS Prevention)

The standard Python `re` module is **STRICTLY FORBIDDEN**. Zenzic exclusively uses the Google RE2 C++ binding (DFA without backtracking). This guarantees an $O(N)$ linear parsing complexity and makes *Regular Expression Denial of Service* (ReDoS) attacks mathematically impossible.

### ADR-020: Mirror Law (Bilingual Parity)

La Mirror Law (Parità Bilingue EN/IT) si applica ESCLUSIVAMENTE alla manualistica utente in docs/. Tutti i file di governance (README, CONTRIBUTING, CHANGELOG) e la Landing Page sono rigorosamente English-Only.

### ADR-037: Agnostic Prose & Temporal Decoupling

- **No Codenames:** Using geological release names in public prose is forbidden.
- **Atemporality:** The documentation describes the *absolute present*. Hardcoded versions in prose or visual assets (e.g., Social Cards) are forbidden.

---

## 4. THE MATHEMATICAL MODEL (FLAT-COST DQS)

The Document Quality Score (DQS) is not an aesthetic metric; it is a punitive algorithm.
The calculation starts at 100 and subtracts points based on 4 weighted categories (Structural, Navigation, Content, Brand & Gov).

**Mathematical Invariants:**

1. **Flat-Cost Suppression:** Every `{/* zenzic:ignore */}` directive costs **exactly 1 point** of technical debt.
2. **Orthogonal Constraints:** The CI fails if the score drops below `fail_under` **OR** if the number of suppressions exceeds the `suppression_cap`. The two limits are orthogonal.
3. **Security Override:** Any security violation (Z201, Z203, Z204) unconditionally forces the DQS to **0/100** (Exit Code 2 or 3).
4. **Fail-Visible:** No `info`-level finding can subtract points silently (Silent Penalty).

---

## 5. ENGINE TOPOLOGY (I/O, NETWORK & MERGE SEMANTICS)

### The I/O Choke Point (Discovery)

The use of `Path.rglob()` is **forbidden** to prevent I/O Thrashing. Ingestion maintains a sequential $O(N)$ complexity, scaled in wall-time via parallel process pools.

### Asynchronous Network I/O & Atomic Caching

External link validation operates via `asyncio` and `httpx`. To guarantee determinism in CI, 200 OK results are saved in a local cache (`.zenzic_cache/external_links.json`) with atomic writing and a configurable TTL. The *Smart Fallback* (HEAD $\rightarrow$ GET stream) prevents over-fetching.

### Additive Deep Merge (Local TOML)

The `.zenzic.local.toml` file overrides the global configuration with **ADDITIVE** semantics (Set Union) for critical lists. A local file can only *add* security rules, never remove them.

---

## 6. CI INTEGRATION & TELEMETRY

### Native CI & Progressive Adoption

Zenzic natively supports CI/CD pipelines via the `--format github-annotations` flag, injecting errors directly into Pull Requests. Adoption in legacy repositories is governed by the `--only` parameter, which enables **Progressive Adoption** by discarding unwanted findings at the engine level.

### Dual-Badge Telemetry

The ecosystem exposes two public truths:

1. **CI Status Badge:** Demonstrates the real-time Pass/Fail status of the pipeline.
2. **DQS Score Badge:** A "Time-Traveling Badge" crystallized in the commit. The *Badge Freshness Gate* (`zenzic score --check-stamp`) fails the CI if the badge in the README does not mathematically match the reality of the codebase.

---

## 7. OPERATIONAL PROTOCOLS (FOR THE TEAM)

1. **Diátaxis Purity:** Documentation must strictly respect the 4 quadrants of the Diátaxis framework (Tutorials, How-To, Explanation, Reference). Mixed-intent "Frankenstein Pages" and FAQs are architecturally forbidden.
2. **D.I.A. (Documentation Impact Analysis):** No PR altering the CLI behavior can be merged without simultaneous updates in `zenzic-doc`.
3. **Truth-Seeker Audit:** When reviewing documentation, textual search is not enough. Every claim must be verified by reading the execution tree of the real Python code or the fixtures.
4. **Hostile Precision (Voice):** We do not write to please; we write to instruct. The user interface must convey "Hostile Precision": sharp geometries, raw terminals, zero marketing fluff.

---
**END OF MANIFESTO.**
*Any deviation from this document is classified as Technical Debt and will be intercepted by the Quality Gate.*
