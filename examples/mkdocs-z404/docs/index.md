# MkDocs Z404 Fixture

This example demonstrates `Z404 CONFIG_ASSET_MISSING` detection for MkDocs projects.

The `mkdocs.yml` in this directory declares `theme.favicon` and `theme.logo`
pointing to files that do not exist on disk.

Zenzic emits **Z404 warnings** for each missing asset.
