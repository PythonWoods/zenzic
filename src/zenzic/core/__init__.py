# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Public API surface for the Zenzic core engine.

Import the resolver and its outcome types from here::

    from zenzic.core import InMemoryPathResolver, Resolved, FileNotFound
"""

from zenzic.core.resolver import (
    AnchorMissing,
    FileNotFound,
    InMemoryPathResolver,
    PathTraversal,
    Resolved,
    ResolveOutcome,
)


__all__ = [
    "AnchorMissing",
    "FileNotFound",
    "InMemoryPathResolver",
    "PathTraversal",
    "Resolved",
    "ResolveOutcome",
]
