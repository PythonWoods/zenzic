<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Setup Guide

This guide covers installing and configuring the project in Vanilla mode.

## Prerequisites

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

```bash
# Zero-install: run directly from PyPI
uvx zenzic check all

# Or install as a project dev dependency
uv add --dev zenzic
```

## Minimal configuration

Create a `zenzic.toml` at the repository root:

```toml
engine   = "vanilla"
docs_dir = "docs"
```

That is the entire required configuration. Run `zenzic check all` — Zenzic will
validate links, snippets, placeholders, and assets across every `.md` file under
`docs/`.

## Adding custom rules

Extend enforcement without writing Python:

```toml
[[custom_rules]]
id       = "ZZ-NOFIXME"
pattern  = "(?i)\\bFIXME\\b"
message  = "FIXME markers must be resolved before publishing."
severity = "error"
```

## Next steps

- [API reference](api.md) — programmatic usage
- [Home](../index.md)
