# Zensical Basic Example

A minimal project showing Zenzic integration with the
[Zensical](https://zensical.org) build engine (v0.0.31+).

## What it demonstrates

| Feature | Where |
| :--- | :--- |
| `[project].nav` syntax (v0.0.31+) | `zensical.toml` |
| `engine = "zensical"` in `zenzic.toml` | `zenzic.toml` |
| Nested nav sections | `zensical.toml` nav |
| Orphan detection via `ORPHAN_BUT_EXISTING` | any file absent from nav |
| Clean relative links | `docs/**/*.md` |

## Run

```bash
cd examples/zensical-basic
zenzic check all
```

Expected result: `SUCCESS` with a score ≥ 90.
