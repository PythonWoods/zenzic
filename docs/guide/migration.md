---
icon: lucide/arrow-right-left
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Migrating from MkDocs to Zensical

Zenzic acts as a continuous integrity guard during your migration. Because it lints the
**source files** and reads configuration as plain data — never by importing or executing the
build framework — it works correctly against both engines simultaneously and can validate your
documentation before, during, and after the switch.

---

## What stays the same

Zensical is a compatible successor to MkDocs. It reads `mkdocs.yml` natively, so many projects can switch
the build binary without touching a single documentation file. From Zenzic's perspective:

- The `docs/` directory layout is unchanged.
- `mkdocs.yml` remains the primary navigation and plugin configuration file.
- i18n folder-mode and suffix-mode conventions are identical.
- `[build_context]` in `zenzic.toml` can stay as `engine = "mkdocs"` until you are ready
  to create `zensical.toml`.

---

## MkDocs Material best practices

### Language switcher optimisation

When using `mkdocs-material` with the `i18n` plugin and multiple locales, the language
switcher in the site header can be controlled by two different mechanisms.  Mixing them
causes routing conflicts that Zenzic — a source linter — cannot detect automatically,
but that silently break the user experience at build time.

**Recommended configuration:**

```yaml
# mkdocs.yml
plugins:
  - i18n:
      docs_structure: folder
      fallback_to_default: true
      reconfigure_material: true   # ← delegate switcher to the i18n plugin
      reconfigure_search: true
      languages:
        - locale: en
          default: true
          build: true
          link: /
        - locale: it
          build: true
          link: /it/
```

**Do not** add an `extra.alternate` block alongside `reconfigure_material: true`.
When both are present, the Material theme receives two competing switcher
definitions; depending on the plugin version the result is either a duplicated
switcher or no switcher at all:

```yaml
# ✗ — remove this block when reconfigure_material: true is set
extra:
  alternate:
    - name: English
      link: /
      lang: en
    - name: Italiano
      link: /it/
      lang: it
```

**Why Zenzic handles this correctly:**
When `reconfigure_material: true` is present in `mkdocs.yml`, Zenzic recognises
that the Material theme will auto-generate locale entry points (e.g. `/it/`) at
build time.  These pages are never listed in `nav:` — they are synthetic routes
produced by the plugin.  Zenzic marks them as **auto-generated REACHABLE** in the
Virtual Site Map so they are never reported as orphans.

---

## Phase 1 — Validate before switching

Run the full check suite against your MkDocs project and establish a baseline:

```bash
# Make sure the docs are clean before you touch anything
zenzic check all
zenzic score --save   # persist baseline to .zenzic-score.json
```

A clean baseline means any regression introduced during the migration is immediately visible
with `zenzic diff`.

---

## Phase 2 — Switch the build binary

Install Zensical alongside (or instead of) MkDocs:

```bash
uv add --dev zensical      # recommended
# or: pip install zensical
```

Run your documentation build to verify it produces identical output:

```bash
zensical build
```

Zenzic's checks are engine-neutral — run them after the build to confirm nothing broke:

```bash
zenzic check all
zenzic diff              # should report zero delta against the pre-migration baseline
```

---

## Phase 3 — Declare Zensical identity (optional)

If you want Zenzic to enforce the Zensical identity contract — requiring `zensical.toml` to
be present and using the `ZensicalAdapter` for nav extraction — update `zenzic.toml`:

```toml
# zenzic.toml
[build_context]
engine = "zensical"
default_locale = "en"
locales        = ["it"]   # if you have non-default locale dirs
```

And create a minimal `zensical.toml` at the repository root:

```toml
# zensical.toml
[site]
name = "My Documentation"

[nav]
nav = [
    {title = "Home",  file = "index.md"},
    {title = "Guide", file = "guide.md"},
]
```

!!! warning "Enforcement contract"

    Once `engine = "zensical"` is declared in `zenzic.toml`, `zensical.toml` **must** exist.
    Zenzic raises a `ConfigurationError` immediately if it is absent — there is no silent
    fallback to `mkdocs.yml`. This is intentional: engine identity must be provable.

---

## Phase 4 — Verify link integrity

The link check is your most important validation step. Run it against the completed migration:

```bash
# Internal links + i18n fallback resolution
zenzic check links

# Reference-style links + Shield (credential detection)
zenzic check references

# Full suite
zenzic check all
zenzic diff --threshold 0   # fail on any regression, no margin
```

If the score matches the pre-migration baseline, the migration is complete.

---

## Keeping custom rules during migration

`[[custom_rules]]` in `zenzic.toml` are **adapter-independent** — they fire identically
regardless of the engine. Any rules you had in place for your MkDocs project continue to work
without modification after switching to Zensical:

```toml
# These rules work with both engines
[[custom_rules]]
id       = "ZZ-NODRAFT"
pattern  = "(?i)\\bDRAFT\\b"
message  = "Remove DRAFT marker before publishing."
severity = "warning"

[build_context]
engine = "zensical"
```

---

## Quick reference

| Step | Command | Expected result |
| :--- | :--- | :--- |
| Baseline | `zenzic score --save` | Score saved to `.zenzic-score.json` |
| After build switch | `zenzic check all` | Same issues as before |
| Regression check | `zenzic diff` | Delta = 0 |
| Identity enforcement | `engine = "zensical"` in `zenzic.toml` | Requires `zensical.toml` |
| Final gate | `zenzic diff --threshold 0` | Exit 0 only if score did not drop |
