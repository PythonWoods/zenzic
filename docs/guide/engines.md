---
icon: lucide/blocks
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Engine Configuration Guide

Zenzic is **agnostic** — it works with MkDocs, Zensical, or a bare folder of Markdown files
without requiring any build framework to be installed. It is also **opinionated**: when you
declare an engine, you must prove it. This guide explains how to configure Zenzic for each
supported engine and what the rules are.

## Cross-ecosystem reach

Zenzic is a Python tool, but its reach is not limited to the Python documentation ecosystem.
Because Zenzic analyses **source Markdown files and configuration as plain data** — never
invoking a build engine, never importing framework code — it can validate documentation for
any static site generator (SSG), regardless of what language that generator is written in.

| Support level | Engine | SSG language | How |
| :--- | :--- | :--- | :--- |
| **Native** | MkDocs | Python | `MkDocsAdapter` — reads `mkdocs.yml`, resolves i18n, enforces nav |
| **Native** | Zensical | Python | `ZensicalAdapter` — reads `zensical.toml`, zero-YAML |
| **Agnostic** | Vanilla | any | `VanillaAdapter` — works on any Markdown folder; orphan check disabled |
| **Extensible** | Hugo *(example)* | Go | Third-party adapter via `zenzic.adapters` entry-point |
| **Extensible** | Docusaurus *(example)* | Node.js | Third-party adapter via `zenzic.adapters` entry-point |
| **Extensible** | Jekyll *(example)* | Ruby | Third-party adapter via `zenzic.adapters` entry-point |

The "Extensible" entries are examples of what the adapter system enables — not shipped
adapters. A team maintaining Hugo, Docusaurus, or Jekyll documentation can write a
third-party adapter package and install it alongside Zenzic without any change to Zenzic
itself:

```bash
# Example: third-party adapter for a hypothetical Hugo support package
uv pip install zenzic-hugo-adapter   # or: pip install zenzic-hugo-adapter
zenzic check all --engine hugo
```

This cross-language reach is a structural property, not a roadmap promise. The Adapter
protocol defines five methods; any Python package that implements them and registers under
the `zenzic.adapters` entry-point group is a valid Zenzic adapter — for any SSG.

---

## Choosing an engine

The `[build_context]` section in `zenzic.toml` tells Zenzic which engine your project uses:

```toml
# zenzic.toml
[build_context]
engine = "mkdocs"   # or "zensical"
```

If `[build_context]` is absent entirely, Zenzic auto-detects:

- `mkdocs.yml` present → `MkDocsAdapter`
- neither config present, no locales declared → `VanillaAdapter` (orphan check disabled)

---

## MkDocs

`MkDocsAdapter` is selected when `engine = "mkdocs"` (or any unrecognised engine string).
It reads `mkdocs.yml` using a permissive YAML loader that silently ignores unknown tags
(such as MkDocs `!ENV` interpolation), so environment-variable-heavy configs work without
any preprocessing.

### Static analysis limits

`MkDocsAdapter` parses `mkdocs.yml` as **static data**. It does not execute the MkDocs
build pipeline. This means:

- **`!ENV` tags** — silently treated as `null`. If your nav relies on environment variable
  interpolation at build time, the nav entries that depend on those values will be absent
  from Zenzic's view.
- **Plugin-generated nav** — plugins that mutate the nav at runtime (e.g. `mkdocs-awesome-pages`,
  `mkdocs-literate-nav`) produce a navigation tree that Zenzic never sees. Pages included
  only by these plugins will be reported as orphans.
- **Macros** — `mkdocs-macros-plugin` (Jinja2 templates in Markdown) is not evaluated.
  Links inside macro expressions are not validated.

For projects that rely heavily on dynamic nav generation, add the plugin-generated paths to
`excluded_dirs` in `zenzic.toml` to suppress false orphan reports until a native adapter
is available.

### Minimal configuration

```toml
# zenzic.toml
docs_dir = "docs"

[build_context]
engine         = "mkdocs"
default_locale = "en"
locales        = ["it", "fr"]   # non-default locale directory names (folder mode)
```

When `locales` is empty, Zenzic falls back to reading locale information directly from the
`mkdocs-static-i18n` plugin block in `mkdocs.yml` — zero configuration required for most
projects.

### i18n: Folder Mode

In Folder Mode (`docs_structure: folder`), each non-default locale lives in a top-level
directory under `docs/`:

```text
docs/
  index.md          ← default locale
  assets/
    logo.png        ← shared asset
  it/
    index.md        ← Italian translation
```

Zenzic reads the `languages` list from `mkdocs.yml` to identify locale directories. Files
whose first path component is a locale directory are excluded from the orphan check — they
inherit their nav membership from the default-locale original.

