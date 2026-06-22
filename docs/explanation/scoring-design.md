---
sidebar_label: Scoring Design
description: "Design rationale, worked example, and CLI output guide for the Zenzic Documentation Quality Score."
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Scoring Design

## Design Rationale

The Zenzic Documentation Quality Score (DQS) is deliberately non-forgiving on Security and Governance. The algorithm encodes the principle that:

- A document set with leaked credentials is not a quality product at any score.
- A document set with uncontrolled brand decay cannot exceed 70/100, regardless of its link integrity.

Security violations produce an immediate score of 0, bypassing all other computation. Governance violations receive exponential amplification above 10 occurrences, and a full Governance-bucket wipe caps the total score at 70.

### Dual-Gate Architecture

`fail_under` and `suppression_cap` operate as **orthogonal constraints** evaluated independently:

- **Score gate:** `score < fail_under` → `zenzic score` exits with code 1
- **Governance cap:** `|Fₛ| > suppression_cap` → `zenzic score` exits with code 1

A hybrid policy such as `fail_under = 90`, `suppression_cap = 30` enforces: "Overall quality must never drop below 90/100, *and* regardless of score, no more than 30 suppressed defects are ever tolerated."

Because every suppression deducts 1 point (flat-cost model), the **maximum achievable score** for a repository is:

$$\text{Max Achievable Score} = 100 - |F_s|$$

where $|F_s|$ is the total active suppression count. Configuring `fail_under > 100 - suppression_cap` creates a mathematical contradiction. Safe rule: `fail_under` ≤ `100 - suppression_cap`.

## Worked Example {#example}

**Scenario:** A repository has 2 broken links (Z101), 3 orphan pages (Z402), 5 untagged code blocks (Z505), and 15 Z601 brand violations, with 8 active suppressions (cap = 30).

**Stage 1 — Security Gate:** No Z2xx findings → continue.

**Stage 2 — Penalty Table:**

| Tier | Cap | Deduction | cat_pts |
| :--- | ---: | ---: | ---: |
| Structural | 30 | 2 × 8.0 = 16.0 | 14.0 |
| Navigation | 25 | 3 × 4.0 = 12.0 | 13.0 |
| Content | 20 | 5 × 1.0 = 5.0 | 15.0 |
| Governance | 25 | 15 × 2.0 = 30.0 → cap to 25 | 0.0 |

$S_{\text{base}} = 14 + 13 + 15 + 0 = 42$

**Stage 3 — Governance Escalation:** 15 Z601 violations → $n_{\text{excess}} = 5$ → multiplier $= 2^{5/5} = 2.0$ → deduction $= 30 \times 2 = 60 \to \min(60, 25) = 25$. Brand bucket = 0.

**Stage 4 — Gravity Cap:** $\text{cat\_pts}_{\text{brand}} = 0$ → $S_{\text{gravity}} = \min(42, 70) = 42$.

**Stage 5 — Suppression Debt:** $n = 8$ suppressions → flat-cost: $\omega_{\text{debt}} = 8$.

$$S_{\text{final}} = \max(0,\; 42 - 8) = \mathbf{34}$$

## Reading the CLI Output {#cli-output}

Running `zenzic score` displays a **Quality Breakdown Ledger** that exposes every arithmetic step — from raw per-tier penalties to the applied cap, the Gravity Cap adjustment, suppression debt, and the final score.

```text
✨ Quality Score: 65/100

╭─ Quality Breakdown ──────────────────────────────────────╮
│   Category     Issues  Weight  Raw Pts  Applied Pts      │
├──────────────────────────────────────────────────────────┤
│ ✓ structural      0      30%      0           0          │
│ ✓ navigation      0      25%      0           0          │
│ ✗ content         2      20%     -4          -4          │
│ ✗ brand          15      25%    -30         -25 (CAPPED) │
├──────────────────────────────────────────────────────────┤
│   Σ Subtotal                                71           │
╰──────────────────────────────────────────────────────────╯
  ! Technical Debt (6 suppressions)          -6 pts
  = Final Quality Score                      65 / 100
```

**Column guide:**

| Column | Meaning |
| :--- | :--- |
| **Raw Pts** | Post-escalation deduction before the category cap, shown as a negative value (or `0`). |
| **Applied Pts** | Deduction actually subtracted, capped at the tier maximum. |
| **(CAPPED)** | The raw deduction exceeded the tier cap and was truncated. |
| **Σ Subtotal** | Sum of all retained `cat_pts` values before Gravity Cap and Suppression Debt. |

**When the Gravity Cap fires** (Brand bucket = 0), an extra line appears between Σ Subtotal and Technical Debt:

```text
│   Σ Subtotal                                75           │
╰──────────────────────────────────────────────────────────╯
  ! Gravity Cap Enforcement (Brand = 0)       -5 pts
  ! Technical Debt (0 suppressions)            0 pts
  = Final Quality Score                       70 / 100
```

The arithmetic is always explicit: **Σ Subtotal − Gravity Cap − Suppression Debt = Final Score**.

## Result Interpretation

### Informational Findings

Informational findings are non-blocking diagnostics for visibility and observability:

- They do not reduce DQS.
- They never trigger the Security Override.
- In SARIF they are emitted at `note` level.

Typical examples: Z106 (`CIRCULAR_LINK`), Z114, Z906.

### Label Semantics: `[MANAGED DEBT]` and `[EXTENDED DEBT]`

- `[MANAGED DEBT]`: active suppressions are present and the project remains on sovereign cap profile (`suppression_cap <= 30`).
- `[EXTENDED DEBT]`: active suppressions are present while using an expanded cap profile (`suppression_cap > 30`).

These labels describe governance posture and help reviewers track suppression growth over time.

### Suppression Posture Inspection

```bash
zenzic score        # view current suppression posture in the Breakdown Ledger
zenzic check all --audit   # view all findings without active suppressions applied
```
