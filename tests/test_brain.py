# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for the Sovereign Cartography module (CEO-242) and Identity Gate (CEO-246)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from zenzic.core.cartography import (
    MAP_END,
    MAP_START,
    ModuleInfo,
    render_markdown_table,
    scan_python_sources,
    update_ledger,
)


# ─── ModuleInfo ───────────────────────────────────────────────────────────────


class TestModuleInfo:
    def test_dataclass_defaults(self) -> None:
        mi = ModuleInfo(rel_path="foo.py")
        assert mi.classes == []
        assert mi.public_functions == []
        assert mi.docstring == ""

    def test_explicit_fields(self) -> None:
        mi = ModuleInfo(
            rel_path="core/shield.py",
            classes=["ShieldViolation"],
            public_functions=["scan_line"],
            docstring="Credential scanner.",
        )
        assert mi.rel_path == "core/shield.py"
        assert "ShieldViolation" in mi.classes
        assert "scan_line" in mi.public_functions


# ─── scan_python_sources ──────────────────────────────────────────────────────


class TestScanPythonSources:
    def test_returns_module_info_list(self, tmp_path: Path) -> None:
        (tmp_path / "hello.py").write_text(
            '"""Hello module."""\n\ndef greet():\n    pass\n', encoding="utf-8"
        )
        results = scan_python_sources(tmp_path)
        assert len(results) == 1
        assert results[0].rel_path == "hello.py"
        assert results[0].docstring == "Hello module."
        assert "greet" in results[0].public_functions

    def test_excludes_init_files(self, tmp_path: Path) -> None:
        (tmp_path / "__init__.py").write_text("", encoding="utf-8")
        (tmp_path / "real.py").write_text("def foo(): pass", encoding="utf-8")
        results = scan_python_sources(tmp_path)
        rel_paths = [r.rel_path for r in results]
        assert "__init__.py" not in rel_paths
        assert "real.py" in rel_paths

    def test_excludes_tests_directory(self, tmp_path: Path) -> None:
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_foo.py").write_text("def test_it(): pass", encoding="utf-8")
        (tmp_path / "real.py").write_text("def foo(): pass", encoding="utf-8")
        results = scan_python_sources(tmp_path)
        rel_paths = [r.rel_path for r in results]
        assert "real.py" in rel_paths
        # Files inside tests/ directory must be excluded
        assert not any("tests" in p for p in rel_paths)

    def test_excludes_private_functions(self, tmp_path: Path) -> None:
        (tmp_path / "mod.py").write_text(
            "def public(): pass\ndef _private(): pass\n", encoding="utf-8"
        )
        results = scan_python_sources(tmp_path)
        assert "public" in results[0].public_functions
        assert "_private" not in results[0].public_functions

    def test_captures_public_classes_only(self, tmp_path: Path) -> None:
        (tmp_path / "mod.py").write_text("class Foo: pass\nclass _Bar: pass\n", encoding="utf-8")
        results = scan_python_sources(tmp_path)
        assert "Foo" in results[0].classes
        assert "_Bar" not in results[0].classes

    def test_handles_syntax_error_gracefully(self, tmp_path: Path) -> None:
        (tmp_path / "broken.py").write_text("def (: pass", encoding="utf-8")
        results = scan_python_sources(tmp_path)
        assert len(results) == 1
        assert results[0].docstring == "[SYNTAX ERROR]"

    def test_returns_sorted_results(self, tmp_path: Path) -> None:
        (tmp_path / "zzz.py").write_text("def z(): pass", encoding="utf-8")
        (tmp_path / "aaa.py").write_text("def a(): pass", encoding="utf-8")
        results = scan_python_sources(tmp_path)
        assert results[0].rel_path == "aaa.py"
        assert results[1].rel_path == "zzz.py"

    def test_no_docstring_returns_empty_string(self, tmp_path: Path) -> None:
        (tmp_path / "nodoc.py").write_text("def foo(): pass\n", encoding="utf-8")
        results = scan_python_sources(tmp_path)
        assert results[0].docstring == ""

    def test_only_first_line_of_docstring_used(self, tmp_path: Path) -> None:
        (tmp_path / "multi.py").write_text(
            '"""First line.\n\nSecond paragraph.\n"""\n', encoding="utf-8"
        )
        results = scan_python_sources(tmp_path)
        assert results[0].docstring == "First line."


# ─── render_markdown_table ────────────────────────────────────────────────────


class TestRenderMarkdownTable:
    def test_renders_table_header(self) -> None:
        md = render_markdown_table([])
        assert "| File |" in md
        assert "Auto-generated" in md

    def test_renders_module_row(self) -> None:
        modules = [
            ModuleInfo(
                rel_path="core/shield.py",
                classes=["ShieldViolation"],
                public_functions=["scan_line"],
                docstring="Credential scanner.",
            )
        ]
        md = render_markdown_table(modules)
        assert "`core/shield.py`" in md
        assert "`ShieldViolation`" in md
        assert "`scan_line`" in md
        assert "Credential scanner." in md

    def test_empty_classes_shows_dash(self) -> None:
        modules = [ModuleInfo(rel_path="mod.py", public_functions=["foo"])]
        md = render_markdown_table(modules)
        # Classes column should be "—"
        assert "| `mod.py` | — |" in md

    def test_undocumented_module_shows_warning(self) -> None:
        modules = [ModuleInfo(rel_path="mod.py")]
        md = render_markdown_table(modules)
        assert "[⚠️ UNDOCUMENTED]" in md

    def test_multiple_classes_comma_separated(self) -> None:
        modules = [ModuleInfo(rel_path="m.py", classes=["Foo", "Bar"])]
        md = render_markdown_table(modules)
        assert "`Foo`, `Bar`" in md

    def test_returns_string(self) -> None:
        assert isinstance(render_markdown_table([]), str)


