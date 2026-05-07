# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Public API for the Zenzic CLI package.

All imports from outside this package must go through this module.
Internal ``_*.py`` modules are private implementation details.
"""

from __future__ import annotations

from ._check import (
    _AllCheckResults,
    _apply_target,
    _collect_all_results,
    _to_findings,
    check_app,
)
from ._clean import clean_app
from ._inspect import inspect_app
from ._lab import lab
from ._shared import (
    _count_docs_assets,
    _render_link_error,
    configure_console,
    get_console,
    get_ui,
)
from ._standalone import diff, init, score


__all__ = [
    # Typer sub-apps (registered in main.py)
    "check_app",
    "clean_app",
    "inspect_app",
    # Standalone commands (registered in main.py)
    "score",
    "diff",
    "init",
    "lab",
    # Console control (called from main.py @app.callback)
    "configure_console",
    # UI & console accessors (used by _lab.py)
    "get_ui",
    "get_console",
    # Internal utilities re-exported for _lab.py compatibility
    "_AllCheckResults",
    "_apply_target",
    "_collect_all_results",
    "_count_docs_assets",
    "_to_findings",
    "_render_link_error",
]
