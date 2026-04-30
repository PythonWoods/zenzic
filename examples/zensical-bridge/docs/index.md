# Welcome to the Zensical Bridge Demo

This project declares `engine = "zensical"` in `zenzic.toml` but has **no
`zensical.toml`** — only a `mkdocs.yml`.

When you run `zenzic check all`, the **Transparent Proxy** activates
automatically and the **Sentinel Banner** is displayed:

```text
SENTINEL: Zensical engine active via mkdocs.yml compatibility bridge.
```

This provides a seamless migration path from MkDocs to Zensical without
blocking your CI pipeline. Engine identity is always transparent.

## Migration from Obsidian Build Tools

This project previously used the **Obsidian** documentation platform before migrating to
Zensical. All pages have been ported. The Obsidian export scripts are archived in
`scripts/obsidian-migration/`.

> **Note (Quartz Z905):** The word "Obsidian" in this section is flagged as a brand
> obsolescence violation. In a real project, replace references with the current brand name
> or use `<!-- zenzic:ignore Z905 -->` for intentional historical references.

## Navigation

- [Guide](guide/index.md)
