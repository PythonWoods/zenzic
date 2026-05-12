# Z204 Privacy Gate — Example

> **Act 20** of `zenzic lab` — Enterprise Privacy Gate

Demonstrates `Z204 FORBIDDEN_TERM`: Zenzic blocks confidential internal terms
from leaking into public documentation.

## Structure

```text
z204-privacy-gate/
├── zenzic.toml            # base config (no forbidden_patterns — safe to commit)
├── .zenzic.local.toml     # overlay with forbidden_patterns (git-ignored in prod)
└── docs/
    └── index.md           # intentionally contains the forbidden terms
```

## Run it

```bash
cd examples/rules/z204-privacy-gate
zenzic check references    # EXIT 2 — Z204 fires on docs/index.md
```

## Expected findings

| File | Line | Code | Message |
|------|------|------|---------|
| `docs/index.md` | 14 | `Z204` | `CODENAME-PHOENIX` — confidential term detected |
| `docs/index.md` | 17 | `Z204` | `internal-staging.example.corp` — confidential term detected |

Exit code: **2** (security_breach — same severity as Z201 credential scanner).

## Why `.zenzic.local.toml`?

`forbidden_patterns` contains confidential business terms that must **never**
be committed to a public repository.  Zenzic enforces this by design: the
canonical location for `forbidden_patterns` is the local overlay, which you
add to `.gitignore`.  The shared `zenzic.toml` stays clean and auditable.
