<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Blue-Team Fixtures

Three identical clean doc sets — one per engine — each with every red-team attack
vector resolved. Run any of them to earn the Obsidian Seal.

```bash
(cd examples/matrix/blue-team/standalone && uv run zenzic check all)
(cd examples/matrix/blue-team/mkdocs     && uv run zenzic check all)
(cd examples/matrix/blue-team/zensical   && uv run zenzic check all)
```

Expected exit: 0 (Obsidian Seal ✨)

## Fix Log

| Was (red-team) | Is (blue-team) | Rule resolved |
|---|---|---|
| `aws_access_key_id: AKIAIOSFODNN7EXAMPLE` in frontmatter | Credential removed | Z201 |
| `/how-to/configure` (absolute) | `../how-to/configure.md` (relative) | Z105 |
| `/reference/api` (absolute) | `../reference/api.md` (relative) | Z105 |
| Body < 50 words | Body ≥ 60 words | Z502 |
| `draft: false` in frontmatter | `draft:` field removed | Z501 |
| No `index.md` in `tutorial/` | `docs/tutorial/index.md` added | Z401 |
| No `index.md` in `how-to/` | `docs/how-to/index.md` added | Z401 |
| No `index.md` in `reference/` | `docs/reference/index.md` added | Z401 |
| No `index.md` in `explanation/` | `docs/explanation/index.md` added | Z401 |

## Lesson

The contrast is the lesson. The same engine that detected the secret just confirmed
that clean docs are genuinely clean. A green exit means nothing without the memory
of the breach — that is the War Room pattern.
