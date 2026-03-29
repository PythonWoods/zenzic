---
icon: lucide/plug
---

# Writing a Zenzic Adapter

This guide explains how to create a third-party adapter that teaches Zenzic to
understand your documentation engine's project layout, navigation structure, and
i18n conventions — without modifying Zenzic itself.

---

## What Is an Adapter?

An **adapter** is a Python class that satisfies the `BaseAdapter` protocol
(`src/zenzic/core/adapters/_base.py`).  Zenzic's
scanner, orphan detector, and link validator talk exclusively to this protocol —
they never import or call engine-specific code directly.

An adapter answers four questions for each docs tree:

| Method | Question |
|---|---|
| `is_locale_dir(part)` | Is this top-level directory a non-default locale? |
| `resolve_asset(missing_abs, docs_root)` | Does a default-locale fallback exist for this missing asset? |
| `is_shadow_of_nav_page(rel, nav_paths)` | Is this file a locale mirror of a nav-listed page? |
| `get_ignored_patterns()` | Which filename globs should the orphan check skip? |
| `get_nav_paths()` | Which `.md` paths are listed in this engine's nav config? |

---

## Step 1 — Create the Adapter Class

```python
# my_engine_adapter/adapter.py

from __future__ import annotations

from pathlib import Path
from typing import Any


class MyEngineAdapter:
    """Adapter for MyEngine documentation projects."""

    def __init__(
        self,
        config: dict[str, Any],
        docs_root: Path,
    ) -> None:
        self._docs_root = docs_root
        self._config = config
        # Extract whatever your engine's config format provides.
        self._nav_paths: frozenset[str] = self._parse_nav()

    # ── BaseAdapter protocol ───────────────────────────────────────────────

    def is_locale_dir(self, part: str) -> bool:
        """Return True when *part* is a non-default locale directory.

        If your engine does not support i18n, always return False.
        """
        locales: list[str] = self._config.get("locales", [])
        return part in locales

    def resolve_asset(self, missing_abs: Path, docs_root: Path) -> Path | None:
        """Return the default-locale fallback path for a missing locale asset.

        If your engine does not support i18n asset fallback, always return None.
        """
        return None

    def is_shadow_of_nav_page(self, rel: Path, nav_paths: frozenset[str]) -> bool:
        """Return True when *rel* is a locale mirror of a nav-listed page.

        Example: docs/fr/guide/index.md shadows guide/index.md.
        If your engine does not support i18n, always return False.
        """
        if not rel.parts or not self.is_locale_dir(rel.parts[0]):
            return False
        default_rel = Path(*rel.parts[1:]).as_posix()
        return default_rel in nav_paths

    def get_ignored_patterns(self) -> set[str]:
        """Return glob patterns for files the orphan check should skip.

        For suffix-mode i18n plugins, return patterns like {'*.fr.md', '*.it.md'}.
        """
        return set()

    def get_nav_paths(self) -> frozenset[str]:
        """Return the set of .md paths listed in the engine's nav, relative to docs_root."""
        return self._nav_paths

    # ── Private helpers ────────────────────────────────────────────────────

    def _parse_nav(self) -> frozenset[str]:
        nav = self._config.get("nav", [])
        paths: set[str] = set()
        for entry in nav:
            if isinstance(entry, str) and entry.endswith(".md"):
                paths.add(entry.lstrip("/"))
        return frozenset(paths)
```

---

## Step 2 — Register via Entry Points

Zenzic discovers adapters through the `zenzic.adapters` entry-point group.
Register your adapter in your package's `pyproject.toml`:

```toml
[project.entry-points."zenzic.adapters"]
myengine = "my_engine_adapter.adapter:MyEngineAdapter"
```

The **key** (left of `=`) becomes the engine name users pass to `--engine` or
set as `engine` in `zenzic.toml`:

```toml
# In the user's zenzic.toml
[build_context]
engine = "myengine"
```

---

## Step 3 — Implement the Factory Hook (Optional)

By default, Zenzic instantiates your adapter by calling:

```python
adapter_class(context, docs_root, config_dict)
```

where `context` is a `BuildContext` instance and `config_dict` is the parsed
engine config (or `{}` if discovery failed).

If your adapter needs a different constructor signature, implement a
`from_repo(context, docs_root, repo_root)` classmethod and Zenzic will prefer it:

```python
@classmethod
def from_repo(
    cls,
    context: "BuildContext",
    docs_root: Path,
    repo_root: Path,
) -> "MyEngineAdapter":
    config_path = repo_root / "myengine.toml"
    config = {}
    if config_path.exists():
        import tomllib
        with config_path.open("rb") as f:
            config = tomllib.load(f)
    return cls(config, docs_root)
```

---

## Step 4 — Validate with Zenzic

After installing your package (`uv pip install -e .` or `pip install -e .`),
verify the adapter is discovered:

```bash
# List all installed adapters
zenzic check orphans --engine myengine --help

# Run against a real docs tree
zenzic check orphans --engine myengine
zenzic check all --engine myengine
```

---

## Step 5 — Custom Rules Are Engine-Independent

`[[custom_rules]]` in `zenzic.toml` run on raw Markdown source and are
completely decoupled from the adapter layer.  A rule that searches for `DRAFT`
will fire identically whether the adapter is MkDocs, Zensical, or your own
engine.  No extra work is required to make custom rules compatible with a new
adapter.

---

## Adapter Contract Guarantees

Your adapter must satisfy these invariants, or Zenzic's scanner may produce
incorrect results:

1. `get_nav_paths()` returns paths **relative to `docs_root`**, using forward
   slashes, with no leading `/`.
2. `get_nav_paths()` returns only `.md` files (other extensions are ignored by
   the orphan checker).
3. `is_locale_dir()` must return `False` for the **default** locale.  Only
   non-default locale directories should return `True`.
4. All methods must be **pure**: same inputs always produce the same outputs.
   No I/O, no global-state mutation.
5. `resolve_asset()` must never raise — return `None` on any failure.

---

## Testing Your Adapter

Use `zenzic.core.adapters.BaseAdapter` as the typing target in your tests to
verify protocol compliance:

```python
from zenzic.core.adapters import BaseAdapter
from my_engine_adapter.adapter import MyEngineAdapter

def test_satisfies_protocol() -> None:
    adapter = MyEngineAdapter(config={}, docs_root=Path("/tmp/docs"))
    assert isinstance(adapter, BaseAdapter)

def test_nav_paths_relative() -> None:
    adapter = MyEngineAdapter(
        config={"nav": ["index.md", "guide/setup.md"]},
        docs_root=Path("/tmp/docs"),
    )
    paths = adapter.get_nav_paths()
    assert "index.md" in paths
    assert "guide/setup.md" in paths
    assert all(not p.startswith("/") for p in paths)
```
