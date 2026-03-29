---
icon: lucide/library
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# API Reference

Auto-generated reference documentation for all public modules in `zenzic`. This section is English-only, as the source docstrings are written in English.

---

## `zenzic.core.scanner`

Filesystem scanning utilities: repo root discovery, orphan page detection, asset tracking, and placeholder scanning.

::: zenzic.core.scanner
    options:
      members:
        - find_repo_root
        - find_config_file
        - find_orphans
        - find_placeholders
        - find_unused_assets
        - calculate_orphans
        - calculate_unused_assets
        - check_placeholder_content
        - check_asset_references

---

## `zenzic.core.scorer`

Documentation quality scoring engine: weighted 0–100 score computation, snapshot persistence, and snapshot loading.

::: zenzic.core.scorer
    options:
      members:
        - compute_score
        - save_snapshot
        - load_snapshot
        - ScoreReport
        - CategoryScore

---

## `zenzic.core.validator`

Validation logic: broken link detection via MkDocs and Python snippet syntax checking.

::: zenzic.core.validator
    options:
      members:
        - validate_links
        - validate_snippets
        - check_snippet_content
        - SnippetError

---

## `zenzic.models.config`

Configuration model.

::: zenzic.models.config
    options:
      members:
        - ZenzicConfig