When `fallback_to_default: true` is set, asset links from `docs/it/index.md` that resolve
to `docs/it/assets/logo.png` (absent) are automatically re-checked against `docs/assets/logo.png`,
mirroring the build engine's actual fallback behaviour.

```yaml
# mkdocs.yml
plugins:
  - i18n:
      docs_structure: folder
      fallback_to_default: true
      languages:
        - locale: en
          default: true
          build: true
        - locale: it
          build: true
```

> **Rule:** If `fallback_to_default: true` is set, at least one language entry must have
> `default: true`. If none does, Zenzic raises `ConfigurationError` immediately — it cannot
> determine the fallback target locale.

### i18n: Suffix Mode

In Suffix Mode (`docs_structure: suffix`), translated files are siblings of the originals:

```text
docs/
  guide.md        ← default locale
  guide.it.md     ← Italian translation (same directory depth)
  assets/
    logo.png      ← same relative path from both files
```

Zenzic reads the non-default locale codes from `mkdocs.yml` and generates `*.{locale}.md`
exclusion patterns (e.g. `*.it.md`, `*.fr.md`). These files are excluded from the orphan check.

Only valid ISO 639-1 two-letter lowercase codes produce exclusion patterns. Version tags
(`v1`, `v2`), build tags (`beta`, `rc1`), three-letter codes, and BCP 47 region codes are
silently rejected — they do not produce false exclusions.

---

## Zensical

`ZensicalAdapter` is selected when `engine = "zensical"`. It reads `zensical.toml` natively
using Python's `tomllib` — **zero YAML**. No `mkdocs.yml` is read or required.

### Native Enforcement

```toml
# zenzic.toml
[build_context]
engine = "zensical"
```

If `zensical.toml` is **absent** when `engine = "zensical"` is declared, Zenzic raises
`ConfigurationError` immediately:

```text
ConfigurationError: engine 'zensical' declared in zenzic.toml but zensical.toml is missing
hint: create zensical.toml or set engine = 'mkdocs' for MkDocs projects
```

There is no fallback. There is no silent degradation. Engine identity must be provable from
the files on disk.

### zensical.toml nav format

Zenzic reads the `[nav]` section to determine which pages are declared:

```toml
# zensical.toml
[project]
site_name = "My Docs"

[nav]
nav = [
  {title = "Home",     file = "index.md"},
  {title = "Tutorial", file = "tutorial.md"},
  {title = "API",      file = "reference/api.md"},
]
```

Files listed under `file` (relative to `docs/`) are the nav set. Any `.md` file under `docs/`
that is not in this set and is not a locale mirror is reported as an orphan.

### Why Zensical eliminates i18n complexity

MkDocs i18n relies on a plugin (`mkdocs-static-i18n`) with its own YAML configuration,
`docs_structure` switches, `fallback_to_default` logic, and `languages` lists. Zensical
defines i18n semantics natively in `zensical.toml` without plugin indirection. The result:

- No YAML to parse for locale detection
- No `fallback_to_default` ambiguity
- No "which plugin block applies?" heuristics
- `ConfigurationError` is impossible for misconfigured i18n — the TOML schema is explicit

When Zensical's i18n configuration is available in `zensical.toml`, `ZensicalAdapter` will
read it directly. Until then, locale topology is sourced from `[build_context]` in `zenzic.toml`.

---

## Absolute Link Prohibition

**This rule applies to every engine, unconditionally.**

Links that begin with `/` are a hard error in all engine modes:

```markdown
<!-- Rejected — absolute path breaks portability -->
[Download](/assets/guide.pdf)

<!-- Correct — relative path survives any hosting prefix -->
[Download](../assets/guide.pdf)
```

A link to `/assets/guide.pdf` presupposes the site is served from the domain root. When
documentation is hosted at `https://example.com/docs/`, the browser resolves
`/assets/guide.pdf` to `https://example.com/assets/guide.pdf` — a 404. The fix is always
a relative path.

The check runs before any adapter logic — before nav parsing, before locale detection,
before path resolution. It cannot be suppressed by engine configuration.

External URLs (`https://...`, `http://...`) are not affected.

---

## Vanilla (no engine)

`VanillaAdapter` is returned when no engine config file is present and no locales are
declared. All adapter methods are no-ops:

- `is_locale_dir` → always `False`
- `resolve_asset` → always `None`
- `is_shadow_of_nav_page` → always `False`
- `get_nav_paths` → `frozenset()`
- `get_ignored_patterns` → `set()`

`find_orphans` returns `[]` immediately — without a nav, there is no reference set to
compare against. Snippet, placeholder, link, and asset checks still run normally.

This means Zenzic works out of the box on any other Markdown-based system without
producing false positives.
