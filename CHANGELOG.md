<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

## [0.19.0] - Unreleased

### Added

- Lossless AST parser and serializer (Composite Pattern) for Markdown blocks and inline elements.
- O(N) character-by-character state machine for inline tokenization, eliminating regex backtracking.
- Mutator engine for non-destructive in-memory AST modifications.
- Atomic File Writer implementing a strict write barrier with `tempfile` and `os.replace`.
- `zenzic fix` CLI command with `--dry-run` and `--apply` modes.
- `Z108 (EMPTY_LINK_TEXT)` auto-fix support, injecting the `TODO` keyword to transition structural errors into content debt.

### Fixed

- **Z501 (Placeholder Content):** Fixed context-blindness that caused placeholders inside fenced code blocks to trigger false positives. Restored default placeholder patterns in standard configurations.

## Historical Releases

- v0.18.x archive: [changelogs/v0.18.x.md](./changelogs/v0.18.x.md)
- v0.17.x archive: [changelogs/v0.17.x.md](./changelogs/v0.17.x.md)
- v0.16.x archive: [changelogs/v0.16.x.md](./changelogs/v0.16.x.md)
- v0.15.x archive: [changelogs/v0.15.x.md](./changelogs/v0.15.x.md)
- v0.14.x archive: [changelogs/v0.14.md](./changelogs/v0.14.md)
- v0.13.x archive: [changelogs/v0.13.md](./changelogs/v0.13.md)
- v0.12.x archive: [changelogs/v0.12.md](./changelogs/v0.12.md)
- v0.11.x archive: [changelogs/v0.11.md](./changelogs/v0.11.md)
- v0.10.x archive: [changelogs/v0.10.md](./changelogs/v0.10.md)
- v0.9.x archive: [changelogs/v0.9.md](./changelogs/v0.9.md)
- v0.8.x archive: [changelogs/v0.8.md](./changelogs/v0.8.md)
- v0.1.x–v0.7.x archive index: [changelogs/README.md](./changelogs/README.md)
