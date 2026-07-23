# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Shared test helpers importable from any test module.

Unlike ``conftest.py``, this module can be imported explicitly via::

    from _helpers import make_mgr
"""

from __future__ import annotations

from pathlib import Path

from zenzic.core.exclusion import LayeredExclusionManager
from zenzic.models.config import ZenzicConfig


def make_mgr(
    config: ZenzicConfig | None = None,
    *,
    repo_root: Path | None = None,
    docs_root: Path | None = None,
) -> LayeredExclusionManager:
    """Convenience helper: build a :class:`LayeredExclusionManager` for tests."""
    if config is None:
        config = ZenzicConfig()
    effective_docs = docs_root or (repo_root / config.docs_dir if repo_root else None)
    return LayeredExclusionManager(
        config,
        repo_root=repo_root,
        docs_root=effective_docs,
    )
