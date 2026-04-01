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
| Links — **UNREACHABLE_LINK** (nav orphan) | `orphan-nav.md` exists but is absent from `nav:` in `mkdocs.yml` |
| Links — **UNREACHABLE_LINK** (private dir) | `_drafts/unreleased.md` is in a `_`-prefixed directory (Zensical rule) |
| Orphans | `api.md` exists on disk but is absent from `nav` |
| Snippets | `tutorial.md` contains a Python block with a `SyntaxError` |
| Placeholders | `api.md` has only 18 words and a task marker |
| Assets | `assets/unused.png` is on disk but never referenced |
| Custom rules | `[[custom_rules]]` in `zenzic.toml`: `ZZ-NOFIXME` pattern |

## Visual Snippets

Every `check links` finding in Zenzic rc5 includes a **Visual Snippet** — the exact
source line from your Markdown file, displayed below the error header with a `│` indicator.
Run the command and watch the terminal:

```bash
zenzic check links
```

You will see output like this (colours rendered in your terminal):

```text
BROKEN LINKS (7):
  [UNREACHABLE_LINK] index.md:22 — 'orphan-nav.md' resolves to '/orphan-nav/'
  which exists on disk but is not listed in the site navigation (UNREACHABLE_LINK)
  — add it to nav in mkdocs.yml or remove the link
    │ - [Nav orphan — exists on disk, missing from nav](orphan-nav.md)
  [UNREACHABLE_LINK] index.md:23 — '_drafts/unreleased.md' resolves to
  '/_drafts/unreleased/' which exists on disk but is not listed in the site
  navigation (UNREACHABLE_LINK) — add it to nav in mkdocs.yml or remove the link
    │ - [Private draft — inside `_drafts/`](_drafts/unreleased.md)
  [FILE_NOT_FOUND] index.md:16 — 'non-existent.md' not found in docs
    │ - [broken link to a page that does not exist](non-existent.md)
  ...
```

The `│` line shows the **exact Markdown source** — the link text, the target, and the
surrounding context — so you can fix the problem without hunting through the file.

## Run it

```bash
cd examples/broken-docs

# See link failures with Visual Snippets
zenzic check links

# Full report across all checks
zenzic check all

# Suppress non-zero exit (useful in CI soft-gate mode)
zenzic check all --exit-zero
```

Expected exit code: **1** (check failures; no Shield events).

## Engine

Uses `engine = "mkdocs"` (via `[build_context]` in `zenzic.toml`). The `mkdocs.yml`
intentionally omits `api.md` and `orphan-nav.md` from the nav to trigger the orphan and
UNREACHABLE_LINK checks. The `zensical.toml` mirrors the current v0.0.31+ schema and
provides an alternative native-engine config where `_drafts/` triggers the
private-directory UNREACHABLE_LINK rule.

## Ground truth

The UNREACHABLE_LINK findings are verifiable against the real MkDocs build output.
Run `nox -s audit_sandboxes` from the project root to execute the automated ground-truth
verification: it builds the MkDocs sandbox with the real MkDocs engine and confirms that
nav-orphan pages have no navigation links in the generated HTML.
