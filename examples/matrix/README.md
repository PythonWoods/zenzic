<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# War Room — Cross-Engine Validation Matrix

The Siege & Shield pattern: two opposing fixtures that prove Zenzic's detection is
engine-agnostic. The same attack vectors fire identically whether the docs are built
with Standalone, MkDocs, or Zensical.

```text
examples/matrix/
├── red-team/   ← attack vectors — expected exit 2 (SECURITY BREACH)
└── blue-team/  ← clean docs    — expected exit 0 (Obsidian Seal ✨)
```

## The Siege — watch the red banner

```bash
(cd examples/matrix/red-team/standalone && uv run zenzic check all)
(cd examples/matrix/red-team/mkdocs     && uv run zenzic check all)
(cd examples/matrix/red-team/zensical   && uv run zenzic check all)
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

## The Shield — Obsidian Seal

```bash
(cd examples/matrix/blue-team/standalone && uv run zenzic check all)
(cd examples/matrix/blue-team/mkdocs     && uv run zenzic check all)
(cd examples/matrix/blue-team/zensical   && uv run zenzic check all)
```

All three return exit code 0. Every finding from the red-team has been resolved:
relative links, sufficient prose, directory indexes, and no credentials.

Exit code: 0 (Obsidian Seal ✨)

## What this proves

> Zenzic's Core is a pure algorithm — it has no knowledge of which engine produced
> the docs it is inspecting.

The parity guarantee: identical content produces identical findings regardless of
which adapter is active. See `examples/matrix/red-team/README.md` for the full
attack vector inventory and `examples/matrix/blue-team/README.md` for the fix log.
