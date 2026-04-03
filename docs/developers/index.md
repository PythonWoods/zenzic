---
icon: lucide/code
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Developer Guide

Welcome to the Zenzic engineering community. We build tools that bridge the gap
between human documentation and executable truth. Our codebase follows rigorous
standards for performance, type safety (`mypy --strict`), and accessibility.

This section covers everything you need to extend, adapt, or contribute to Zenzic.

---

## In this section

- [Writing Plugin Rules](plugins.md) — implement `BaseRule` subclasses, register
  them via `entry_points`, and satisfy the pickle / purity contract.
- [Writing an Adapter](writing-an-adapter.md) — implement the `BaseAdapter` protocol
  to teach Zenzic about a new documentation engine.
- [Example Projects](examples.md) — four self-contained runnable fixtures that
  demonstrate correct and incorrect Zenzic configurations.

---

## Interactive Workflow with Just

Zenzic uses [`just`](https://github.com/casey/just) as its interactive command runner.
`just` is the fast day-to-day layer; `nox` is the reproducible CI layer underneath.

| Command | Description |
|:--------|:------------|
| `just sync` | Install / update all dependency groups (`uv sync --all-groups`) |
| `just check` | **Self-lint — run Zenzic on its own documentation (strict)** |
| `just test` | Run the test suite (delegates to `nox -s tests`) |
| `just preflight` | Full CI-equivalent pipeline: lint, typecheck, tests, reuse, security |
| `just build` | Build the documentation site (`mkdocs build --strict`) |
| `just serve` | Start the live-reload documentation server |
| `just deploy` | `preflight` + production build — local release check |
| `just clean` | Remove generated artefacts (`site/`, `dist/`, caches, score file) |

The Sentinel's self-linting duty — `just check` — is the first command to run after
any documentation change. If Zenzic validates external projects, it must first pass
its own checks.

---

## Contributing

Full contribution guidelines, code conventions, Core Laws, and the pre-PR checklist
are in [`CONTRIBUTING.md`](https://github.com/PythonWoods/zenzic/blob/main/CONTRIBUTING.md)
on GitHub.

When you open a pull request, GitHub automatically loads the
[PR checklist](https://github.com/PythonWoods/zenzic/blob/main/.github/PULL_REQUEST_TEMPLATE.md)
— verify all items before requesting a review.
