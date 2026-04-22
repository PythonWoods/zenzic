# Standalone Markdown — MISSING_DIRECTORY_INDEX Demo

This example demonstrates `MISSING_DIRECTORY_INDEX` detection on a bare Markdown
project with no build engine.

## Structure

```text
docs/
  index.md          — root landing page
  guides/
    index.md        — properly indexed: no finding
    setup.md
  deep-folder/      — NO index.md → MISSING_DIRECTORY_INDEX
    advanced.md
    internals.md
```

## What fires

```bash
zenzic check all --show-info
```

```text
💡 [MISSING_DIRECTORY_INDEX]  Directory contains Markdown files but has
no index page — the directory URL may return a 404.
  docs/deep-folder
```

This is an **info-level** finding: exit code 0, quality score unaffected.
Add an `index.md` to `docs/deep-folder/` to resolve it.

## Run

```bash
cd examples/standalone-markdown
zenzic check all --show-info
```

Expected: `MISSING_DIRECTORY_INDEX` info finding for `docs/deep-folder/`, all checks pass.
