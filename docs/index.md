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

    Detects dead internal links, missing anchors, and unreachable external URLs — at source level, before the build runs.

    ```bash
    zenzic check links
    ```

    [:octicons-arrow-right-24: Details](checks.md#links)

- :lucide-file: &nbsp; __Orphan pages__

    Finds `.md` files that exist on disk but are absent from the site navigation. Invisible to readers.

    ```bash
    zenzic check orphans
    ```

    [:octicons-arrow-right-24: Details](checks.md#orphans)

- :lucide-code: &nbsp; __Invalid snippets__

    Compiles every fenced Python block with `compile()`. Catches syntax errors before readers copy-paste broken code.

    ```bash
    zenzic check snippets
    ```

    [:octicons-arrow-right-24: Details](checks.md#snippets)

- :lucide-pencil: &nbsp; __Placeholder stubs__

    Flags pages below a word-count threshold or containing patterns like `TODO`, `WIP`, `coming soon`.

    ```bash
    zenzic check placeholders
    ```

    [:octicons-arrow-right-24: Details](checks.md#placeholders)

- :lucide-image: &nbsp; __Unused assets__

    Reports images and files that exist in `docs/` but are never referenced by any page.

    ```bash
    zenzic check assets
    ```

    [:octicons-arrow-right-24: Details](checks.md#assets)

- :lucide-shield-check: &nbsp; __Zenzic Shield__

    Scans every reference URL for leaked credentials — API keys, tokens, AWS access keys. Exits with code `2` immediately.

    ```bash
    zenzic check references
    ```

    [:octicons-arrow-right-24: Details](checks.md#references)

</div>

---

<div class="zz-sentinel-section">
<h2 id="sentinel-in-action">Sentinel in Action</h2>
<p>Every finding is pinned to file, line, and source. Structured output for human eyes and machine parsing alike.</p>
<div class="grid cards">
<ul>
<li>
<p><span class="twemoji"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19h8"/><path d="m4 17 6-6-6-6"/></svg></span> &nbsp; <strong>Gutter reporter</strong></p>
<hr>
<p>Each error shows the exact offending source line with gutter context. No scrolling through logs to find what broke.</p>
<div class="zz-sentinel-demo" aria-hidden="true">
<div class="zz-sentinel-demo__rule">docs/guide.md</div>
<div class="zz-sentinel-demo__finding">
<span class="zz-sentinel-demo__icon zz-sentinel-demo__icon--error">✘</span>
<span class="zz-sentinel-demo__badge">[FILE_NOT_FOUND]</span>
<span class="zz-sentinel-demo__message">'intro.md' not reachable from nav</span>
</div>
<div class="zz-sentinel-demo__snippet zz-sentinel-demo__snippet--dim"><span class="zz-sentinel-demo__line-no">15</span><span class="zz-sentinel-demo__gutter">│</span><span>before continuing.</span></div>
<div class="zz-sentinel-demo__snippet"><span class="zz-sentinel-demo__line-no">16</span><span class="zz-sentinel-demo__gutter zz-sentinel-demo__gutter--active">❱</span><span>See the getting started page for details.</span></div>
<div class="zz-sentinel-demo__snippet zz-sentinel-demo__snippet--dim"><span class="zz-sentinel-demo__line-no">17</span><span class="zz-sentinel-demo__gutter">│</span><span>Then configure your environment.</span></div>
</div>
</li>
<li>
<p><span class="twemoji"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/></svg></span> &nbsp; <strong>Zenzic Shield</strong></p>
<hr>
<p>Scans every line — including fenced <code>bash</code> and <code>yaml</code> blocks — for leaked credentials. Exit code <code>2</code> is reserved exclusively for security events.</p>
<div class="zz-sentinel-demo zz-sentinel-demo--breach-panel" aria-hidden="true">
<div class="zz-sentinel-demo__breach-header">SECURITY BREACH DETECTED</div>
<div class="zz-sentinel-demo__breach-row">
<span class="zz-sentinel-demo__icon zz-sentinel-demo__icon--error">✘</span>
<span class="zz-sentinel-demo__breach-key">Finding:</span>
<span class="zz-sentinel-demo__message">GitHub token detected</span>
</div>
<div class="zz-sentinel-demo__breach-row">
<span class="zz-sentinel-demo__icon zz-sentinel-demo__icon--error">✘</span>
<span class="zz-sentinel-demo__breach-key">Location:</span>
<span class="zz-sentinel-demo__message">docs/tutorial.md:42</span>
</div>
<div class="zz-sentinel-demo__breach-row">
<span class="zz-sentinel-demo__icon zz-sentinel-demo__icon--error">✘</span>
<span class="zz-sentinel-demo__breach-key">Credential:</span>
<span class="zz-sentinel-demo__breach-secret">ghp_************3456</span>
</div>
<div class="zz-sentinel-demo__breach-action">
<span class="zz-sentinel-demo__breach-key">Action:</span>
<span>Rotate this credential immediately and purge it from the repository history.</span>
</div>
</div>
</li>
<li>
<p><span class="twemoji"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2h-4a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V8"/><path d="M16.706 2.706A2.4 2.4 0 0 0 15 2v5a1 1 0 0 0 1 1h5a2.4 2.4 0 0 0-.706-1.706z"/><path d="M5 7a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h8a2 2 0 0 0 1.732-1"/></svg></span> &nbsp; <strong>Grouped by file</strong></p>
<hr>
<p>Findings are grouped under a file header instead of streamed as flat logs. You see where the problem lives before reading the finding details.</p>
<div class="zz-sentinel-demo" aria-hidden="true">
<div class="zz-sentinel-demo__rule">docs/guide.md</div>
<div class="zz-sentinel-demo__finding">
<span class="zz-sentinel-demo__icon zz-sentinel-demo__icon--error">✘</span>
<span class="zz-sentinel-demo__badge">[FILE_NOT_FOUND]</span>
<span class="zz-sentinel-demo__message">'intro.md' not reachable from nav</span>
</div>
<div class="zz-sentinel-demo__finding">
<span class="zz-sentinel-demo__icon zz-sentinel-demo__icon--warning">⚠</span>
<span class="zz-sentinel-demo__badge">[ZZ-NODRAFT]</span>
<span class="zz-sentinel-demo__message">Remove DRAFT markers before publishing.</span>
</div>
</div>
</li>
<li>
<p><span class="twemoji"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h.01"/><path d="M3 12h.01"/><path d="M3 19h.01"/><path d="M8 5h13"/><path d="M8 12h13"/><path d="M8 19h13"/></svg></span> &nbsp; <strong>Severity summary</strong></p>
<hr>
<p>Every run ends with a compact summary: counts by severity, files with findings, and a final verdict. You know immediately whether the check failed hard or only emitted warnings.</p>
<div class="zz-sentinel-demo" aria-hidden="true">
<div class="zz-sentinel-demo__summary-row">
<span class="zz-sentinel-demo__count zz-sentinel-demo__count--error">✘ 2 errors</span>
<span class="zz-sentinel-demo__count zz-sentinel-demo__count--warning">⚠ 1 warning</span>
<span class="zz-sentinel-demo__count zz-sentinel-demo__count--muted">• 1 file with findings</span>
</div>
<div class="zz-sentinel-demo__verdict zz-sentinel-demo__verdict--failed">FAILED: One or more checks failed.</div>
</div>
</li>
</ul>
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
