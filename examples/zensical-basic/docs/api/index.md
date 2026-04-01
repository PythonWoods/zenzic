# API Reference

This section is declared as a nested nav section in `zensical.toml`:

```toml
[project]
nav = [
    {"API" = [
        "api/index.md",
        {"Endpoints" = "api/endpoints.md"},
    ]},
]
```

## Overview

- [Endpoints](endpoints.md) — full list of API operations.

This reference page exists to verify that nested nav sections are interpreted
consistently by Zenzical and by Zenzic's `ZensicalAdapter`. The adapter must
extract `api/index.md` and `api/endpoints.md` from `[project].nav`, classify
both routes as reachable, and keep internal links fully portable with relative
paths only. This keeps the example realistic and lint-clean.

Return to the [Guide](../guide.md) or the [home page](../index.md).
