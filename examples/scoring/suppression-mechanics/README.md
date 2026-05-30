<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Flat-Cost Suppression Model — Empirical Sandbox

Demonstrates the ADR-031 flat-cost suppression model empirically using `zenzic
score` and `zenzic check all`.

## What This Example Shows

| Property | Value |
| :--- | :--- |
| Engine | standalone |
| `suppression_cap` | 2 |
| Inline suppressions | 3 × Z105 ABSOLUTE_PATH |
| Expected DQS | 91/100 |
| Expected exit code | **1** (hard-fail: cap exceeded) |

## Setup

`.zenzic.toml` declares `suppression_cap = 2` — a hard-fail threshold.  Three
Markdown files each contain one absolute-path link suppressed inline:

```text
docs/index.md   [/deployment/overview](...)   <!-- zenzic:ignore: Z105 --> (1/3)
docs/guide.md   [/admin/api-dashboard](...)   <!-- zenzic:ignore: Z105 --> (2/3)
docs/api.md     [/auth/tokens/manage](...)    <!-- zenzic:ignore: Z105 --> (3/3)
```

Z105 ABSOLUTE_PATH carries a 2.0 pt penalty in the Structural tier.

## Score Arithmetic

| Tier | Issues | Raw penalty | cat\_pts |
| :--- | ---: | ---: | ---: |
| structural | 3 × Z105 | 3 × 2.0 = 6 pts | **24 pts** |
| navigation | 0 | 0 pts | **25 pts** |
| content | 0 | 0 pts | **20 pts** |
| governance | 0 | 0 pts | **25 pts** |

```text
S_base     = 24 + 25 + 20 + 25 = 94
ω_debt     = 3 suppressions × 1 pt each = 3
S_final    = max(0, 94 − 3) = 91
```

## Validated Output

```console
$ zenzic score

✨ Quality Score: 91/100

                 Quality Breakdown
╭──────┬────────────────┬────────┬────────┬───────╮
│  •   │ Category       │ Issues │ Weight │ Score │
├──────┼────────────────┼────────┼────────┼───────┤
│  ✘   │ structural     │      3 │    30% │  0.24 │
│  ✔   │ navigation     │      0 │    25% │  0.25 │
│  ✔   │ content        │      0 │    20% │  0.20 │
│  ✔   │ brand          │      0 │    25% │  0.25 │
╰──────┴────────────────┴────────┴────────┴───────╯
  ! Technical Debt (Suppressions): -3 pts

FAILED: suppression cap exceeded (3/2).
```

Exit code: **1** (cap exceeded, regardless of DQS value).

## Key Behavioral Differences

### `zenzic score` vs `zenzic check all`

`zenzic check all` applies inline suppression filtering: Z105 findings are
hidden from the output (the check exits with no findings visible).  The cap
gate still fires, raising exit code to 1.

`zenzic score` does **not** filter suppressed findings from the category
penalty calculation.  Each suppressed Z105 finding still subtracts 2.0 pts
from the Structural bucket.  The suppression then adds 1 pt of debt on top:

| Cost component | Source | Amount |
| :--- | :--- | ---: |
| Structural penalty | 3 × Z105 × 2.0 pts | **6 pts** |
| Suppression debt | 3 suppressions × 1 pt (ADR-031 flat-cost) | **3 pts** |
| Total DQS reduction | | **9 pts** |

### Hard-Fail Gate

`suppression_cap = 2` is a **hard-fail threshold**, not a budget.  The DQS
value is computed normally (91/100) and only then is the cap check applied.
Exit code 1 is mandatory when count > cap, regardless of how high the score is.

Removing one suppression (count = 2 = cap) would restore exit code 0.
