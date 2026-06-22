---

description: "The Zenzic Evolution Policy governing how project rules, architecture, and the Three Pillars can change."
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Evolution Policy: The Immutable Pillars

> *"The Three Pillars do not evolve. They protect the things that do."*

---

The Zenzic Evolution Policy governs how the project changes. Its first principle
is that **not everything can change** — and the Three Pillars are the things
that cannot.

---

## 1. The Immutability Contract

The Three Pillars are not preferences. They are the structural requirements of the
Privacy Gate. A Zenzic without Pillar II (Zero Subprocesses) is not a faster Zenzic
— it is a different tool that has abandoned its trust model.

### What "Immutable" Means

| Pillar | Can Be Relaxed? | Consequence of Relaxation |
| :--- | :---: | :--- |
| **I — Lint the Source, Not the Build** | ❌ No | Breaks the pre-build analysis guarantee |
| **II — Zero Subprocesses** | ❌ No | Breaks the Zero-Trust execution model |
| **III — Pure Functions First** | ❌ No | Breaks reproducibility and auditability |

A change that violates Pillar II or Pillar III — even temporarily, even for a
well-motivated reason — requires:

1. **A Major version increment**
2. **A formal [ADR](../adr-vault.md)** added to the Zenzic Ledger
3. **A structural stress-test** of the proposed replacement architecture

This ensures that the trust model is not abandoned lightly or by accident.

---

## 2. What Can Evolve (Lightweight Procedure)

**Operational Standards** — quality gate thresholds, coverage floors, benchmark
targets, finding code messages (not semantics) — evolve simply by documenting the rationale in a commit and updating the relevant `[POLICIES]` or `[ARCHITECTURE]` section in the Ledger.

Examples of Operational Standard changes:

- Raising the coverage floor from 80% to 85%
- Adjusting mutation score targets
- Updating a finding code message (text only, not semantics)
- Adding a new `Zxxx` finding code in an existing range

---

## 3. RFC Template (for Pillar-Level Proposals)

Any proposal to amend a Three Pillars invariant must include:

1. **Current Text:** The exact `[INVARIANT]` text being challenged.
2. **Proposed Text:** The replacement wording, if any.
3. **Rationale:** Why the current invariant is architecturally insufficient or harmful.
4. **Cost:** What breaks? Which users must migrate? Which ADRs are invalidated?
5. **Alternative Analysis:** What alternatives were considered before proposing this?

A proposal without a Cost section and Alternative Analysis will not enter debate.

---

## 4. The "Convenience" Prohibition

> *"We don't accept shortcuts because of convenience."*

The following are **not** valid rationales for a Pillar amendment:

- "It's annoying to write pure functions for this rule."
- "We need to ship this subprocess call now."
- "The AI proposed a simpler architecture that bypasses Pillar II."
- "This is a temporary exception."

If a proposed change would be rejected as a pull request by a junior engineer who
has read the Zenzic Ledger once — it is not a candidate for the Evolution Policy.
It is a candidate for a code review.

---

## 5. Security Exceptions

In the event of a **Critical Security Vulnerability** requiring an emergency deviation
from a Pillar (e.g., a process isolation call during a zero-day response), a temporary exception can be made. It must be tracked with a dedicated ADR detailing the security rationale, and the architectural violation must be resolved as soon as the vulnerability is mitigated. This exception cannot be invoked for convenience or technical debt.
