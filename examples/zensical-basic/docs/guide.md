# Guide

This page is listed in the nav under `{"Guide" = "guide.md"}`.

## Getting started

Install Zensical with `pip` or `uv`:

```bash
pip install zensical
# or
uv add --dev zensical
```

Then create your `zensical.toml`:

```toml
[project]
site_name = "My Docs"
docs_dir  = "docs"
```

Run the dev server:

```bash
zensical serve
```

## Navigation formats

Zensical accepts three nav entry forms inside `[project].nav`:

| Form | TOML syntax | Description |
| :--- | :--- | :--- |
| Plain string | `"page.md"` | Title inferred from first `#` heading |
| Titled page | `{"Title" = "page.md"}` | Explicit sidebar label |
| Section | `{"Section" = ["a.md", ...]}` | Collapsible group |

See the [home page](index.md) or the [API Reference](api/index.md).
