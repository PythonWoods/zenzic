<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Red-Team Fixtures

Three identical doc sets — one per engine — each containing the same four attack
vectors. Run any of them to watch Zenzic fire exit code 2 (SECURITY BREACH).

```bash
(cd examples/matrix/red-team/standalone && uv run zenzic check all)
(cd examples/matrix/red-team/mkdocs     && uv run zenzic check all)
(cd examples/matrix/red-team/zensical   && uv run zenzic check all)
```

Expected exit: 2 (SECURITY BREACH)

## Attack Vector Inventory

| Attack Vector | Rule | File | Technique |
|---|---|---|---|
| Shadow Secret | Z201 | `docs/how-to/configure.md` | `aws_access_key_id: AKIAIOSFODNN7EXAMPLE` in YAML frontmatter |
| Absolute Trap | Z105 | `docs/tutorial/getting-started.md` | Link to `/how-to/configure` |
| Absolute Trap | Z105 | `docs/how-to/configure.md` | Link to `/reference/api` |
| Absolute Trap | Z105 | `docs/reference/api.md` | Link to `/how-to/configure` |
| Short Content Ghost | Z502 | `docs/tutorial/getting-started.md` | Body < 50 words |
| Short Content Ghost | Z502 | `docs/how-to/configure.md` | Body < 50 words |
| Short Content Ghost | Z502 | `docs/reference/api.md` | Body < 50 words |
| Short Content Ghost | Z502/Z501 | `docs/explanation/architecture.md` | 2 prose words + `draft: false` |
| Missing Index | Z401 | `docs/tutorial/` | No `index.md` |
| Missing Index | Z401 | `docs/how-to/` | No `index.md` |
| Missing Index | Z401 | `docs/reference/` | No `index.md` |
| Missing Index | Z401 | `docs/explanation/` | No `index.md` |

## Parity Note

Z401 is not standalone-only — it fires for all engines via `adapter.provides_index()`.
All four attack categories (Z201, Z105, Z502, Z401) are engine-agnostic by design.

See `../blue-team/README.md` for the complete fix log.
