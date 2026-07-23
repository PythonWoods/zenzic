# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Public API surface for the Zenzic core engine.

Import the resolver and its outcome types from here::

    from zenzic.core import InMemoryPathResolver, Resolved, FileNotFound

Import the incremental analysis engine::

    from zenzic.core import IncrementalAnalysisEngine
"""

from zenzic.core.incremental import IncrementalAnalysisEngine
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
    "IncrementalAnalysisEngine",
    "InMemoryPathResolver",
    "PathTraversal",
    "Resolved",
    "ResolveOutcome",
]
