# mkdocs-basic — MkDocs 1.6.1 Reference Fixture

A clean, minimal MkDocs 1.x project used as a stable baseline for Zenzic.
This fixture intentionally models the official MkDocs nav patterns:

- plain page entries
- titled page entries
- nested sections
- external nav links
- configuration tags like !ENV and !relative

## Run

```bash
cd examples/mkdocs-basic
zenzic check all
```

Expected exit code: 0.

## Why this fixture exists

- Validates that MkDocsAdapter remains compatible with MkDocs 1.6.x config shapes.
- Demonstrates that Zenzic parses mkdocs.yml statically without calling MkDocs.
- Provides a migration-safe baseline before moving projects to Zensical.
