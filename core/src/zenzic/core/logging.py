# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Logging configuration for Zenzic.

Two distinct logging surfaces:

* **CLI mode** — the CLI sets up a root ``zenzic`` logger backed by
  ``RichHandler`` so that log records are formatted consistently with the
  Rich console used for check output.  Call :func:`setup_cli_logging` once
  at startup (``main.py``) and then use :func:`get_logger` anywhere inside
  the ``zenzic`` package.

* **Plugin mode** — MkDocs owns the logging hierarchy.  The plugin acquires
  ``logging.getLogger("mkdocs.plugins.zenzic")`` directly; this module is
  not involved.  :func:`get_logger` returns a plain ``zenzic`` child logger
  that inherits whatever handlers the host application has attached.
"""

from __future__ import annotations

import logging

from rich.logging import RichHandler


LOGGER_NAME = "zenzic"


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a ``zenzic[.name]`` logger.

    Args:
        name: Optional sub-name appended after ``"zenzic."``.
              Pass ``__name__`` from the calling module for structured
              namespacing (e.g. ``"zenzic.core.validator"``).

    Returns:
        A :class:`logging.Logger` that is a child of the root ``zenzic``
        logger.  If :func:`setup_cli_logging` has been called, the root
        logger carries a ``RichHandler``; otherwise records propagate to
        whatever the host application has configured.
    """
    if name:
        return logging.getLogger(f"{LOGGER_NAME}.{name}")
    return logging.getLogger(LOGGER_NAME)


def setup_cli_logging(level: int = logging.WARNING) -> None:
    """Configure the ``zenzic`` root logger for CLI use.

    Attaches a :class:`~rich.logging.RichHandler` so that log records are
    formatted with Rich markup, consistent with the rest of the CLI output.
    Safe to call multiple times — a second call is a no-op when a
    ``RichHandler`` is already attached.

    Must be called from ``main.py`` before any other Zenzic code runs, and
    must *not* be called from the plugin (MkDocs owns the logging hierarchy
    in that context).

    Args:
        level: Minimum log level to emit (default: ``logging.WARNING``).
               Pass ``logging.DEBUG`` to enable verbose diagnostic output.
    """
    logger = logging.getLogger(LOGGER_NAME)
    if any(isinstance(h, RichHandler) for h in logger.handlers):
        return  # already configured

    handler = RichHandler(
        level=level,
        show_time=False,
        show_path=False,
        rich_tracebacks=True,
        markup=True,
    )
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
