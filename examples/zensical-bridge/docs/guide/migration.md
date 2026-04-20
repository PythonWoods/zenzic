# Migration Guide

This section covers the migration path from MkDocs to native Zensical.

## Step 1 — Introduce `zensical.toml`

Create a `zensical.toml` at the project root:

```toml
[project]
site_name = "My Docs"
docs_dir  = "docs"
nav = [
    "index.md",
    {"Guide" = ["guide/index.md", {"Migration" = "guide/migration.md"}]},
]
```

Once `zensical.toml` is present, the Transparent Proxy is deactivated and
Zenzic uses the native Zensical engine directly. The Sentinel Banner will no
longer appear.

## Step 2 — Remove `mkdocs.yml`

After verifying all links pass with Zensical native mode, the `mkdocs.yml`
can be archived or removed.

Return to [Home](../index.md).
