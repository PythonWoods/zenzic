<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Performance Tuning

For large documentation trees, Zenzic's `InMemoryPathResolver` builds a complete
file map at startup. This page describes tuning options that keep lint times under
100 ms even for repositories with thousands of Markdown files.

## Key principles

1. **O(1) asset resolution** — Zenzic pre-builds a `frozenset` of known paths in
   Pass 1. Every link lookup in Pass 2 is a constant-time set membership check.
   No filesystem I/O occurs after construction.

2. **Suffix detection without plugins** — The resolver identifies `page.it.md` as
   a translation of `page.md` purely from the filename. No MkDocs plugin, no Hugo
   configuration, no Zensical config required.

3. **`excluded_build_artifacts`** — list generated files here so Zenzic never
   attempts to stat them on disk during lint. See [setup](setup.md) for an example.

## Navigation

- [Back to Advanced](setup.md)
- [Back to Guides](../index.md)
- [Home](../../index.md)
