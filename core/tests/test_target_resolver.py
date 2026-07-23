# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from zenzic.cli._target_resolver import _resolve_target
from zenzic.models.config import ZenzicConfig


def test_resolve_target_strips_fragments_and_queries(tmp_path: Path) -> None:
    """_resolve_target must strip #fragments and ?queries before Path.exists() checks."""
    repo_root = tmp_path / "repo"
    docs_dir = repo_root / "docs"
    docs_dir.mkdir(parents=True)

    # Create a dummy md file
    target_file = docs_dir / "page.md"
    target_file.touch()

    config = ZenzicConfig(docs_dir=Path("docs"))

    # Test with fragment
    raw_fragment = "docs/page.md#gh-light-mode-only"
    resolved_fragment = _resolve_target(repo_root, config, raw_fragment)
    assert resolved_fragment == target_file.resolve()

    # Test with query string
    raw_query = "docs/page.md?version=1.0"
    resolved_query = _resolve_target(repo_root, config, raw_query)
    assert resolved_query == target_file.resolve()

    # Test with both
    raw_both = "docs/page.md?version=1.0#gh-light-mode-only"
    resolved_both = _resolve_target(repo_root, config, raw_both)
    assert resolved_both == target_file.resolve()
