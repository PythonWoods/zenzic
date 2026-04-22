# Zensical Z404 Fixture

This example demonstrates `Z404 CONFIG_ASSET_MISSING` detection for Zensical projects.

The `zensical.toml` in this directory declares `[project].favicon` and `[project].logo`
pointing to files that do not exist on disk.

Zenzic emits **Z404 warnings** for each missing asset.
