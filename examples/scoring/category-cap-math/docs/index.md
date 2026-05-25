<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Category Cap Math — Index

This page demonstrates two scoring invariants introduced in Zenzic v0.8.0:

1. **Category Cap**: A single tier cannot drag the DQS below its floor.
2. **ADR-031 Gate Paradox Resolution**: Z103/Z111/Z113 now carry non-zero DQS
   penalties. See [ADR-031 Paradox](orphan.md) for details.

## Five Broken Links (Z104 × 5)

Each link below targets a file that does not exist on disk. Each triggers
Z104 FILE_NOT_FOUND (8.0 pts, Structural tier).

- [Alpha Reference](missing-alpha.md)
- [Beta Reference](missing-beta.md)
- [Gamma Reference](missing-gamma.md)
- [Delta Reference](missing-delta.md)
- [Epsilon Reference](missing-epsilon.md)

## Expected Score

| Tier | Raw penalty | Cap | cat\_pts |
| :--- | ---: | ---: | ---: |
| Structural | 5 × 8.0 = **40 pts** | 30 pts | **0 pts** |
| Navigation | 0 pts | 25 pts | **25 pts** |
| Content | 0 pts | 20 pts | **20 pts** |
| Governance | 0 pts | 25 pts | **25 pts** |

`S_base = 0 + 25 + 20 + 25 = 70`

No suppressions → `ω_debt = 0` → **DQS = 70 / 100**.

### Cap Invariant Proof

The raw Structural penalty (40 pts) exceeds the Structural cap (30 pts) by 10
pts. Without the cap, the score would be `100 − 40 = 60`. The cap ensures the
Structural bucket clamps to 0 and the 10-pt excess is discarded: DQS = **70**.
