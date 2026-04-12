# Docusaurus v3 — Reference Fixture

A minimal Docusaurus v3 project used as the reference fixture for Zenzic's
`DocusaurusAdapter`. This example demonstrates:

| Feature | Where |
| :--- | :--- |
| `engine = "docusaurus"` in `zenzic.toml` | `zenzic.toml` |
| `baseUrl` extraction from config | `docusaurus.config.ts` |
| `.mdx` extension support | `docs/intro.mdx` |
| MDX component tolerance | `docs/intro.mdx` — `<Icon />` JSX |
| Cross-page relative links | `docs/intro.mdx` → `docs/guide/install.mdx` |
| i18n Ghost Route injection | `i18n/it/.../intro.mdx` |
| Mirror Law validation | IT translation mirrors EN structure |

## Run

```bash
cd examples/docusaurus-v3
zenzic check all
```

Expected exit code: 0.

## Why this fixture exists

- Validates that `DocusaurusAdapter` correctly maps `.mdx` → clean URLs.
- Demonstrates that Zenzic parses `docusaurus.config.ts` as plain text — no
  Node.js subprocess is ever spawned.
- Proves that MDX-specific syntax (JSX components, imports) does not crash
  the Markdown parser.
- Provides a migration reference for users moving from MkDocs to Docusaurus.
