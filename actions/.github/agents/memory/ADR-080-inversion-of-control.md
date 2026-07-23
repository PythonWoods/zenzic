<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-080: Inversion of Control for Dynamic Frameworks (The Bridge Architecture)

**Date:** 2026-06-12
**Status:** Accepted (To be implemented in v0.12.0)
**Context:** Docusaurus (and similar frameworks) generate routes dynamically at runtime using JavaScript/TypeScript (e.g., `sidebars.ts` generated indices, Webpack aliases). Zenzic is a pure Python static analyzer (Pillar 3). Attempting to evaluate or reverse-engineer TypeScript logic using Python regex/heuristics leads to fragile code, infinite maintenance loops, and violates absolute determinism (Pillar 1).

**Decision:**
We will NOT attempt to build a TypeScript parser in Python. If the mountain will not come to Muhammad, Muhammad must go to the mountain.
We will implement an **Inversion of Control (Bridge Architecture)**:

1. **The Plugin:** We will develop a native TypeScript plugin (`docusaurus-plugin-zenzic`).
2. **The Dump:** During `npm run build` or `npm start`, this plugin will hook into the Docusaurus lifecycle, extract the 100% accurate, final Virtual Site Map (VSM), and dump it to a physical file: `.zenzic-vsm.json`.
3. **The Consumption:** When `zenzic check all` runs, the Python engine will detect `.zenzic-vsm.json`. It will bypass its own native `DocusaurusAdapter` heuristics and ingest the JSON as the Absolute Truth.

**Consequences:**

- Zenzic remains pure Python (Zero Subprocess).
- Zero heuristic technical debt.
- False positives on dynamic routes drop to mathematically zero.
