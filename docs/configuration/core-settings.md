---
icon: lucide/sliders-horizontal
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Core Settings {#core-settings}

All top-level fields in `zenzic.toml` that control paths, thresholds, and scoring.

---

## `docs_dir`

**Type:** string (path) — **Default:** `"docs"`

Path to the documentation source directory, relative to the repository root.

```toml
docs_dir = "documentation"
```

---

## `excluded_dirs`

**Type:** list of strings — **Default:** `["includes", "assets", "stylesheets", "overrides", "hooks"]`

Directory names (not full paths) inside `docs_dir` that are excluded from all checks. Any
directory whose **name** matches an entry in this list is skipped, regardless of its depth in
the tree. This means `excluded_dirs = ["assets"]` excludes both `docs/assets/` and
`docs/guide/assets/`.

The default list covers the standard MkDocs and Material for MkDocs special directories, which
contain theme overrides, CSS, and snippet includes rather than documentation content.

```toml
excluded_dirs = ["includes", "assets", "partials", "_templates"]
```

---

## `excluded_assets`

**Type:** list of strings — **Default:** `[]`

Asset paths (relative to `docs_dir`) excluded from the unused-assets check. This field exists
for files that are referenced by `mkdocs.yml` or theme templates rather than by any Markdown
page — for example, favicons, logos, and social preview images.

Leading slashes are stripped, so `"assets/favicon.svg"` and `"/assets/favicon.svg"` are
equivalent.

```toml
excluded_assets = [
    "assets/favicon.svg",
    "assets/icon-512.png",
    "assets/logo.png",
    "assets/social-preview.png",
]
```

---

## `excluded_asset_dirs`

**Type:** list of strings — **Default:** `["overrides"]`

Directories inside `docs_dir` whose non-Markdown files are excluded from the unused-assets
check. Intended for theme override directories where files are consumed by the build tool rather
than referenced from Markdown pages.

```toml
excluded_asset_dirs = ["overrides", "_theme"]
```

---

## `excluded_file_patterns`

**Type:** list of strings — **Default:** `[]`

Filename glob patterns excluded from the orphan check. This is an escape hatch for non-standard
setups. **For projects using `mkdocs-i18n` with `docs_structure: suffix`**, no configuration is
needed — Zenzic auto-detects all non-default locales from `mkdocs.yml` and excludes the
corresponding `*.{locale}.md` files automatically.

```toml
# Manual exclusion for a custom naming scheme
excluded_file_patterns = ["*.locale.md", "*_draft.md"]
```

Patterns are matched against the **filename only** (not the full path). Applies only to the
orphan check — placeholder and asset checks scan locale-suffixed files normally.

---

## `excluded_build_artifacts`

**Type:** list of strings (glob patterns) — **Default:** `[]`

Glob patterns (relative to `docs_dir`) for assets generated at build time. Links to paths
matching these patterns are not reported as broken even when the file does not exist on disk at
lint time.

```toml
excluded_build_artifacts = [
    "pdf/*.pdf",
    "assets/bundle.zip",
]
```

Use this when your documentation links to files produced only during the build step and therefore
absent when Zenzic runs on the raw source.

---

## `excluded_external_urls`

**Type:** list of strings — **Default:** `[]`

URL prefixes excluded from the external broken-link check. A URL is skipped when it starts with
any entry in this list. Matching is prefix-based — a single entry covers an entire domain or
subtree.

Common scenarios:

- **Pre-release libraries** — links to your own GitHub repo or PyPI page before they are public
- **Private repositories** — internal GitHub repos not reachable from CI runners
- **Staged environments** — staging or preview URLs that only exist during a deploy window

```toml
excluded_external_urls = [
    "https://github.com/MyOrg/my-library",
    "https://pypi.org/project/my-library/",
]
```

!!! warning "Use sparingly"
    Excluding a URL prefix silences all broken-link errors under that prefix. Prefer fixing the
    underlying issue and removing the exclusion once the URL is live.

---

## `snippet_min_lines`

**Type:** integer — **Default:** `1`

Minimum number of lines a fenced Python code block must contain to be syntax-checked. The default
of `1` checks every block, including single-line expressions.

Raise this value if your documentation includes many short illustrative snippets — import
statements, one-line examples, type annotations — that are intentionally incomplete and would
fail `compile()`. A value of `3` is a common choice for projects with both single-line examples
and multi-line executable code.

```toml
snippet_min_lines = 3
```

---

## `placeholder_max_words`

**Type:** integer — **Default:** `50`

Pages with fewer words than this threshold are flagged as `short-content`. Word count is computed
by splitting the raw Markdown source on whitespace — it includes headings, link text, and code
block content, but not HTML tags.

Set to `0` to disable the word-count signal entirely. The pattern-match signal
(`placeholder_patterns`) runs independently and is not affected.

```toml
placeholder_max_words = 100
```

---

## `placeholder_patterns`

**Type:** list of strings — **Default:** `["coming soon", "work in progress", "wip", "todo", "to do", "stub", "placeholder", "fixme", "tbd", "to be written", "to be completed", "to be added", "under construction", "not yet written", "draft", "da completare", "in costruzione", "in lavorazione", "da scrivere", "da aggiungere", "bozza", "prossimamente"]`

Case-insensitive strings that, when found anywhere on a line, flag the page as
`placeholder-text`. Matching is performed line-by-line on the raw Markdown source. Each pattern
is treated as a literal string, not a regular expression.

```toml
placeholder_patterns = ["coming soon", "wip", "fixme", "tbd", "draft"]
```

To disable pattern matching entirely while keeping the word-count check:

```toml
placeholder_patterns = []
```

---

## `validate_same_page_anchors`

**Type:** boolean — **Default:** `false`

When `true`, same-page anchor links (`[text](#section)`) are validated against the headings
extracted from the source file.

Zenzic resolves anchor slugs in the following order:

1. **Explicit MkDocs Material anchor** — if the heading contains `{ #custom-id }`, that ID is
   used directly.
2. **Standard slug** — HTML tags are stripped, text is lowercased and non-word characters
   replaced with hyphens, matching Python-Markdown's `toc` extension.

Disabled by default because anchor IDs can also be produced at build time by HTML attributes or
custom plugins invisible during source-level scanning. Enable for projects where all anchors are
driven by ATX headings.

```toml
validate_same_page_anchors = true
```

---

## `fail_under`

**Type:** integer — **Default:** `0`

Minimum quality score (0–100). If `zenzic score` produces a score below this value, the command
exits with code 1. Setting `fail_under = 0` (the default) disables the threshold.

The `--fail-under` CLI flag overrides this value for a single run.

```toml
fail_under = 80   # exit 1 if score < 80
```

To run in observational mode regardless of what `zenzic.toml` contains:

```bash
zenzic score --fail-under 0
```

---

## `strict`

**Type:** boolean — **Default:** `false`

When `true`, every invocation of `zenzic check all`, `zenzic score`, and `zenzic diff` behaves
as if `--strict` were passed: external URLs are validated via network requests and warnings are
treated as errors.

Use this to make strict mode the permanent default for a project, without adding `--strict` to
every CI command:

```toml
strict = true
```

The `--strict` CLI flag overrides this value for a single run (setting it for that run
regardless of what `zenzic.toml` contains).

---

## `exit_zero`

**Type:** boolean — **Default:** `false`

When `true`, `zenzic check all` always exits with code `0` even when issues are found. All
findings are still printed and included in the quality score — only the exit code is suppressed.

Use this during an active documentation improvement sprint when you want full visibility without
blocking the pipeline:

```toml
exit_zero = true
```

The `--exit-zero` CLI flag overrides this value for a single run.

!!! warning "Use sparingly"
    Setting `exit_zero = true` in `zenzic.toml` disables the quality gate globally. Prefer
    using `--exit-zero` as a temporary CLI flag during cleanup sprints, and removing it once
    the baseline is clean.
