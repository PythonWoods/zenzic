<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD051 -- intentional dead anchors (test fixture) -->

# Welcome to Broken Docs

This site intentionally triggers all Zenzic checks — including path traversal and dead anchors.
Run `zenzic check all --strict` from this directory to see the full report.

![Project logo](assets/logo.png)

## What is broken here

| Check | Trigger |
| --- | --- |
| Links — missing file | [broken link to a page that does not exist](non-existent.md) |
| Links — dead anchor | [jump to a section that does not exist](#non-existent-section) |
| Links — path traversal | [escape from docs/](../../../../etc/passwd) |
| Links — **absolute path** | [absolute link to logo](/assets/logo.png) |
| Links — **broken i18n** | [Italian page that does not exist](missing.it.md) |
| Orphans | `api.md` exists on disk but is absent from `nav` |
| Snippets | `tutorial.md` contains a Python block with a `SyntaxError` |
| Placeholders | `api.md` has only 18 words and a bare task marker — see the file |
| Assets | `assets/unused.png` is on disk but never referenced |

The path traversal link above (`../../../../etc/passwd`) demonstrates the **Zenzic Shield**:
it is classified as `PathTraversal` — not a generic `FileNotFound` — and blocked before any
filesystem access occurs.

The absolute link (`/assets/logo.png`) demonstrates the **Portability Enforcement Layer**:
links starting with `/` are rejected as environment-dependent. They break when the site is
hosted in a subdirectory. Zenzic enforces relative paths for indestructible portability.

The broken i18n link (`missing.it.md`) demonstrates cross-locale link validation: Zenzic
checks that the target translation file actually exists on disk, even when i18n fallback is
active.

![Used image](assets/used.png)

See the [Tutorial](tutorial.md) to continue.
