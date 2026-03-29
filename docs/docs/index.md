---
icon: lucide/book-open-text
hide:
  - toc
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Documentation

Zenzic is a **CI-first documentation linter** for MkDocs and Zensical sites. It analyses raw Markdown source files — never the generated HTML — and catches documentation rot before it reaches your users.

!!! tip "Zero install — run it now"

    ```bash
    uvx zenzic check all
    ```

    `uvx` downloads and runs Zenzic in a throwaway environment. Nothing is installed on your system.

---

## The problem Zenzic solves

Documentation degrades silently. A developer renames a page and forgets to update the nav. A code example that worked six months ago now has a syntax error. An image gets deleted but the Markdown that references it stays. A page marked "coming soon" is never written.

None of these are hard errors that break your build. They are **soft failures** — they accumulate unnoticed until a user follows a dead link, copies broken code, or lands on a page that says "TODO". By then the damage is done.

Because Zenzic analyses raw Markdown source files — never the generated HTML — it is **generator-agnostic and version-independent**. It works identically with MkDocs, Zensical, or any future generator that reads `mkdocs.yml`. Upgrading your documentation engine does not break your quality gate.

Beyond reporting, Zenzic provides **autofix utilities** (like `zenzic clean assets`) to automatically clean your repository of unused files, making it a proactive participant in your project's health.

> Your generator builds the documentation. Zenzic enforces its quality.

---

## What's in this documentation

<div class="grid cards" markdown>

- :lucide-play: &nbsp; **User Guide**

    ---

    Installation, all CLI commands, quality scoring, CI/CD integration, and badges.

  - [Getting Started](../usage/index.md)
  - [Available Checks](../checks.md)
  - [Configuration](../configuration/index.md)
  - [Engines](../guides/engines.md)
  - [CI/CD Integration](../ci-cd.md)
  - [Badges](../usage/badges.md)
  - [FAQs](../community/faqs.md)

- :lucide-book: &nbsp; **Developer Guide**

    ---

    Architecture internals and auto-generated API documentation.

  - [Architecture](../architecture.md)
  - [API Reference](../reference/api.md)

- :lucide-users: &nbsp; **Community**

    ---

    Report issues, request features, improve the docs, or open a pull request.

  - [Get Involved](../community/index.md)
  - [How to Contribute](../community/contribute/index.md)

</div>

---

## Built with confidence

Zenzic ships with **98.4 % test coverage** measured by `pytest-cov`. Every check, every edge case in the state-machine parser, and every async code path in the link validator has a dedicated test. `ruff` enforces code quality across the entire codebase.

A linter that catches your documentation issues must itself be correct. These numbers are not a vanity metric — they are what let you trust Zenzic's output in automated pipelines.
