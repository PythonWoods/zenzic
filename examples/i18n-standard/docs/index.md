<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# i18n Standard — The Gold Standard

Welcome to the **Zenzic Gold Standard** example. This site demonstrates a perfectly
structured bilingual documentation project that scores **100/100** under `zenzic check all --strict`.

## What makes this the standard

| Rule | How this site complies |
| --- | --- |
| **Suffix Mode** | Translations live as `page.it.md` siblings, never in a `docs/it/` subtree |
| **Zero absolute links** | Every internal link is relative (`../`, `./`) |
| **Path symmetry** | A link `../assets/brand-kit.zip` resolves identically from `.md` and `.it.md` |
| **Asset integrity** | All referenced assets exist on disk; no unreferenced files left dangling |
| **No placeholders** | Every page has real content, no TODO stubs |

## Explore the structure

- [Guides index](guides/index.md) — start here for the guided tour
- [Advanced setup](guides/advanced/setup.md) — deep nesting, relative links three levels up
- [API Reference](reference/api.md) — programmatic interface

## Download

The full brand kit is available as a ZIP archive:
[Download brand-kit.zip](assets/brand-kit.zip)

The user manual (generated at build time):
[Download manual.pdf](assets/manual.pdf)
