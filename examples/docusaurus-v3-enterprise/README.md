# Docusaurus v3 Enterprise — Reference Fixture

This example is the flagship Zenzic fixture. It demonstrates the full stack
of Docusaurus v3 analysis capabilities in a single coherent project.

## What this example shows

| Feature | File | Demonstrates |
|---|---|---|
| Current docs | `docs/intro.mdx` | Standard Docusaurus routing |
| @site/ alias | `docs/guide/deploy.mdx` | `@site/docs/` prefix resolution |
| Versioned docs | `versioned_docs/version-1.0.0/intro.md` | Cross-version alias link |
| Ghost Routing | `i18n/it/…/intro.mdx` | Bilingual route validation |

## Key check — versioned @site/ link

In `versioned_docs/version-1.0.0/intro.md`:

```markdown
Read the [current Introduction](@site/docs/intro.mdx) for the latest content.
```

Zenzic resolves `@site/docs/intro.mdx` → `docs/intro.mdx` → `REACHABLE`.
No Node.js process is ever invoked.

## Run

```bash
cd examples/docusaurus-v3-enterprise
zenzic check all
```

Expected: all checks pass, exit code 0.
