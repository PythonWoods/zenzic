---
icon: lucide/arrow-right-left
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Migrating to Zensical

!!! note "Zenzic vs Zensical"
    **Zenzic** is the documentation linter described in this documentation site — the tool
    you run with `zenzic check all`.

    **Zensical** is a separate build engine (a compatible successor to MkDocs 1.x). This page
    describes how to use Zenzic as a safety net while switching your *build engine* from MkDocs
    to Zensical.

    You do not need to use Zensical to use Zenzic. Zenzic works with MkDocs, Zensical,
    Vanilla Markdown folders, and any engine that has an adapter.

---

## Your source files outlive your build engine

Build engines evolve. They change configuration formats, drop plugin systems, merge with
commercial platforms, or simply stop being maintained. When that happens, the assets at risk
are not your Markdown files — those are plain text and will always be readable. What is at
risk is your **investment in structure**: the navigation, the i18n conventions, the link
graph, the asset organisation you have built over years.

Zenzic's role in a migration is not to make the switch faster. It is to make the switch
**provably safe** — by guaranteeing that every structural invariant you care about is
measured before, during, and after the move, and that any regression is visible immediately
and attributed precisely.

This guarantee rests on a single architectural principle: **Zenzic lints the source, never
the build**. It reads `mkdocs.yml`, `zensical.toml`, and your Markdown files as plain data.
It never imports or executes a build framework. This means:

- Zenzic understands your documentation structure even if the build binary that used to
  interpret it no longer works.
- Running `zenzic check all` on a project in the middle of a migration produces the same
  analysis as on a fully operational project — because the source files have not changed.
- Switching `engine` in `zenzic.toml` (one line) is all it takes to validate whether your
  content is structurally compatible with a new engine, without touching a single Markdown
  file.

This is the Safe Harbor: **a fixed validation layer that remains valid before, during, and
after any build engine change**.

---

## The MkDocsAdapter: plain-data preservation

The `MkDocsAdapter` treats `mkdocs.yml` as a pure data structure — a set of nav paths,
plugin declarations, and locale settings. It extracts what it needs (nav tree, i18n
configuration, plugin flags like `reconfigure_material`) and hands the result to the Rule
Engine as typed Python objects. It never calls `mkdocs build`, never imports `mkdocs`, and
never depends on any plugin being installed or functional.

The practical consequence is that `MkDocsAdapter` is a **custodian of the classic pluggable
ecosystem standard**. As long as your `mkdocs.yml` describes a valid MkDocs 1.x-style
structure, Zenzic will understand and validate it — regardless of what any build binary
does or does not support. If you run `zenzic check all` with `engine = "mkdocs"`, you are
testing your content against the documented MkDocs 1.x structural contract, not against any
particular binary version.

This makes Zenzic's output a portable quality certificate: if Zenzic says your
documentation is structurally sound, that claim is true independently of which engine you
use to render it tomorrow.

---

## i18n: validating structure independently of rendering

The MkDocs `i18n` plugin (folder-mode and suffix-mode conventions) defines a well-specified
content structure: locale directories, fallback chains, per-locale nav shadowing. Zenzic
encodes this specification in `MkDocsAdapter` and the Virtual Site Map independently of any
rendering implementation.

This matters during engine transitions. When a build engine is still maturing its i18n
support, there is a window where the *structural rules* of your i18n setup are well-defined
but the *rendering capability* of the engine may not yet be complete. Zenzic operates
entirely in the structural domain:

- **Cross-locale link resolution** — a link from an Italian page to an English-only asset
  is resolved against the fallback chain defined in `mkdocs.yml`, not against the build
  output.
- **Ghost Route detection** — locale entry points generated at build time (e.g. `/it/`)
  are marked `REACHABLE` in the VSM so they are never reported as orphans, even if they
  have never been rendered.
- **Locale directory suppression** — files under `docs/it/`, `docs/fr/`, etc. are
  classified as locale shadows, not orphans.

You can therefore validate a complex i18n structure with Zenzic and be confident in its
internal consistency — the link graph is correct, the fallback chains are intact, the nav
is complete — before committing to any rendering engine.

