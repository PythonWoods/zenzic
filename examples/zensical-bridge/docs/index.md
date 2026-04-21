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

## Navigation

- [Guide](guide/index.md)
