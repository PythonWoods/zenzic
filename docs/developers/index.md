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

## Contributing

Full contribution guidelines, code conventions, Core Laws, and the pre-PR checklist
are in [`CONTRIBUTING.md`](https://github.com/PythonWoods/zenzic/blob/main/CONTRIBUTING.md)
on GitHub.

When you open a pull request, GitHub automatically loads the
[PR checklist](https://github.com/PythonWoods/zenzic/blob/main/.github/PULL_REQUEST_TEMPLATE.md)
— verify all items before requesting a review.
