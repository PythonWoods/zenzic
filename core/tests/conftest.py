# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Shared pytest configuration, Hypothesis profiles, and test helpers.

Hypothesis profiles
───────────────────
- **dev** (default): 50 examples per test — fast local iteration.
- **ci**: 500 examples per test — thorough, used in CI pipelines.
- **purity**: 1 000 examples per test — pre-release exhaustive check.

Select a profile via the ``HYPOTHESIS_PROFILE`` environment variable::

    HYPOTHESIS_PROFILE=ci just test
    HYPOTHESIS_PROFILE=purity just test   # before a release
"""

from __future__ import annotations

import logging
import os

import pytest
from hypothesis import HealthCheck, settings


@pytest.fixture(autouse=True)
def _reset_zenzic_logger():
    """Reset the ``zenzic`` logger after each test.

    CLI-invoking tests call ``setup_cli_logging()``, which installs a
    ``RichHandler`` and sets ``propagate=False`` on the ``zenzic`` root
    logger.  This leaks into subsequent tests that use ``caplog``, which
    relies on propagation reaching the root logger.

    Teardown removes any ``RichHandler`` instances and restores propagation
    so that ``caplog`` captures log records correctly regardless of test
    execution order.
    """
    yield
    zenzic_logger = logging.getLogger("zenzic")
    zenzic_logger.handlers = [
        h for h in zenzic_logger.handlers if h.__class__.__name__ != "RichHandler"
    ]
    if not zenzic_logger.handlers:
        zenzic_logger.propagate = True


_SUPPRESS = [HealthCheck.too_slow, HealthCheck.differing_executors]


settings.register_profile(
    "ci",
    max_examples=500,
    suppress_health_check=_SUPPRESS,
)
settings.register_profile(
    "dev",
    max_examples=50,
    suppress_health_check=_SUPPRESS,
)
settings.register_profile(
    "purity",
    max_examples=1000,
    suppress_health_check=_SUPPRESS,
)

settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))
