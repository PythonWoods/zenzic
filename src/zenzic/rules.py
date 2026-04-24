# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Public Plugin SDK — import from here in your plugin code.

Compatibility stub — canonical location is ``zenzic.core.rules``.
"""

from zenzic.core.rules import (
    BaseRule,
    CustomRule,
    RuleFinding,
    Severity,
    Violation,
    run_rule,
)


__all__ = ["BaseRule", "CustomRule", "RuleFinding", "Severity", "Violation", "run_rule"]
