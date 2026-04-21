# Advanced Topics

This page lives in `docs/deep-folder/` — a directory with **no `index.md`**.

Zenzic reports `MISSING_DIRECTORY_INDEX` for this directory when you run:

```bash
zenzic check all --show-info
```

This is an **info-level** finding: it does not affect the exit code or the
quality score. It highlights directories that may produce 404s when served
without an explicit nav configuration.

See [Internals](internals.md) for implementation details.
