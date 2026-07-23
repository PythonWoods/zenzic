# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Re-export shim — canonical location is ``zenzic.models.references``.

Import from ``zenzic.models.references`` directly.  This module exists only
to satisfy any internal cross-package imports that may reference the ``core``
package for data models.
"""

from zenzic.models.references import IntegrityReport, ReferenceFinding, ReferenceMap


__all__ = ["IntegrityReport", "ReferenceFinding", "ReferenceMap"]
