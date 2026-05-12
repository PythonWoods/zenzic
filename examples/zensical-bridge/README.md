# Zensical Bridge — Transparent Proxy Example

This example demonstrates Zenzic's **Transparent Proxy** mode.

## Setup

- `zenzic.toml` declares `engine = "zensical"`
- **No `zensical.toml`** is present — only `mkdocs.yml`

## What happens

When `zenzic check all` runs, the **ZensicalLegacyProxy** activates and the
**Zenzic Banner** is printed:

```text
ZENZIC: Zensical engine active via mkdocs.yml compatibility bridge.
```

All link validation, anchor checks, and credential scanner runs via the MkDocs adapter
internally. Results are identical to running with `engine = "mkdocs"`.

## Purpose

This is not a silent fallback. The Zenzic Banner makes the bridge explicit,
preserving operator awareness of engine identity at all times. It provides a
frictionless migration path: add `zensical.toml` when ready, and Zenzic
automatically switches to native mode on the next run.

## Run

```bash
cd examples/zensical-bridge
zenzic check all
```

Expected output includes the Zenzic Banner followed by a clean check result.
