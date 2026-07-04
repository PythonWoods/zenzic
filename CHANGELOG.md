<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

## [0.20.0] — 2026-07-04

### ✨ The Extensibility Update

This minor release opens the Zenzic AST to user-defined Python rules via the **Custom Rules API v2**
and expands the auto-fix engine to cover two additional codes.

### Added

- **Custom Rules API v2 (AST Walker):** Users can now write custom analysis rules in Python by
  subclassing `BaseASTRule` from `zenzic.rules`. Rules are auto-discovered from `.zenzic/rules/*.py`
  at scan startup — no registration or entry-point wiring required.
- **Deterministic Visitation Budget Sandbox (Z901 / Z902):** Every custom rule executes inside a
  single-threaded visitation counter guard (`max_visits`, default 10 000). Exceeding the budget
  raises `ZenzicRuleTimeout`, which is caught and emitted as **Z902 (RULE_TIMEOUT)** without halting
  the scan. Any other unhandled exception is caught and emitted as **Z901 (RULE_ENGINE_ERROR)**.
- **`fixable` metadata field:** `CodeDefinition` now carries a `fixable: bool` attribute surfaced in
  `zenzic explain` output and as **Fixable: Yes/No** badges in `finding-codes.md`.
- **Auto-Fix: Z121 → Z122 (MISSING_OR_EMPTY_HREF):** `zenzic fix` now rewrites `<a>` tags with a
  missing or empty `href` attribute to `href="#"`, converting the Error to a Warning (`Z122`).
- **Auto-Fix: Z603 (DEAD_SUPPRESSION):** `zenzic fix` cleanly removes dead
  `<!-- zenzic:ignore: Zxxx -->` comments and `data-zenzic-ignore` HTML attributes without
  corrupting surrounding text.

### Changed

- `src/zenzic/rules.py` (compatibility stub) replaced by the `zenzic.rules` package
  (`src/zenzic/rules/__init__.py` + `src/zenzic/rules/base.py`). The public SDK surface is
  unchanged; all previously exported symbols remain available.
- `zenzic fix` now runs a per-file scan pass before applying mutations in order to collect dead
  suppression line numbers for Z603 auto-fix targeting.

### Hardened

- **Suppression Tracker:** `SuppressionTracker._parse()` now also registers `data-zenzic-ignore`
  HTML attributes (via `PolyglotExtractor`) as suppressions, enabling Z603 detection for dead
  HTML-level suppressions with distinct diagnostic messaging.
- **Validator:** Removed the silent early-exit bypass for `data-zenzic-ignore` nodes in the
  Polyglot Extractor pipeline; suppression is now delegated to the `SuppressionTracker` for
  consistent tracking.

## Historical Releases

- v0.19.x archive: [changelogs/v0.19.x.md](./changelogs/v0.19.x.md)
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
