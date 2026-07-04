---
sidebar_label: "Scoring System"
sidebar_position: 4
description: "The Deterministic Quality Score — conceptual model, penalty table, running the score, and CI enforcement patterns."
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Scoring System — The Deterministic Quality Score

> *"A Exclusion Zone must be able to say exactly how solid its pier is."*

**A broken link degrades user experience. A leaked credential requires immediate incident response. A score of 97 means three findings remain unresolved.**

The Deterministic Quality Score (DQS) is a **single 0–100 value** computed from the
concrete issue count across every check. Zero issues means 100/100. No partial credit,
no rounding favors, no surprises. Given the same source files and the same version of
Zenzic, the score is identical on every machine — no sampling, no weighting by file
age, no subjective component.

For exact formulas and the mathematical specification, see the
[Scoring Algorithm Reference](../reference/scoring-algorithm.md).

---

## What the Score Measures

The Quality Score is a **weighted composite** of four check categories. Each category
maps directly to a `zenzic check` sub-command and to the `Zxxx` finding codes it emits.

| Category | Command | Finding Codes | Weight |
|----------|---------|---------------|---------|
| **Structural Integrity** | `zenzic check links [PATH]` | [Z101], [Z102], [Z104], [Z105], [Z107], [Z108] | **30 %** |
| **Content Excellence** | `zenzic check all [PATH]` | [Z403], [Z501], [Z502], [Z503], [Z505] | **20 %** |
| **Navigation** | `zenzic check orphans [PATH]` | [Z301], [Z302], [Z303], [Z401], [Z402] | **25 %** |
| **Brand & Assets** | `zenzic check assets [PATH]` | [Z404], [Z405], [Z406], [Z601] | **25 %** |

[Z101]: ../reference/finding-codes.md#z101
[Z102]: ../reference/finding-codes.md#z102
[Z104]: ../reference/finding-codes.md#z104
[Z105]: ../reference/finding-codes.md#z105
[Z107]: ../reference/finding-codes.md#z107
[Z108]: ../reference/finding-codes.md#z108
[Z301]: ../reference/finding-codes.md#z301
[Z302]: ../reference/finding-codes.md#z302
[Z303]: ../reference/finding-codes.md#z303
[Z402]: ../reference/finding-codes.md#z402
[Z501]: ../reference/finding-codes.md#z501
[Z502]: ../reference/finding-codes.md#z502
[Z503]: ../reference/finding-codes.md#z503
[Z505]: ../reference/finding-codes.md#z505
[Z405]: ../reference/finding-codes.md#z405
[Z406]: ../reference/finding-codes.md#z406
[Z601]: ../reference/finding-codes.md#z601
[Z401]: ../reference/finding-codes.md#z401
[Z403]: ../reference/finding-codes.md#z403
[Z404]: ../reference/finding-codes.md#z404

**Reading the weights.** The two largest weights — Structural and Governance — reflect
Zenzic's design principle: correctness (links that actually resolve) and trust (brand
and contract compliance) matter more than aesthetic content quality.

!!! danger "Security Override"
    If any security finding is detected — Z201 (credential scanner), Z202, or Z203 (path traversal guard) —
    the Quality Score **collapses to 0/100 unconditionally**. A documentation source that
    is actively leaking a credential cannot receive a Quality Score.

---

## Penalty Calibration Philosophy {#penalty-calibration}

Penalties are assigned to one of three severity tiers, independent of which category they sit in:

| Tier | Examples | Points |
|---|---|---|
| Critical | Z503 (snippet error) | 10.0 |
| High | Z301, Z402 (broken link, orphan page) | 3.0 – 4.0 |
| Standard | Z104, Z401, Z403 … | 1.0 – 2.0 |

A **Critical** penalty (10 pts) signals that the content is actively harmful to readers
(a broken code example). A **High** penalty signals a structural defect that a reader
will directly encounter (a dead link, an unreachable page). A **Standard** penalty
signals a quality deficit that degrades the experience over time.

