# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for the Zenzic Finding Code Registry (codes.py).

Ensures that every registered Zxxx code has complete SARIF metadata
(description, default level, CamelCase name) so the SARIF output is
always valid and never emits incomplete rule entries.
"""

from __future__ import annotations

import pytest

from zenzic.core.codes import (
    CODE_DESCRIPTIONS,
    CODE_NAMES,
    CODE_SARIF_LEVELS,
    get_sarif_name,
)


# ── Completeness: every code in CODE_NAMES must have full metadata ─────────────


def test_every_code_has_description() -> None:
    """Each code in CODE_NAMES must have a corresponding CODE_DESCRIPTIONS entry."""
    missing = sorted(set(CODE_NAMES) - set(CODE_DESCRIPTIONS))
    assert missing == [], f"Codes missing from CODE_DESCRIPTIONS: {missing}"


def test_every_code_has_sarif_level() -> None:
    """Each code in CODE_NAMES must have a corresponding CODE_SARIF_LEVELS entry."""
    missing = sorted(set(CODE_NAMES) - set(CODE_SARIF_LEVELS))
    assert missing == [], f"Codes missing from CODE_SARIF_LEVELS: {missing}"


def test_no_orphan_descriptions() -> None:
    """No code in CODE_DESCRIPTIONS may be absent from CODE_NAMES (ghost metadata)."""
    orphans = sorted(set(CODE_DESCRIPTIONS) - set(CODE_NAMES))
    assert orphans == [], f"Ghost codes in CODE_DESCRIPTIONS (not in CODE_NAMES): {orphans}"


def test_no_orphan_sarif_levels() -> None:
    """No code in CODE_SARIF_LEVELS may be absent from CODE_NAMES (ghost metadata)."""
    orphans = sorted(set(CODE_SARIF_LEVELS) - set(CODE_NAMES))
    assert orphans == [], f"Ghost codes in CODE_SARIF_LEVELS (not in CODE_NAMES): {orphans}"


# ── SARIF level values must be valid ───────────────────────────────────────────

_VALID_SARIF_LEVELS = {"error", "warning", "note", "none"}


def test_sarif_levels_are_valid_values() -> None:
    """All entries in CODE_SARIF_LEVELS must be a valid SARIF level string."""
    invalid = {
        code: level for code, level in CODE_SARIF_LEVELS.items() if level not in _VALID_SARIF_LEVELS
    }
    assert invalid == {}, f"Invalid SARIF levels: {invalid}"


# ── Severity policy: Z1xx/Z2xx must be 'error', Z906 must be 'note' ───────────


@pytest.mark.parametrize("code", [c for c in CODE_NAMES if c.startswith("Z1")])
def test_z1xx_sarif_level_is_error(code: str) -> None:
    """Z1xx (Link Integrity) codes must have SARIF level 'error'."""
    assert CODE_SARIF_LEVELS[code] == "error", (
        f"{code} should be 'error' (Link Integrity), got '{CODE_SARIF_LEVELS[code]}'"
    )


@pytest.mark.parametrize("code", [c for c in CODE_NAMES if c.startswith("Z2")])
def test_z2xx_sarif_level_is_error(code: str) -> None:
    """Z2xx (Security) codes must have SARIF level 'error'."""
    assert CODE_SARIF_LEVELS[code] == "error", (
        f"{code} should be 'error' (Security), got '{CODE_SARIF_LEVELS[code]}'"
    )


def test_z906_sarif_level_is_note() -> None:
    """Z906 NO_FILES_FOUND is informational — must be SARIF level 'note'."""
    assert CODE_SARIF_LEVELS["Z906"] == "note"


# ── get_sarif_name: deterministic CamelCase conversion ─────────────────────────


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("Z101", "LinkBroken"),
        ("Z201", "ShieldSecret"),
        ("Z402", "OrphanPage"),
        ("Z505", "UntaggedCodeBlock"),
        ("Z906", "NoFilesFound"),
        ("Z203", "PathTraversalFatal"),
    ],
)
def test_get_sarif_name_camelcase(code: str, expected: str) -> None:
    assert get_sarif_name(code) == expected


def test_get_sarif_name_unknown_code_falls_back_to_code() -> None:
    """An unknown code must return the raw code string, not raise."""
    assert get_sarif_name("Z999") == "Z999"


def test_get_sarif_name_all_codes_non_empty() -> None:
    """Every registered code must produce a non-empty CamelCase name."""
    for code in CODE_NAMES:
        name = get_sarif_name(code)
        assert name, f"get_sarif_name('{code}') returned empty string"
        assert "_" not in name, f"get_sarif_name('{code}') still contains underscore: '{name}'"
