# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for Atomic Write Barrier and AST Auto-Fix Hardening."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from zenzic.cli._fix import _atomic_write
from zenzic.core.mutator import EmptyLinkTextMutation, Mutator
from zenzic.core.parser import parse, serialize
from zenzic.core.validator import _extract_empty_link_texts


def test_atomic_write_symlink_preservation(tmp_path: Path) -> None:
    """The Symlink Trap: atomic write resolves symlinks, leaving the link intact and updating target."""
    target_file = tmp_path / "real_file.md"
    symlink_file = tmp_path / "symlink_file.md"

    target_file.write_text("Original content", encoding="utf-8")
    symlink_file.symlink_to(target_file)

    assert symlink_file.is_symlink()

    # Call _atomic_write on the symlink
    _atomic_write(symlink_file, "Updated content")

    # Verify the target file got the new content
    assert target_file.read_text(encoding="utf-8") == "Updated content"

    # Verify the symlink itself remains a symlink and is not replaced by a regular file
    assert symlink_file.is_symlink()
    assert symlink_file.resolve() == target_file.resolve()


def test_atomic_write_keyboard_interrupt_cleanup(tmp_path: Path) -> None:
    """Permission/Termination Denial: KeyboardInterrupt does not leak temporary files."""
    test_file = tmp_path / "test_file.md"
    test_file.write_text("Original content", encoding="utf-8")

    # Mock os.replace to raise KeyboardInterrupt
    with patch("os.replace", side_effect=KeyboardInterrupt("Simulated Ctrl-C")):
        with pytest.raises(KeyboardInterrupt, match="Simulated Ctrl-C"):
            _atomic_write(test_file, "New content")

    # Check that no temp files starting with .zenzic-tmp- exist in the directory
    temp_files = list(tmp_path.glob(".zenzic-tmp-*"))
    assert len(temp_files) == 0, f"Leaked temporary files found: {temp_files}"


def test_formatted_empty_link_validation_and_mutation() -> None:
    """AST Drift / Empty Link Bypass: Formatted empty links are correctly flagged and mutated."""
    empty_formats = [
        "[](url)",
        "[ ](url)",
        "[**](url)",
        "[*_~` `~_*](url)",
        "[*](url)",
        "[**][ref]",
    ]

    # 1. Test Validator Flags them
    for text in empty_formats:
        findings = _extract_empty_link_texts(text)
        assert len(findings) == 1, f"Expected validator to flag: {text}"

    # 2. Test Mutator Fixes them
    mutator = Mutator([EmptyLinkTextMutation()])

    for text in empty_formats:
        if "ref" in text:
            # References aren't inline links in standard parsing as LinkNode, skip mutation test
            continue
        ast = parse(text)
        new_ast, changed = mutator.mutate(ast)
        assert changed, f"Expected mutator to change: {text}"

        serialized = serialize(new_ast)
        assert serialized == "[MISSING LINK LABEL](url)", f"Got: {serialized}"
