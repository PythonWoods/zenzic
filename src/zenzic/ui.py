# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Compatibility stub — canonical location is ``zenzic.core.ui``.

Third-party plugins and external code that import from ``zenzic.ui`` continue
to work unchanged.  All new internal code should import from ``zenzic.core.ui``.
"""

from zenzic.core.ui import *  # noqa: F401, F403
