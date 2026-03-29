<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# broken-docs — Intentional Failures Fixture

This example intentionally triggers every Zenzic check. It exists to demonstrate
what failures look like and to serve as a regression fixture for the check engine.

## What it demonstrates

| Check | Trigger |
| --- | --- |
| Links — missing file | `non-existent.md` does not exist |
| Links — dead anchor | `#non-existent-section` not in any page |
| Links — path traversal | `../../../../etc/passwd` escapes `docs/` |
| Links — absolute path | `/assets/logo.png` is not a relative path |
| Links — broken i18n | `missing.it.md` does not exist on disk |
| Orphans | `api.md` exists on disk but is absent from `nav` |
| Snippets | `tutorial.md` contains a Python block with a `SyntaxError` |
| Placeholders | `api.md` has only 18 words and a task marker |
| Assets | `assets/unused.png` is on disk but never referenced |
| Custom rules | `[[custom_rules]]` in `zenzic.toml`: `ZZ-NOFIXME` pattern |

## Run it

```bash
cd examples/broken-docs

# See all failures
zenzic check all

# Suppress non-zero exit (useful in CI soft-gate mode)
zenzic check all --exit-zero
```

Expected exit code: **1** (check failures; no Shield events).

## Engine

Uses `engine = "mkdocs"`. The `mkdocs.yml` intentionally omits `api.md` from
the nav to trigger the orphan check. The `zensical.toml` provides an alternative
native-engine config demonstrating the same orphan trigger.
