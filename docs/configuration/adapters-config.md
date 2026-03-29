---
icon: lucide/plug
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Adapters & Engine Configuration

Zenzic uses an **adapter** to obtain engine-specific knowledge — nav structure, i18n directories,
and locale patterns — without importing or executing any build framework. Adapters are discovered
at runtime via Python entry-points; no Zenzic update is required to add third-party support.

---

## `[build_context]`

**Type:** table — **Default:** `engine = "mkdocs"`, `default_locale = "en"`, `locales = []`,
`fallback_to_default = true`

Engine and i18n context for locale-aware path resolution. This section is required only for
projects using **Folder Mode i18n** (`docs_structure: folder`) — where non-default locale pages
live under a top-level directory (e.g. `docs/it/`).

When `[build_context]` is absent (or `locales` is empty), Zenzic reads locale configuration
directly from `mkdocs.yml` — including `docs_structure`, `fallback_to_default`, and the
`languages` list. Zero-configuration projects are unaffected.

```toml
[build_context]
engine         = "mkdocs"   # "mkdocs" or "zensical"
default_locale = "en"       # ISO 639-1 code of the default locale
locales        = ["it"]     # non-default locale directory names (e.g. docs/it/, docs/fr/)
# fallback_to_default = true
```

> **TOML ordering:** `[build_context]` must be the **last** section in `zenzic.toml`. TOML table
> headers apply to all subsequent keys; placing `[build_context]` before top-level fields silently
> moves them into the sub-table.

### `engine`

**Default:** `"mkdocs"`

Selects the adapter used for nav extraction and i18n path resolution. Valid values for a stock
Zenzic installation are `"mkdocs"` and `"zensical"`. Third-party adapters registered under the
`zenzic.adapters` entry-point group add their own values.

### `default_locale`

**Default:** `"en"`

ISO 639-1 code identifying the default locale directory. Used for i18n fallback resolution.

### `locales`

**Default:** `[]`

Non-default locale directory names. Zenzic uses this list to answer two questions at lint time:

1. **Asset fallback** — a link from `docs/it/index.md` to `assets/logo.svg` resolves literally to
   `docs/it/assets/logo.svg` (which does not exist). Knowing `"it"` is a locale dir, Zenzic
   strips the prefix and checks `docs/assets/logo.svg` instead.
2. **Orphan suppression** — files under `docs/it/` are never listed in the nav (the i18n plugin
   injects them). Knowing which directories are locale trees prevents every translated file from
   being reported as an orphan.

### `fallback_to_default`

**Default:** `true`

Mirrors the `fallback_to_default` flag of the `mkdocs-i18n` plugin. When `true`, a link from a
translated page to a page that exists only in the default locale is suppressed — the build engine
will serve the default-locale version at runtime. Set to `false` to require every locale to have
its own copy of every page.

---

## Adapter auto-detection

Zenzic resolves the correct adapter automatically from `build_context.engine`:

| `build_context.engine` | Config file present | Adapter selected |
| :--- | :--- | :--- |
| `"mkdocs"` (default) | `mkdocs.yml` found | `MkDocsAdapter` — reads nav and i18n from `mkdocs.yml` |
| `"mkdocs"` | `mkdocs.yml` absent, no locales | `VanillaAdapter` — no nav awareness |
| `"zensical"` | `zensical.toml` found | `ZensicalAdapter` — reads nav from `zensical.toml` |
| `"zensical"` | `zensical.toml` absent | **Error** — `zensical.toml` is required |
| any unknown string | — | `VanillaAdapter` — no registered adapter for this engine |

### Vanilla mode

When `VanillaAdapter` is selected, Zenzic has no knowledge of the project's nav structure. In
this mode:

- **Orphan check** is skipped — without a nav declaration, every Markdown file would appear
  to be an orphan, making the check meaningless.
- All other checks (links, snippets, placeholders, assets, references) run normally.

Vanilla mode is the correct behaviour for plain Markdown repositories, wikis, and projects that
declare navigation dynamically at build time.

---

## `--engine` flag (one-off override)

The `--engine` flag on `zenzic check orphans` and `zenzic check all` overrides
`build_context.engine` for a single run without touching `zenzic.toml`:

```bash
zenzic check orphans --engine zensical
zenzic check all --engine mkdocs
```

If you pass an engine name that has no registered adapter, Zenzic lists the available adapters
and exits with code 1:

```text
ERROR: Unknown engine adapter 'hugo'.
Installed adapters: mkdocs, vanilla, zensical
Install a third-party adapter or choose from the list above.
```

---

## Third-party adapters

Third-party adapters (e.g. `zenzic-hugo-adapter`) are discovered automatically once installed as
Python packages — no Zenzic update required. Adapters register themselves under the
`zenzic.adapters` entry-point group in their `pyproject.toml`:

```toml
[project.entry-points."zenzic.adapters"]
hugo = "zenzic_hugo.adapter:HugoAdapter"
```

See [Writing an Adapter](../developers/writing-an-adapter.md) for the full protocol.
