<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# API Reference

This page documents the programmatic interface exposed by the i18n Standard example.
It is intentionally simple — the goal is to demonstrate a valid reference page with
working cross-links, not to describe a real API.

## `check_links(docs_dir)`

Validates all internal links in the given docs directory.

**Parameters:**

- `docs_dir` (`str`) — path to the documentation root, relative to the repo root.

**Returns:** exit code `0` on success, `1` on link errors, `2` on security violations.

## `score()`

Returns the current documentation quality score (0–100).

## Related pages

- [Advanced setup](../guides/advanced/setup.md) — configuration reference
- [Performance tuning](../guides/advanced/tuning.md) — optimisation guide
- [Home](../index.md)
