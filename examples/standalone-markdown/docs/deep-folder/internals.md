# Internals

Technical notes on the vanilla engine mode.

Zenzic's `VanillaAdapter` performs all checks without any build engine:

- Link validation (relative `.md` paths resolved against the filesystem)
- Anchor resolution (heading IDs derived from heading text)
- Shield credential scan (9 pattern families, always active)
- `MISSING_DIRECTORY_INDEX` check (directories without `index.md`)

Return to [Advanced Topics](advanced.md) or [Home](../index.md).