# ─── update_ledger ────────────────────────────────────────────────────────────


class TestUpdateLedger:
    def test_updates_map_section(self, tmp_path: Path) -> None:
        ledger = tmp_path / "ZENZIC_BRAIN.md"
        ledger.write_text(
            f"# Header\n\n{MAP_START}\nOLD CONTENT\n{MAP_END}\n\n# Footer\n",
            encoding="utf-8",
        )
        updated = update_ledger(ledger, "NEW CONTENT")
        assert updated is True
        text = ledger.read_text(encoding="utf-8")
        assert "NEW CONTENT" in text
        assert "OLD CONTENT" not in text
        assert "# Header" in text
        assert "# Footer" in text

    def test_returns_false_when_no_change(self, tmp_path: Path) -> None:
        ledger = tmp_path / "ZENZIC_BRAIN.md"
        content = f"# H\n{MAP_START}\nCONTENT\n{MAP_END}\n"
        ledger.write_text(content, encoding="utf-8")
        updated = update_ledger(ledger, "CONTENT")
        assert updated is False
        assert ledger.read_text(encoding="utf-8") == content

    def test_raises_if_start_marker_missing(self, tmp_path: Path) -> None:
        ledger = tmp_path / "BRAIN.md"
        ledger.write_text(f"No markers here.\n{MAP_END}\n", encoding="utf-8")
        with pytest.raises(ValueError, match="not found"):
            update_ledger(ledger, "anything")

    def test_raises_if_end_marker_missing(self, tmp_path: Path) -> None:
        ledger = tmp_path / "BRAIN.md"
        ledger.write_text(f"{MAP_START}\nno end marker\n", encoding="utf-8")
        with pytest.raises(ValueError, match="not found"):
            update_ledger(ledger, "anything")

    def test_preserves_content_outside_markers(self, tmp_path: Path) -> None:
        ledger = tmp_path / "BRAIN.md"
        ledger.write_text(f"BEFORE\n{MAP_START}\nOLD\n{MAP_END}\nAFTER\n", encoding="utf-8")
        update_ledger(ledger, "NEW")
        text = ledger.read_text(encoding="utf-8")
        assert text.startswith("BEFORE\n")
        assert text.endswith("AFTER\n")


# ─── _is_dev_mode (CEO-246 Identity Gate) ────────────────────────────────────


class TestIsDevMode:
    def test_returns_bool(self) -> None:
        from zenzic.main import _is_dev_mode

        result = _is_dev_mode()
        assert isinstance(result, bool)

    def test_returns_false_for_missing_package(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import importlib.metadata

        from zenzic.main import _is_dev_mode

        monkeypatch.setattr(
            importlib.metadata,
            "distribution",
            lambda _: (_ for _ in ()).throw(importlib.metadata.PackageNotFoundError("zenzic")),
        )
        assert _is_dev_mode() is False

    def test_returns_false_for_empty_direct_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import importlib.metadata

        from zenzic.main import _is_dev_mode

        class FakeDist:
            def read_text(self, filename: str) -> None:
                return None

        monkeypatch.setattr(importlib.metadata, "distribution", lambda _: FakeDist())
        assert _is_dev_mode() is False

    def test_returns_false_for_non_editable_install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import importlib.metadata

        from zenzic.main import _is_dev_mode

        class FakeDist:
            def read_text(self, filename: str) -> str:
                return json.dumps({"url": "https://files.example.com/zenzic-0.7.0.tar.gz"})

        monkeypatch.setattr(importlib.metadata, "distribution", lambda _: FakeDist())
        assert _is_dev_mode() is False

    def test_returns_false_when_editable_is_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import importlib.metadata

        from zenzic.main import _is_dev_mode

        class FakeDist:
            def read_text(self, filename: str) -> str:
                return json.dumps(
                    {
                        "url": "file:///home/user/zenzic",
                        "dir_info": {"editable": False},
                    }
                )

        monkeypatch.setattr(importlib.metadata, "distribution", lambda _: FakeDist())
        assert _is_dev_mode() is False

    def test_returns_true_for_editable_install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import importlib.metadata

        from zenzic.main import _is_dev_mode

        class FakeDist:
            def read_text(self, filename: str) -> str:
                return json.dumps(
                    {
                        "url": "file:///home/user/zenzic",
                        "dir_info": {"editable": True},
                    }
                )

        monkeypatch.setattr(importlib.metadata, "distribution", lambda _: FakeDist())
        assert _is_dev_mode() is True

    def test_returns_false_for_invalid_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import importlib.metadata

        from zenzic.main import _is_dev_mode

        class FakeDist:
            def read_text(self, filename: str) -> str:
                return "{ not valid json"

        monkeypatch.setattr(importlib.metadata, "distribution", lambda _: FakeDist())
        assert _is_dev_mode() is False
