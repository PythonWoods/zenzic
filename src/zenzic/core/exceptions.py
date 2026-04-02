# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Core exception hierarchy for Zenzic.

All user-facing errors inherit from ``ZenzicError``, which carries an optional
structured ``context`` dictionary for machine-readable diagnostics.  The CLI
catches ``ZenzicError`` at the top level and formats the message with Rich;
the plugin lets them propagate to MkDocs' own error handling.

Hierarchy::

    ZenzicError
    ├── ConfigurationError   — missing / malformed config files
    │   └── EngineError      — engine binary absent or incompatible
    ├── CheckError           — check machinery failure (not a finding)
    ├── NetworkError         — HTTP failure during link validation
    └── PluginContractError  — rule plugin violates the pickle / purity contract
"""

from __future__ import annotations

from typing import Any


class ZenzicError(Exception):
    """Base exception for all Zenzic errors with structured context support.

    Args:
        message: Human-readable error description shown to the user.
        context: Optional mapping of diagnostic key/value pairs appended to
            the string representation for debugging (e.g. ``{"file": "x.md",
            "line": 42}``).

    Examples:
        Basic usage::

            raise ZenzicError("Operation failed")

        With context::

            raise ZenzicError(
                "Nav parse failed",
                context={"file": "mkdocs.yml", "reason": "invalid YAML"},
            )
    """

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.context: dict[str, Any] = context or {}

    def __str__(self) -> str:
        if self.context:
            ctx_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} [{ctx_str}]"
        return self.message


class ConfigurationError(ZenzicError):
    """Raised when the project configuration is missing or invalid.

    Covers ``zensical.toml`` / ``mkdocs.yml`` not found, malformed TOML or
    YAML, and conflicting / unsupported configuration values.

    Examples::

        raise ConfigurationError(
            "zensical.toml not found in repository root",
            context={"searched": str(repo_root)},
        )
    """


class EngineError(ConfigurationError):
    """Raised when a documentation engine cannot be found or used.

    Inherits from ``ConfigurationError`` because the engine is part of the
    project setup.  Covers binary not on ``$PATH``, engine does not support
    the detected configuration format, and version incompatibilities.

    Examples::

        raise EngineError(
            "--engine zensical requires zensical.toml",
            context={"engine": "zensical", "missing_config": "zensical.toml"},
        )

        raise EngineError(
            "Engine 'mkdocs' not found on PATH",
            context={"engine": "mkdocs", "suggestion": "uv add --dev mkdocs"},
        )
    """


class CheckError(ZenzicError):
    """Raised when a check encounters an internal error.

    Distinct from check *findings* (broken links, orphans, invalid snippets)
    which are normal return values.  ``CheckError`` signals a failure in the
    check machinery itself: an unexpected I/O error, a parser crash, or an
    unrecoverable internal state.

    Examples::

        raise CheckError(
            "Failed to read file during asset scan",
            context={"file": str(path), "reason": str(exc)},
        )
    """


class NetworkError(ZenzicError):
    """Raised when an external HTTP request fails during link validation.

    A non-2xx HTTP status code is reported as a check *finding* and does not
    raise ``NetworkError``.  This exception is reserved for transport-level
    failures: connection timeouts, DNS errors, TLS handshake failures.

    Examples::

        raise NetworkError(
            "Connection timed out",
            context={"url": url, "timeout_s": 10},
        )
    """


class PluginContractError(ZenzicError):
    """Raised when a plugin rule violates the serialisability or purity contract.

    The :class:`~zenzic.core.rules.AdaptiveRuleEngine` validates every rule at
    construction time.  A rule that cannot be pickled (e.g. defined inside a
    function, or holding a reference to an unpickleable object) is rejected
    immediately with this error rather than failing inside a worker process.

    Examples::

        raise PluginContractError(
            "Rule 'MY-001' is not serialisable and cannot be used with the "
            "AdaptiveRuleEngine.",
            context={"rule_id": "MY-001", "cause": str(exc)},
        )
    """
