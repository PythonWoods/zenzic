---
# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
date: 2026-06-28
authors:
  - pythonwoods
categories:
  - Releases
  - Engineering
---

# Zenzic v0.17.0: Closing the HTML Blind Spot

With the release of Zenzic v0.17.0 (Magnetite Polyglot), we are marking a fundamental shift in our architecture. Zenzic is no longer just a "Markdown Linter". It has evolved into a full-fledged **Document Integrity Engine**.

For a long time, the documentation ecosystem has suffered from an architectural blind spot: raw HTML inside Markdown. When developers embed `<a>` tags or `<img>` elements directly into their Markdown to achieve specific layouts or functionality, traditional linters gloss over them. This creates a "Shadow Zone" where broken links and missing assets silently accumulate.

With v0.17.0, we have closed this gap entirely.

<!-- more -->

## The Uniform Resolver Pipeline (URP)

To tackle the HTML shadow zone without sacrificing the extreme performance that Zenzic is known for, we built the **Uniform Resolver Pipeline (URP)**.

The Polyglot Extractor natively parses `<a>` and `<img>` tags directly within the Markdown document. But instead of relying on slow, heavy DOM parsers, we achieved this by building a highly optimized O(N) DFA (Deterministic Finite Automaton) using the Google RE2 engine.

This means that whether a link is written in standard Markdown format `[text](url)` or as raw HTML `<a href="url">text</a>`, it now passes through the exact same validation pipeline. Both are subjected to the same strict checks for orphans, broken paths, and missing assets.

This unified approach brings five new diagnostic codes to ensure HTML hygiene:

- **Z120 UNKNOWN_HTML_ATTRIBUTE**: Warns when you use an attribute outside the Safe-Core list.
- **Z121 MISSING_OR_EMPTY_HREF**: Prevents you from shipping empty links.
- **Z122 JUMP_LINK_DETECTED**: Warns against opaque JavaScript jump anchors (`href="#"`).
- **Z123 NON_HTTP_SCHEME**: Flags `mailto:`, `tel:`, and similar non-resolvable URI schemes.
- **Z124 OPAQUE_HTML_CONTEXT**: Detects event handlers or shadow-routing attributes that can break SPA frameworks.

## Inviolable Security: Z205 Forbidden Scheme

Beyond structural integrity, raw HTML opens the door to potential cross-site scripting (XSS) vectors. A malicious actor could obfuscate a payload within an `href` attribute using `javascript:` or `data:` schemes.

To protect the integrity of your technical documentation, v0.17.0 introduces the **Z205 FORBIDDEN_SCHEME** security gate.

This is not a warning. It is a critical, **non-suppressible** violation. If Zenzic detects a forbidden scheme, it immediately halts the pipeline with an Exit 2 status. Inline suppressions like `data-zenzic-ignore` cannot bypass this. In environments using SARIF for CI/CD integrations, this triggers a `toolExecutionNotifications` alert, ensuring the build is definitively stopped before any compromised documentation can be deployed.

## The Path Forward

The v0.17.0 release cements our commitment to zero-debt documentation and absolute structural integrity. As we move towards v0.18.0, our focus will shift from the CI/CD pipeline directly into your editor with the upcoming Zenzic Language Server (ZLS).

Check out the [Changelog](https://github.com/PythonWoods/zenzic/blob/main/CHANGELOG.md) for the full list of updates and bug fixes in this release.

Happy writing, and stay secure!
