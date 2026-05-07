# Content Spam Demo — Category Cap Invariant

This fixture demonstrates the **Category Cap** behaviour of the Quartz Scoring Engine (CEO-163).

It contains **100 untagged code blocks** (Z505 UNTAGGED_CODE_BLOCK) — deliberately more
violations than any real project would ever have.

## What this proves

The Content category has a maximum weight of **30 points**. Even if 100 violations generate
`100 × 1.0 = 100 pts` of potential deductions, the cap limits the actual loss to 30 pts.

The other three categories remain unaffected:

| Category | Weight | Pts | Issues |
|----------|--------|-----|--------|
| Structural | 40% | 40 | 0 |
| Content | 30% | **0** | 100 × Z505 |
| Navigation | 20% | 20 | 0 |
| Brand | 10% | 10 | 0 |
| **Total** | | **70/100** | |

## Run it

```bash
cd examples/scoring/content-spam

# Score: 70/100 (content zeroed, others intact)
zenzic score

# See all 100 Z505 findings in ruff-style flat output
zenzic check all
```
