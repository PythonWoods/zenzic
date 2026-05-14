# mkdocs-basic — MkDocs 1.6.1 Reference Fixture

A clean, minimal MkDocs 1.x project used as a stable baseline for Zenzic.
This fixture intentionally models the official MkDocs nav patterns:

- plain page entries
- titled page entries
- nested sections
- external nav links
- configuration tags like `!ENV` and `!relative`

It demonstrates `MkDocsAdapter` against a real MkDocs 1.x project layout while
keeping the quality gate in the standalone Zenzic CLI.

## Prerequisites

Install Zenzic in your environment:

```bash
pip install zenzic
```

Install MkDocs separately only if you want to build the site fixture itself:

```bash
pip install "mkdocs>=1.6.1"
```

## Build Configuration

The `mkdocs.yml` in this example is consumed statically by `MkDocsAdapter`:

```yaml
plugins:
  - search
```

Zenzic reads the navigation and i18n shape from `mkdocs.yml` without importing
or executing MkDocs.

## Run

```bash
cd examples/mkdocs-basic
zenzic check all
```

Expected exit code: 0.

Or build MkDocs separately after the Zenzic audit passes:

```bash
mkdocs build --strict
```

## Configuration

This example uses `zenzic.toml`. Zenzic also supports the `[tool.zenzic]`
table inside `pyproject.toml` as a fallback when `zenzic.toml` is absent:

```toml
# pyproject.toml — alternative configuration
[tool.zenzic]
docs_dir = "docs"
fail_under = 90

[tool.zenzic.build_context]
engine = "mkdocs"
```

## Why this fixture exists

- Validates that `MkDocsAdapter` remains compatible with MkDocs 1.6.x config shapes.
- Demonstrates that Zenzic parses `mkdocs.yml` statically without calling MkDocs.
- Demonstrates a migration-safe MkDocs baseline validated by the standalone Zenzic CLI.
- Provides a migration-safe baseline before moving projects to Zensical.
