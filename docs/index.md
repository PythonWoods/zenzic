---
template: home.html
hide:
  - navigation
  - toc
  - path
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD041 MD036 -->

<div class="zz-hero" markdown>

![Zenzic](assets/brand/svg/zenzic-wordmark.svg#only-light){ .zz-hero__logo }
![Zenzic](assets/brand/svg/zenzic-wordmark-dark.svg#only-dark){ .zz-hero__logo }

High-performance documentation linter for any Markdown-based project.
Catch broken links, orphan pages, and leaked credentials — before your users do.
{: .zz-hero__tagline }

[Get started](guide/index.md){ .md-button .md-button--primary }
[View on GitHub](https://github.com/PythonWoods/zenzic){ .md-button }
{: .zz-hero__actions }

</div>

<div class="zz-hero__screenshot-wrap" markdown>

![Zenzic Sentinel — full audit output with quality score](assets/screenshots/screenshot.svg){ .zz-hero__screenshot }

</div>

---

<div class="grid cards zz-features" markdown>

- :lucide-link-2-off: &nbsp; __Broken links__

    ---

    Detects dead internal links, missing anchors, and unreachable external URLs — at source level, before the build runs.

    ```bash
    zenzic check links
    ```

- :lucide-file: &nbsp; __Orphan pages__

    ---

    Finds `.md` files that exist on disk but are absent from the site navigation. Invisible to readers.

    ```bash
    zenzic check orphans
    ```

- :lucide-code: &nbsp; __Invalid snippets__

    ---

    Compiles every fenced Python block with `compile()`. Catches syntax errors before readers copy-paste broken code.

    ```bash
    zenzic check snippets
    ```

- :lucide-pencil: &nbsp; __Placeholder stubs__

    ---

    Flags pages below a word-count threshold or containing patterns like `TODO`, `WIP`, `coming soon`.

    ```bash
    zenzic check placeholders
    ```

- :lucide-image: &nbsp; __Unused assets__

    ---

    Reports images and files that exist in `docs/` but are never referenced by any page.

    ```bash
    zenzic check assets
    ```

- :lucide-shield-check: &nbsp; __Zenzic Shield__

    ---

    Scans every reference URL for leaked credentials — API keys, tokens, AWS access keys. Exits with code `2` immediately.

    ```bash
    zenzic check references
    ```

</div>

---

<div class="zz-sentinel-section" markdown>

## Sentinel in Action

Every finding is pinned to file, line, and source. Structured output for human eyes and machine parsing alike.

<div class="grid cards" markdown>

- :lucide-terminal: &nbsp; __Gutter reporter__

    ---

    Each error shows the exact offending source line with gutter context. No scrolling through logs to find what broke.

    ```text
    docs/guide.md
      ✘ 16:    [FILE_NOT_FOUND]  'setup.md' not found in docs
        │
     16 │ Read the [setup guide](setup.md) before continuing.
        │
    ```

- :lucide-shield: &nbsp; __Zenzic Shield__

    ---

    Scans every line — including fenced `bash` and `yaml` blocks — for leaked credentials. Exit code `2` is reserved exclusively for security events.

    ```text
    docs/tutorial.md
      ✘ 42:    [CREDENTIAL_LEAK]  GitHub token detected
        │
     42 │ Authorization: Bearer ghp_example123token
        │
    ```

- :lucide-chart-bar: &nbsp; __Quality score__

    ---

    `zenzic score` emits a single deterministic __0–100 integer__. Save a baseline and gate pull requests on regression.

    ```bash
    zenzic score --save          # persist baseline
    zenzic diff --threshold 5   # exit 1 if score drops > 5
    ```

</div>

</div>

---

<div class="zz-score-section" markdown>

## Quality score

`zenzic score` aggregates all six checks into a single __0–100 integer__ weighted by severity. Deterministic — track it in CI, compare across branches, block regressions.

```bash
zenzic score --save
zenzic diff --threshold 5
```

</div>

---

<div class="zz-trust-section" markdown>

Apache-2.0 &nbsp;·&nbsp; Python 3.11+ &nbsp;·&nbsp; zero runtime dependencies

</div>
