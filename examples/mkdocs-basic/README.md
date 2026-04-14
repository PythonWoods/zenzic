# mkdocs-basic — MkDocs 1.6.1 Reference Fixture

A clean, minimal MkDocs 1.x project used as a stable baseline for Zenzic.
This fixture intentionally models the official MkDocs nav patterns:

- plain page entries
- titled page entries
- nested sections
- external nav links
- configuration tags like `!ENV` and `!relative`

It also demonstrates the `zenzic.integrations.mkdocs` plugin — a native MkDocs
plugin that fires `zenzic check all` automatically during every `mkdocs build`.

## Prerequisites

Install Zenzic with the optional MkDocs integration extra:

```bash
pip install "zenzic[mkdocs]"
```

This installs both `zenzic` and `mkdocs>=1.6.1`. Without this extra, the
`zenzic` plugin entry in `mkdocs.yml` will cause `mkdocs build` to abort with
an "Unknown plugin" error.

## Plugin Configuration

The `mkdocs.yml` in this example registers the plugin with zero configuration:

```yaml
plugins:
  - search
  - zenzic          # drop-in — no config block required
```

The plugin is auto-discovered via the `mkdocs.plugins` entry point registered
in Zenzic's `pyproject.toml`. You do **not** need to install or configure
anything beyond `pip install "zenzic[mkdocs]"`.

## Run

```bash
cd examples/mkdocs-basic
zenzic check all
```

Expected exit code: 0.

Or trigger through MkDocs (runs Zenzic as part of the build pipeline):

```bash
mkdocs build --strict
```

## Configuration

This example uses `zenzic.toml`. Zenzic also supports the `[tool.zenzic]`
table inside `pyproject.toml` as a fallback when `zenzic.toml` is absent:

```toml
# pyproject.toml — alternative configuration
[tool.zenzic]
docs_dir = "docs"
fail_under = 90

[tool.zenzic.build_context]
engine = "mkdocs"
```

## Why this fixture exists

- Validates that `MkDocsAdapter` remains compatible with MkDocs 1.6.x config shapes.
- Demonstrates that Zenzic parses `mkdocs.yml` statically without calling MkDocs.
- Demonstrates the `zenzic.integrations.mkdocs` plugin as a build-time quality gate.
- Provides a migration-safe baseline before moving projects to Zensical.
