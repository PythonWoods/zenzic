<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# i18n-standard — Gold Standard Bilingual Project

This example demonstrates a perfectly structured bilingual documentation project
that scores **100/100** under `zenzic check all --strict`.

## What it demonstrates

- **Suffix-mode i18n**: translations live as `page.it.md` siblings alongside
  `page.md` — never in a separate `docs/it/` subtree
- **Path symmetry**: a link `../../assets/brand-kit.zip` resolves identically
  from both `page.md` and `page.it.md`
- **Build artifact exclusion**: `manual.pdf` and `brand-kit.zip` are listed in
  `excluded_build_artifacts` — links to them are validated structurally without
  requiring the files to exist on disk
- **`fail_under = 100`**: enforces a perfect score; any regression fails the gate

## Run it

```bash
cd examples/i18n-standard
zenzic check all --strict
```

Expected exit code: **0** — `SUCCESS: All checks passed.`

## Structure

```text
docs/
  index.md / index.it.md          ← home page (EN + IT)
  guides/
    index.md / index.it.md        ← guides section
    advanced/
      setup.md / setup.it.md      ← deep nesting, ../../ relative links
      tuning.md / tuning.it.md
  reference/
    api.md / api.it.md            ← API reference
```

## Engine

Uses `engine = "mkdocs"` with the MkDocs `i18n` plugin in `docs_structure: suffix` mode.
`locales = ["it"]` and `default_locale = "en"` declared in `zenzic.toml`.
