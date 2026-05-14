<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Setup Guide

This guide covers installing and configuring the project in Standalone Mode.

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
engine   = "standalone"
docs_dir = "docs"
```

That is the entire required configuration. Run `zenzic check all` — Zenzic will
validate links, snippets, content quality, and assets across every `.md` file under
`docs/`.

## Adding custom rules

Extend enforcement without writing Python:

```toml
[[custom_rules]]
id       = "ZZ-NOHTML"
pattern  = "<(?!--)[a-zA-Z]"
message  = "Avoid raw HTML in Markdown — use native Markdown syntax instead."
severity = "warning"
```

## Next steps

- [API reference](api.md) — programmatic usage
- [Home](../index.md)
