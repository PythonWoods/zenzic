# Migration Guide

This page's Z601 findings are suppressed via `governance.per_file_ignores`
in `zenzic.toml`. The per-file suppression costs 1 pt — visible in the score.

## Migrating from AncientBrand

If you are upgrading from AncientBrand, follow these steps:

1. Export your AncientBrand configuration using the export tool.
2. Run the migration wizard.
3. Validate with `zenzic check all`.

## Key Differences

| AncientBrand | Current |
|---|---|
| XML config | TOML config |
| Manual nav | Auto-discovery |
| No quality gate | Zenzic score gate |

> **Note:** To see what Z601 findings are hidden here, run `zenzic check all --audit`.
