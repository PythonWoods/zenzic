# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Adapter factory — dynamic entry-point discovery with VanillaAdapter fallback.

Adapter registration
--------------------
Adapters are discovered via the ``zenzic.adapters`` entry-point group.  Any
installed package can contribute an adapter by declaring it in ``pyproject.toml``::

    [project.entry-points."zenzic.adapters"]
    myengine = "my_package.adapter:MyEngineAdapter"

The **key** (e.g. ``myengine``) is the engine name users declare in
``zenzic.toml`` or pass via ``--engine``.

Adapter construction protocol
------------------------------
The factory prefers a ``from_repo(context, docs_root, repo_root)`` classmethod
when it exists on the loaded class.  This lets adapters perform their own config
discovery and enforcement (e.g. raising ``ConfigurationError`` when a required
engine config file is missing).

When ``from_repo`` is absent the factory falls back to calling
``AdapterClass(context, docs_root)``.

Fallback
--------
When no entry point matches the requested engine, :class:`VanillaAdapter` is
returned.  This keeps Zenzic functional as a plain Markdown linter even when
the docs engine is not installed.
"""

from __future__ import annotations

from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

from zenzic.models.config import BuildContext

from ._docusaurus import DocusaurusAdapter
from ._mkdocs import MkDocsAdapter
from ._vanilla import VanillaAdapter
from ._zensical import ZensicalAdapter


# Built-in adapters registered by engine name.  Entry-point discovery can
# override these, but they are always available even when the package is
# installed in a venv that pre-dates the ``zenzic.adapters`` entry-point group.
_BUILTIN_ADAPTERS: dict[str, type[Any]] = {
    "docusaurus": DocusaurusAdapter,
    "mkdocs": MkDocsAdapter,
    "zensical": ZensicalAdapter,
    "vanilla": VanillaAdapter,
}


def _load_adapter_class(engine: str) -> type[Any] | None:
    """Return the adapter class registered for *engine*, or ``None``.

    Resolution order:
    1. ``zenzic.adapters`` entry-point group (allows third-party overrides).
    2. Built-in adapter registry (always available regardless of install state).
    """
    eps = entry_points(group="zenzic.adapters")
    for ep in eps:
        if ep.name == engine:
            return ep.load()  # type: ignore[no-any-return]
    return _BUILTIN_ADAPTERS.get(engine)


def list_adapter_engines() -> list[str]:
    """Return sorted list of engine names registered in ``zenzic.adapters``."""
    eps = entry_points(group="zenzic.adapters")
    return sorted(ep.name for ep in eps)


def get_adapter(
    context: BuildContext,
    docs_root: Path,
    repo_root: Path,
) -> Any:
    """Return the adapter for the declared build engine via entry-point discovery.

    Resolution order:

    1. Query the ``zenzic.adapters`` entry-point group for an adapter whose
       name matches ``context.engine``.
    2. If found: instantiate via ``from_repo(context, docs_root, repo_root)``
       classmethod when present; otherwise call
       ``AdapterClass(context, docs_root)``.
    3. If not found: return :class:`VanillaAdapter` (neutral no-op behaviour).

    This design means adding a new engine adapter **never requires modifying
    Zenzic core** — only installing an adapter package is required.

    Args:
        context: Build context from ``zenzic.toml``.
        docs_root: Resolved absolute path to the ``docs/`` directory.
        repo_root: Resolved absolute path to the repository root (passed to
            ``from_repo`` when the adapter supports it).

    Returns:
        A concrete adapter instance satisfying the
        :class:`~zenzic.core.adapters.BaseAdapter` protocol.

    Raises:
        :class:`~zenzic.core.exceptions.ConfigurationError`: When the
            discovered adapter's ``from_repo`` raises one (e.g.
            ``ZensicalAdapter`` raises when ``zensical.toml`` is absent).
    """
    adapter_class = _load_adapter_class(context.engine)
    if adapter_class is None:
        return VanillaAdapter()

    # VanillaAdapter is a no-op stub with no constructor arguments.
    if adapter_class is VanillaAdapter:
        return VanillaAdapter()

    # Prefer the richer from_repo constructor when available.
    if hasattr(adapter_class, "from_repo"):
        adapter = adapter_class.from_repo(context, docs_root, repo_root)
    else:
        adapter = adapter_class(context, docs_root)

    # If the adapter found no engine config and no locale information, fall
    # back to VanillaAdapter so nav-dependent checks are skipped cleanly.
    if not adapter.has_engine_config():
        return VanillaAdapter()
    return adapter
