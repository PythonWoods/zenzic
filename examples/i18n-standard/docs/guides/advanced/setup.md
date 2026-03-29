<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Advanced Setup

This page sits three levels deep inside the documentation tree:
`docs/guides/advanced/setup.md`. It demonstrates that relative links to shared
assets resolve correctly from any nesting depth.

## Relative link depth test

From this page (`docs/guides/advanced/`), the assets folder is two levels up:

- [Download brand-kit.zip](../../assets/brand-kit.zip)
- [Download manual.pdf](../../assets/manual.pdf)

These paths are resolved by Zenzic relative to the page location. No absolute
paths (`/assets/...`) are ever used — those would break portability.

## Cross-page navigation

- [Back to Guides](../index.md)
- [Performance tuning](tuning.md)
- [API Reference](../../reference/api.md)
- [Home](../../index.md)

## Configuration snippet

```yaml
# zenzic.toml — place at the repo root
docs_dir = "docs"
fail_under = 100
excluded_build_artifacts = ["docs/assets/manual.pdf", "docs/assets/brand-kit.zip"]
```

The `excluded_build_artifacts` field tells Zenzic that `manual.pdf` and
`brand-kit.zip` are generated at build time. Links to them are validated
structurally without requiring the files to exist on disk.
