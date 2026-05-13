# Quick Start

This document is the EN default locale baseline for the Z602 I18N_PARITY example.
It contains four sections. The IT translation at `docs/it/index.md` is missing
the "Advanced Configuration" section, which triggers Z602.

## Installation

Install Zenzic via pip or uv:

```bash
pip install zenzic
# or
uv add zenzic
```

## Basic Usage

Run the full check suite from the project root:

```bash
zenzic check all
```

## Configuration

Create `zenzic.toml` in the project root. Minimum required fields:

```toml
docs_dir = "docs"

[build_context]
engine = "standalone"
```

## Advanced Configuration

Enable i18n parity checking by adding a `[build_context]` section
with `locales` and an `[i18n]` block:

```toml
[build_context]
default_locale = "en"
locales        = ["it", "fr"]

[i18n]
enabled = true
```

Zenzic will compare section headings between the default locale and each
non-default locale file. Missing sections in any locale emit Z602.
