---
icon: lucide/regex
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Custom Rules DSL

`[[custom_rules]]` lets you declare project-specific lint rules directly in `zenzic.toml`. Each
rule applies a regular expression line-by-line to every `.md` file and produces a finding when
the pattern matches. No Python is required — the DSL is pure TOML.

---

## Syntax

```toml
[[custom_rules]]
id       = "ZZ-NOINTERNAL"
pattern  = "internal\\.corp\\.example\\.com"
message  = "Internal hostname must not appear in public documentation."
severity = "error"

[[custom_rules]]
id       = "ZZ-NODRAFT"
pattern  = "(?i)\\bDRAFT\\b"
message  = "Remove DRAFT marker before publishing."
severity = "warning"
```

Each `[[custom_rules]]` header appends one rule to the list. Use double brackets — that is the
TOML array-of-tables syntax.

---

## Fields

| Field | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `id` | string | ✓ | Stable unique identifier shown in findings (e.g. `"ZZ001"`, `"ZZ-NODRAFT"`) |
| `pattern` | string | ✓ | Regular expression applied to each content line |
| `message` | string | ✓ | Human-readable explanation shown in the finding |
| `severity` | `"error"` \| `"warning"` \| `"info"` | — | Default: `"error"` |

---

## Severity behaviour

| Severity | Blocks pipeline | With `--strict` |
| :--- | :---: | :---: |
| `"error"` | Yes (exit code 1) | Yes |
| `"warning"` | No | Yes |
| `"info"` | No | No |

Rules with `severity = "error"` cause `zenzic check all` to exit 1. `"warning"` findings are
surfaced in the report but do not affect the exit code unless `--strict` is passed.

---

## Adapter-independence

**Custom rules are adapter-independent.** A rule searching for `DRAFT` fires identically whether
the project uses `MkDocsAdapter`, `ZensicalAdapter`, or `VanillaAdapter`. The rule engine
operates on raw Markdown text; it has no knowledge of the build engine. This means:

- Rules you write for a MkDocs project require no changes after [migrating to Zensical](../guides/migration.md).
- Rules are safe to write before deciding which build engine a project will use.

---

## Performance

**Patterns are compiled once** at config-load time, not per file. There is no performance penalty
for having many rules. Invalid regex patterns raise a `ConfigurationError` at startup with the
offending pattern and the regex error message.

---

## TOML placement

Place all `[[custom_rules]]` blocks **before** the `[build_context]` section. `[build_context]`
must be the last section in `zenzic.toml` — TOML table headers apply to all subsequent keys, so
any top-level field written after `[build_context]` would silently become a `build_context` sub-key.

```toml
# Correct ordering
docs_dir = "docs"

[[custom_rules]]
id       = "ZZ-NODRAFT"
pattern  = "(?i)\\bDRAFT\\b"
message  = "Remove DRAFT marker before publishing."
severity = "warning"

[build_context]          # ← always last
engine = "mkdocs"
```

---

## Pattern tips

| Goal | Pattern |
| :--- | :--- |
| Case-insensitive word boundary | `(?i)\\bDRAFT\\b` |
| Literal dot (hostname) | `internal\\.corp\\.example\\.com` |
| Match anywhere on line | `TODO` (no anchors needed — matching is per-line) |
| Exclude false positives | Use word boundaries `\\b` to avoid matching `TODOS` when looking for `TODO` |

All patterns are applied with Python `re.search` — a match anywhere on the line triggers the
finding. Use `^` and `$` anchors only when you need to constrain to the start or end of the line.
