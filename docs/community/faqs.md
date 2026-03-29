---
icon: lucide/circle-question-mark
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Frequently Asked Questions

This page collects answers to questions frequently asked by Zenzic users. Browse the sections
below or use the search bar to find what you need.

!!! info "Help us grow this page"

    Have a question that isn't answered here? [Open an issue](https://github.com/PythonWoods/zenzic/issues)
    and we will add it.

## General

**What is Zenzic?**

Zenzic is a high-performance documentation linter for any Markdown-based project. It operates
on raw source files — never the generated output — so it works with any build engine: MkDocs,
Zensical, or any other static site generator via the adapter system. It detects broken links,
orphan pages, placeholder stubs, unused assets, leaked credentials, and more — before the
build runs.

**Is Zenzic free?**

Yes. Zenzic is Open Source under the Apache-2.0 license. You can use, modify, and distribute it
freely, including in commercial contexts.

**Which Python versions are supported?**

Zenzic requires Python 3.11 or higher.

---

## Installation and usage

**How do I install Zenzic?**

The easiest way is to use `uvx` to run it directly without installing:

```bash
uvx zenzic check all
```

Or add it to your project with `uv add --dev zenzic` (recommended) or `pip install zenzic`.

**Do I need a `zenzic.toml` file?**

No. Zenzic works with zero configuration — the defaults cover most standard projects out of the
box. `zenzic.toml` is only needed to customise behaviour, such as excluding specific directories,
assets, or external URLs.

**Can I use Zenzic with a non-MkDocs project?**

Yes. Zenzic works on any folder of Markdown files without requiring a build engine at all
(Vanilla mode). Native adapters for MkDocs and Zensical add nav-awareness and i18n support.
Third-party adapters can extend this to any other engine. See the [Engines guide](../guides/engines.md)
for details.

---

## Checks and results

**What is the difference between `zenzic check all` and `zenzic score`?**

`zenzic check all` runs all checks and returns a binary pass/fail result.
`zenzic score` computes a weighted quality score from 0 to 100 with per-category breakdown,
useful for continuous monitoring and badges.

**What is an "orphan page"?**

An orphan page is a Markdown file present in `docs/` but absent from the site navigation
declared in your build engine's configuration file. Orphan pages are unreachable by users
navigating the site structure. Zenzic reports them so you stay in control.

**The external link check is slow. Can I disable it?**

External link validation only runs when `--strict` is passed — omitting the flag disables all
network requests entirely. To permanently suppress specific URLs without removing strict mode,
add their prefixes to `excluded_external_urls` in `zenzic.toml`:

```toml
excluded_external_urls = [
    "https://internal.company.com",
    "https://github.com/MyOrg/private-repo",
]
```

**Does Zenzic check links in images too?**

Yes. The link check analyses all Markdown references: text links, images, reference-style links,
and same-page anchors (if `validate_same_page_anchors: true` is set).

---

## CI/CD

**How do I integrate Zenzic in GitHub Actions?**

```yaml
- name: Lint documentation
  run: uvx zenzic check all --strict
```

For the full setup with dynamic badges and regression detection, see the [CI/CD guide](../ci-cd.md).

**What does the `--strict` flag do?**

The `--strict` flag has two effects depending on the command:

- `zenzic check links --strict` / `zenzic check all --strict`: also validates external HTTP/HTTPS
  links via network requests (disabled by default for speed).
- `zenzic check references --strict`: treats Dead Definitions (reference links defined but never
  used) as hard errors instead of warnings.

Recommended in CI pipelines to catch all classes of issues.

**What is the Zenzic Shield (exit code 2)?**

Exit code `2` means the reference check detected a pattern that looks like a credential
(API key, token, password) in a URL or text. Rotate the credential immediately if you receive
this exit code.

**Why does Zenzic report `DANGLING_REFERENCE` when I defined the link at the bottom of the file?**

Your reference definition is likely being silently deleted by another tool in your pipeline.
`markdownlint --fix` (a common pre-commit hook) removes bare `[id]: url` reference definitions
when they appear in certain positions — after HTML blocks, `<figure>` tags, or before the first
heading — without reporting which rule triggered the removal. The line simply disappears.

**Solution:** Use inline links (`[text](url)`) instead of reference-style links
(`[text][id]` + `[id]: url` at the bottom). Inline links are immune to this class of linter
interference and are the recommended format for documentation in repositories with aggressive
linting pipelines.