> For the full per-code penalty lookup table, see [Scoring Algorithm — Penalty Reference Table](../reference/scoring-algorithm.md#penalty-table).

---

## Category Cap Invariant

Category deductions are bounded by the category's weight:

- Structural cap: **30 pts** (30% × 100)
- Content cap: **20 pts** (20% × 100)
- Navigation cap: **25 pts** (25% × 100)
- Brand cap: **25 pts** (25% × 100)

**Example:** 100 × Z505 (1.0 pt each) generates 100 pts of potential deduction
against the Content category — but the cap limits the actual loss to 20 pts.
The other three categories remain unaffected: **80/100 total**.

### Score vs. Gate Separation

The Score and the `fail_under` threshold are **independent**:

- **Score (the Metric):** Objective quality measurement bounded by Category Caps.
- **`fail_under` (the Gate):** Your enforcement policy in `.zenzic.toml`.

A score of 70/100 with `fail_under = 80` **still exits 1**. The Category Cap prevents
a noisy violation type from masking structural health — it does not weaken your gate.

The final 0–100 score is the sum of weighted category contributions:

$$
\text{score} = \left\lfloor \sum_i \max\bigl(0,\ w_i \times 100 - \text{deductions}_i\bigr) \right\rceil
$$

---

## Reading Your Score

| Score | Interpretation |
|---|---|
| 95 – 100 | Excellent — minimal residual findings |
| 80 – 94 | Good — some non-critical findings |
| 60 – 79 | Fair — meaningful quality gaps |
| 40 – 59 | Poor — systematic issues requiring attention |
| < 40 | Critical — documentation integrity at risk |

---

## Score Observability {#score-observability}

The score output (`zenzic score`) exposes a Quality Breakdown Ledger that shows every arithmetic step: raw per-tier deductions, applied caps, Gravity Cap adjustment, suppression debt, and the final integer. This explicitness is by design — the score is not a black-box rating but a verifiable arithmetic result.

> For CLI command reference and CI integration patterns, see [Handle Technical Debt](../how-to/handle-technical-debt.md) and [Scoring Design](./scoring-design.md).

---

## Suppression and Governance Gates

Two mechanisms interact with the score differently.

**Suppression (`.zenzic-ignore`)** — removes a specific finding from the output. The
suppressed finding is not penalised. Use suppression only for deliberate, documented
exceptions.

**Governance gates** — certain codes trigger a hard gate: `zenzic
check` exits with code 2 regardless of the DQS. The DQS itself is not affected because
gate codes are excluded from the penalty matrix by design. A project can score 100 and
still fail the gate if a gate-level violation is present. (Note: `Z602 I18N_PARITY` was
permanently deactivated in v0.14 and no longer triggers this gate.)

---

## Quality Regression — Z504

When `zenzic diff` detects a score drop, it emits **[Z504 QUALITY_REGRESSION][z504]**
as a finding. This is the only finding code that bridges the scoring layer and the
finding layer — it means: *"something you changed made the score worse."*

[z504]: ../reference/finding-codes.md#z504

Z504 is not weighted into the score itself (that would be circular). It is the
signal that communicates *which commit introduced a regression*.

---

## The Exclusion Zone Guarantee {#exclusion-zone-guarantee}

When `zenzic score` returns 100/100, it is a formal guarantee that:

- Every internal link resolves (zero Z101/Z102/Z103/Z104/Z105)
- Every anchor reference resolves (zero Z107)
- Every page is reachable from at least one navigation entry point (zero Z402)
- Every code snippet is syntactically valid (zero Z503)
- No placeholder content exists (zero Z501)
- No untagged code blocks exist (zero Z505)
- No unused assets exist (zero Z405)
- No nav contract violations exist (zero Z406)
- No obsolete brand references exist (zero Z601)
- The credential scanner found no credentials in any file (zero Z201 — implicit, collapses score to 0)

<!-- Terminal output: run `uvx zenzic check all` -->

This is the **Zenzic Audit Badge**: the state where the documentation is structurally
complete, content-clean, and security-verified.

> **Carry the Seal in your README:** once you reach 100/100, run `zenzic score --save`
> and add the dynamic score badge to your project. Let contributors see the standard
> they're committing to. See [Official Badges](../how-to/add-badges) for copy-paste badge URLs.

---

## Engineering Invariants

The Quality Score is the operational proof of Zenzic's [Three Pillars](why-zenzic.md#defence-trinity):

**1. Lint the Source, Not the Build.**
The score is computed from raw Markdown source analysis — never from HTML output
or a running web server. The 30% structural weight rewards a source that is internally
coherent before any build step runs.

**2. No Subprocesses.**
`compute_score()` in `core/scorer.py` is a pure Python function — no shell calls,
no `subprocess.run`, no network requests. It receives a `findings_counts: dict[str, int]`
mapping and returns a `ScoreReport`. This guarantees identical results across every OS
and Python version in the CI matrix (ubuntu / windows / macos × Python 3.10–3.14).

**3. Pure Functions First.**
`compute_score()` has no side effects. `save_snapshot()` is the only I/O function
and it is called explicitly only when the user passes `--save`. The test suite
verifies score calculations with property-based tests (Hypothesis) to guarantee
mathematical invariants.

---

## Nav Contract Integrity — Scored as Brand & Assets

What users sometimes call "Nav Isolation" is formally **Nav Contract Integrity ([Z406])**.

Z406 fires when a file declared in the engine's navigation config (e.g., a `mkdocs.yml`
`nav:` entry or similar navigation entry) does not exist on disk.
Each Z406 violation contributes to the **Brand & Assets** category (25%) using the
same per-code penalty as other scored findings (Z406: 2.0 pts per violation).

---

## Worked Example

Suppose a project has:

- 2 × Z503 SNIPPET_ERROR → 2 × 10.0 = 20.0 pts (capped at 20 — fills the Content bucket)
- 1 × Z301 DANGLING_REF → 4.0 pts (Navigation)
- 1 × Z405 UNUSED_ASSET → 3.0 pts (Brand)

```text
Structural deduction = 0
Navigation deduction = min(4.0, 25) = 4.0  → contributes 4.0 × (25/25) = 4.0 weighted
Content   deduction = min(20.0, 20) = 20.0 → contributes 20.0 × (20/20) = 20.0 weighted
Brand     deduction = min(3.0, 25)  = 3.0  → contributes 3.0 × (25/25) = 3.0 weighted

DQS = 100 − (0 + 4.0 + 20.0 + 3.0) = 73
```

The two snippet errors alone reduce the score by 20 points; fixing them recovers
the Content bucket entirely.

---

## Related

- [Scoring Algorithm Reference](../reference/scoring-algorithm.md) — formal weights,
  penalty table, and mathematical specification
- [Finding Codes](../reference/finding-codes.md) — full catalogue of all Z-codes
- [Suppression Policy](../reference/suppression-policy.md) — how suppressed findings affect the Quality Score