---

## What stays the same when switching to Zensical

Zensical reads `mkdocs.yml` natively. Many projects can switch the build binary without
touching a single documentation file. From Zenzic's perspective:

- The `docs/` directory layout is unchanged.
- `mkdocs.yml` remains valid as the primary navigation and configuration source; Zensical
  reads it directly.
- i18n folder-mode and suffix-mode conventions are structurally identical.
- `[build_context]` in `zenzic.toml` can stay as `engine = "mkdocs"` until you are ready
  to create `zensical.toml`.

---

## MkDocs Material best practices

### Language switcher configuration

When using `mkdocs-material` with the `i18n` plugin and multiple locales, the language
switcher can be controlled by two different mechanisms. Mixing them causes routing conflicts
that Zenzic — a source linter — cannot detect automatically, but that silently break the
user experience at build time.

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
When both are present, the Material theme receives two competing switcher definitions;
depending on the plugin version the result is either a duplicated switcher or no switcher
at all:

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
When `reconfigure_material: true` is present in `mkdocs.yml`, Zenzic recognises that the
Material theme will auto-generate locale entry points (e.g. `/it/`) at build time. These
pages are never listed in `nav:` — they are synthetic routes produced by the plugin. Zenzic
marks them as **auto-generated REACHABLE** in the Virtual Site Map so they are never
reported as orphans.

---

## Migration playbook

### Phase 1 — Establish a baseline

Run the full check suite and lock in a quality baseline before changing anything:

```bash
# Confirm the documentation is structurally sound before touching the build layer
zenzic check all
zenzic score --save   # persist baseline to .zenzic-score.json
```

A saved baseline means that any regression introduced during the migration is immediately
measurable with `zenzic diff`. The baseline is a snapshot of your source state — it does
not depend on any build engine being functional.

### Phase 2 — Switch the build binary

Install Zensical alongside (or instead of) MkDocs:

```bash
uv add --dev zensical      # recommended
# or: pip install zensical
```

Run the documentation build to verify it produces correct output:

```bash
zensical build
```

Zenzic's checks are engine-neutral — run them after the build to confirm the source
structure is intact:

```bash
zenzic check all
zenzic diff              # should report zero delta against the pre-migration baseline
```

### Phase 3 — Declare Zensical identity (optional)

If you want Zenzic to enforce the Zensical structural contract — requiring `zensical.toml`
to be present and using `ZensicalAdapter` for nav extraction — update `zenzic.toml`:

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

### Phase 4 — Verify link integrity

The link check is your most important validation step. Run it against the completed
migration:

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

## Your migration options

Switching to Zensical is one of several paths available to a project on MkDocs. Zenzic
supports all of them with the same quality guarantee:

| Path | `engine` in `zenzic.toml` | What Zenzic validates |
| :--- | :--- | :--- |
| Stay on MkDocs 1.x | `"mkdocs"` | Full MkDocs 1.x structural contract |
| Switch to Zensical | `"zensical"` | Zensical nav + TOML identity contract |
| Migrate to another engine | `"mkdocs"` during transition, then adapter | Source integrity throughout |
| Evaluate without committing | `--engine mkdocs` or `--engine zensical` (CLI flag) | Dry-run compatibility check |

The `--engine` CLI flag lets you run a single check against a different engine adapter
without touching `zenzic.toml`:

```bash
# Test whether your current source is structurally compatible with Zensical
# without declaring the switch in zenzic.toml
zenzic check all --engine zensical
```

---

## Keeping custom rules during migration

`[[custom_rules]]` in `zenzic.toml` are **adapter-independent** — they fire identically
regardless of the engine. Any rules you had in place for your MkDocs project continue to
work without modification after switching to Zensical:

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
| Compatibility dry-run | `zenzic check all --engine zensical` | Structural issues with Zensical adapter |
| After build switch | `zenzic check all` | Same issues as before |
| Regression check | `zenzic diff` | Delta = 0 |
| Identity enforcement | `engine = "zensical"` in `zenzic.toml` | Requires `zensical.toml` |
| Final gate | `zenzic diff --threshold 0` | Exit 0 only if score did not drop |
