<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Cross-Engine Validation Matrix

Two opposing fixture sets that prove Zenzic's detection is engine-agnostic.
The same integrity violations fire identically whether the docs are built
with Standalone, MkDocs, or Zensical.

```text
examples/matrix/
├── adversarial-validation/   ← violation fixtures — expected exit 2 (SECURITY BREACH)
└── integrity-baseline/       ← clean docs         — expected exit 0
```

## Stress Test: Massive Violation Matrix

```bash
(cd examples/matrix/adversarial-validation/standalone && uv run zenzic check all)
(cd examples/matrix/adversarial-validation/mkdocs     && uv run zenzic check all)
(cd examples/matrix/adversarial-validation/zensical   && uv run zenzic check all)
```

All three produce identical findings:

| Finding | Rule | Location |
|---|---|---|
| Secret detected (aws-access-key) | Z201 | `docs/how-to/configure.md` |
| Absolute path link | Z105 | `docs/tutorial/getting-started.md` |
| Absolute path link | Z105 | `docs/how-to/configure.md` |
| Absolute path link | Z105 | `docs/reference/api.md` |
| Short content | Z502 | `docs/tutorial/getting-started.md` |
| Short content | Z502 | `docs/how-to/configure.md` |
| Short content | Z502 | `docs/reference/api.md` |
| Short content / Ghost file | Z502/Z501 | `docs/explanation/architecture.md` |
| Missing directory index | Z401 | `docs/tutorial/`, `docs/how-to/`, `docs/reference/`, `docs/explanation/` |

Exit code: 2 (SECURITY BREACH)

## The Defense — Clean Baseline

```bash
(cd examples/matrix/integrity-baseline/standalone && uv run zenzic check all)
(cd examples/matrix/integrity-baseline/mkdocs     && uv run zenzic check all)
(cd examples/matrix/integrity-baseline/zensical   && uv run zenzic check all)
```

All three return exit code 0. Every finding from the adversarial-validation set has been resolved:
relative links, sufficient prose, directory indexes, and no credentials.

Exit code: 0 (Analysis complete ✨)

## What this proves

> Zenzic's Core is a pure algorithm — it has no knowledge of which engine produced
> the docs it is inspecting.

The parity guarantee: identical content produces identical findings regardless of
which adapter is active. See `examples/matrix/adversarial-validation/README.md` for the full
attack vector inventory and `examples/matrix/integrity-baseline/README.md` for the fix log.
