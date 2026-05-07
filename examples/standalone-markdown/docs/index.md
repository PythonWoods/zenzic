# Standalone Markdown Project

A bare Markdown documentation tree — no build engine, no framework, no
configuration file of any documentation system.

Zenzic runs in Standalone Mode: links, snippets, Shield, and directory index
checks all operate without any engine-specific configuration. This makes
it suitable for Hugo, Sphinx, Astro, or any hand-written project.

> **Note:** Orphan detection (Z402) is disabled in Standalone Mode because
> there is no navigation contract to compare against.

## Code Examples

This section includes a code snippet demonstrating the project CLI.

<!-- markdownlint-disable-next-line MD040 -- untagged block is intentional: Z505 UNTAGGED_CODE_BLOCK test fixture -->
```
# Untagged block — no language specifier → Z505 UNTAGGED_CODE_BLOCK
# In a real project, tag this block: ```bash or ```python
zenzic check all --strict
```

> **Note (Quartz Z505):** The block above triggers Z505 because it has no language
> specifier. The fix: add `bash` or `python` after the opening fence. In this fixture
> it is intentionally untagged to demonstrate the finding in ruff-style flat output.

## Contents

- [Guides](guides/index.md)
- [Deep Folder](deep-folder/advanced.md) — no index.md in this section
