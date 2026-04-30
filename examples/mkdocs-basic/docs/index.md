# MkDocs Basic

This fixture represents a clean MkDocs 1.6-style documentation tree.

It is intentionally small but complete enough to validate navigation parsing,
route classification, and source-only linting behavior with deterministic
results. The goal is to provide a reliable benchmark that can be executed in
CI without network assumptions or build-engine subprocess dependencies.

## Quick Navigation {#quick-navigation}

Jump to any section in this guide:

- [Self (circular anchor)](#self) — **Z107 CIRCULAR_ANCHOR**: this link resolves to the
  `#self` anchor below, which in turn points back here. Zenzic detects the cycle.

## Self {#self}

> **Note (Quartz Z107):** This heading carries the `#self` anchor. The link
> `[Self](#self)` in the section above creates a circular anchor reference that
> Zenzic reports as Z107 CIRCULAR_ANCHOR. This demonstrates the structural
> integrity check in ruff-style flat output.

## Contents

- [Guide](guide/index.md)
- [API](api.md)

The navigation includes nested sections and one external link in mkdocs.yml.
Zenzic parses all of it from source configuration without running mkdocs build.
