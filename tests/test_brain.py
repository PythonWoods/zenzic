# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Tests for the Sovereign Cartography module (CEO-242) and Identity Gate (CEO-246)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from zenzic.core.cartography import (
    MAP_END,
    MAP_START,
    ModuleInfo,
    check_perimeter,
    check_sources_perimeter,
    load_dev_gate,
    render_json,
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


# ─── brain_map --check (CEO-257 Quartz Audit Gate) ───────────────────────────


class TestBrainMapCheck:
    """Typer CLI tests for ``zenzic brain map --check`` (D001 MEMORY_STALE)."""

    def _make_src(self, base: Path) -> None:
        """Create a minimal src/<pkg>/ layout so scan_python_sources finds files."""
        pkg = base / "src" / "mypkg"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "core.py").write_text(
            '"""Core module."""\n\ndef run() -> None:\n    pass\n', encoding="utf-8"
        )

    def _make_ledger(self, base: Path, map_content: str) -> Path:
        ledger = base / "ZENZIC_BRAIN.md"
        ledger.write_text(
            f"# Header\n\n{MAP_START}\n{map_content}\n{MAP_END}\n\nFooter\n",
            encoding="utf-8",
        )
        return ledger

    def test_check_exits_0_when_map_in_sync(self, tmp_path: Path) -> None:
        from typer.testing import CliRunner

        from zenzic.cli._brain import brain_app
        from zenzic.core.cartography import render_markdown_table, scan_python_sources

        self._make_src(tmp_path)
        src_root = tmp_path / "src" / "mypkg"
        modules = scan_python_sources(src_root)
        current_map = render_markdown_table(modules)
        self._make_ledger(tmp_path, current_map)

        runner = CliRunner()
        result = runner.invoke(brain_app, [str(tmp_path), "--check"])
        assert result.exit_code == 0, result.output
        assert "memory intact" in result.output

    def test_check_exits_1_when_map_stale(self, tmp_path: Path) -> None:
        from typer.testing import CliRunner

        from zenzic.cli._brain import brain_app

        self._make_src(tmp_path)
        # Deliberately wrong map content
        self._make_ledger(tmp_path, "| `stale/module.py` | OldClass | old_fn | Outdated. |")

        runner = CliRunner()
        result = runner.invoke(brain_app, [str(tmp_path), "--check"])
        assert result.exit_code == 1
        assert "D001" in result.output or "D001" in (result.stderr or "")

    def test_check_exits_1_when_markers_missing(self, tmp_path: Path) -> None:
        from typer.testing import CliRunner

        from zenzic.cli._brain import brain_app

        self._make_src(tmp_path)
        ledger = tmp_path / "ZENZIC_BRAIN.md"
        ledger.write_text("# No markers here\n", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(brain_app, [str(tmp_path), "--check"])
        assert result.exit_code == 1
        assert "D001" in result.output or "D001" in (result.stderr or "")

    def test_check_exits_1_when_no_ledger(self, tmp_path: Path) -> None:
        from typer.testing import CliRunner

        from zenzic.cli._brain import brain_app

        self._make_src(tmp_path)
        # No ZENZIC_BRAIN.md created

        runner = CliRunner()
        result = runner.invoke(brain_app, [str(tmp_path), "--check"])
        assert result.exit_code == 1
        assert "D001" in result.output or "D001" in (result.stderr or "")

    def test_check_does_not_write_ledger(self, tmp_path: Path) -> None:
        from typer.testing import CliRunner

        from zenzic.cli._brain import brain_app

        self._make_src(tmp_path)
        self._make_ledger(tmp_path, "stale content")
        ledger = tmp_path / "ZENZIC_BRAIN.md"
        original_text = ledger.read_text(encoding="utf-8")

        runner = CliRunner()
        runner.invoke(brain_app, [str(tmp_path), "--check"])

        # File must not have been modified
        assert ledger.read_text(encoding="utf-8") == original_text


# ─── load_dev_gate ────────────────────────────────────────────────────────────


class TestLoadDevGate:
    """Tests for ``load_dev_gate`` (CEO-260)."""

    def test_returns_empty_when_no_file(self, tmp_path: Path) -> None:
        assert load_dev_gate(tmp_path) == []

    def test_returns_patterns_when_file_exists(self, tmp_path: Path) -> None:
        (tmp_path / ".zenzic.dev.toml").write_text(
            '[development_gate]\nforbidden_patterns = ["secret-corp", "internal-host"]\n',
            encoding="utf-8",
        )
        result = load_dev_gate(tmp_path)
        assert result == ["secret-corp", "internal-host"]

    def test_returns_empty_when_section_missing(self, tmp_path: Path) -> None:
        (tmp_path / ".zenzic.dev.toml").write_text("[other_section]\nfoo = 1\n", encoding="utf-8")
        assert load_dev_gate(tmp_path) == []

    def test_returns_empty_when_key_missing(self, tmp_path: Path) -> None:
        (tmp_path / ".zenzic.dev.toml").write_text("[development_gate]\n", encoding="utf-8")
        assert load_dev_gate(tmp_path) == []

    def test_returns_empty_on_invalid_toml(self, tmp_path: Path) -> None:
        (tmp_path / ".zenzic.dev.toml").write_text("not valid toml [[[\n", encoding="utf-8")
        assert load_dev_gate(tmp_path) == []


# ─── check_perimeter ──────────────────────────────────────────────────────────


class TestCheckPerimeter:
    """Tests for ``check_perimeter`` — pure function, case-insensitive (CEO-265)."""

    def test_returns_empty_when_no_violations(self) -> None:
        assert check_perimeter("hello world", ["secret", "corp"]) == []

    def test_returns_violated_patterns(self) -> None:
        result = check_perimeter("this contains secret-corp in it", ["secret-corp", "other"])
        assert result == ["secret-corp"]

    def test_is_case_insensitive_lower_pattern(self) -> None:
        # Pattern lowercase, text mixed-case
        assert check_perimeter("Contains Zenzic-Brain here", ["zenzic-brain"]) == ["zenzic-brain"]

    def test_is_case_insensitive_upper_pattern(self) -> None:
        # Pattern mixed-case, text lowercase
        assert check_perimeter("contains zenzic-brain here", ["Zenzic-Brain"]) == ["Zenzic-Brain"]

    def test_returns_original_case_of_pattern(self) -> None:
        result = check_perimeter("found CORP-INTERNAL string", ["CORP-INTERNAL"])
        assert result == ["CORP-INTERNAL"]

    def test_empty_forbidden_returns_empty(self) -> None:
        assert check_perimeter("anything at all", []) == []

    def test_multiple_violations(self) -> None:
        result = check_perimeter("alpha and beta here", ["alpha", "beta", "gamma"])
        assert set(result) == {"alpha", "beta"}


# ─── check_sources_perimeter ──────────────────────────────────────────────────


class TestCheckSourcesPerimeter:
    """Tests for ``check_sources_perimeter`` — Phase B dual-spectrum gate (CEO-267)."""

    def _write_py(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_returns_empty_when_no_violations(self, tmp_path: Path) -> None:
        self._write_py(tmp_path / "mod.py", '"""Clean module."""\n\ndef run(): pass\n')
        result = check_sources_perimeter(tmp_path, ["secret-corp"])
        assert result == []

    def test_catches_hash_comment(self, tmp_path: Path) -> None:
        self._write_py(
            tmp_path / "mod.py", "# TODO: remove zenzic-brain reference\ndef run(): pass\n"
        )
        result = check_sources_perimeter(tmp_path, ["zenzic-brain"])
        assert any("zenzic-brain" in pat for _rel, pat in result)

    def test_catches_docstring_content(self, tmp_path: Path) -> None:
        self._write_py(
            tmp_path / "mod.py", '"""Module for zenzic-brain integration."""\ndef run(): pass\n'
        )
        result = check_sources_perimeter(tmp_path, ["zenzic-brain"])
        assert len(result) == 1
        assert result[0][1] == "zenzic-brain"

    def test_is_case_insensitive(self, tmp_path: Path) -> None:
        # Pattern lowercase, content mixed-case
        self._write_py(tmp_path / "mod.py", "# Zenzic-Brain reference here\ndef run(): pass\n")
        result = check_sources_perimeter(tmp_path, ["zenzic-brain"])
        assert len(result) == 1

    def test_returns_rel_path_not_absolute(self, tmp_path: Path) -> None:
        self._write_py(tmp_path / "sub" / "mod.py", "# secret-corp\ndef run(): pass\n")
        result = check_sources_perimeter(tmp_path, ["secret-corp"])
        assert len(result) == 1
        rel, pat = result[0]
        assert not rel.startswith("/")
        assert "sub" in rel

    def test_returns_empty_when_forbidden_empty(self, tmp_path: Path) -> None:
        self._write_py(tmp_path / "mod.py", "# anything here\ndef run(): pass\n")
        assert check_sources_perimeter(tmp_path, []) == []

    def test_multiple_files_multiple_violations(self, tmp_path: Path) -> None:
        self._write_py(tmp_path / "a.py", "# secret-corp\ndef a(): pass\n")
        self._write_py(tmp_path / "b.py", "# secret-corp and internal-host\ndef b(): pass\n")
        result = check_sources_perimeter(tmp_path, ["secret-corp", "internal-host"])
        rels = [r for r, _ in result]
        assert "a.py" in rels
        assert "b.py" in rels


# ─── render_json ──────────────────────────────────────────────────────────────


class TestRenderJson:
    """Tests for ``render_json`` — machine-readable AST export."""

    def _make_modules(self) -> list[ModuleInfo]:
        return [
            ModuleInfo(
                rel_path="core/shield.py",
                classes=["SecurityFinding"],
                public_functions=["scan_line_for_secrets"],
                docstring="Shield module.",
            )
        ]

    def test_returns_valid_json(self) -> None:
        output = render_json(self._make_modules())
        parsed = json.loads(output)
        assert isinstance(parsed, list)

    def test_contains_expected_keys(self) -> None:
        parsed = json.loads(render_json(self._make_modules()))
        assert parsed[0]["rel_path"] == "core/shield.py"
        assert parsed[0]["classes"] == ["SecurityFinding"]
        assert parsed[0]["public_functions"] == ["scan_line_for_secrets"]
        assert parsed[0]["docstring"] == "Shield module."

    def test_is_deterministic(self) -> None:
        mods = self._make_modules()
        assert render_json(mods) == render_json(mods)

    def test_empty_list_returns_empty_array(self) -> None:
        assert json.loads(render_json([])) == []


# ─── brain_map D002 dual-spectrum (CEO-267) ───────────────────────────────────


class TestBrainMapD002:
    """Integration tests for the D002 dual-spectrum gate via brain_map CLI."""

    def _make_src(self, base: Path, extra_content: str = "") -> Path:
        pkg = base / "src" / "mypkg"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "core.py").write_text(
            f'"""Core module."""\n\ndef run() -> None:\n    pass\n{extra_content}',
            encoding="utf-8",
        )
        return pkg

    def _write_dev_toml(self, base: Path, patterns: list[str]) -> None:
        lines = "[development_gate]\n"
        lines += "forbidden_patterns = [" + ", ".join(f'"{p}"' for p in patterns) + "]\n"
        (base / ".zenzic.dev.toml").write_text(lines, encoding="utf-8")

    def test_d002_silent_when_no_dev_toml(self, tmp_path: Path) -> None:
        from typer.testing import CliRunner

        from zenzic.cli._brain import brain_app

        self._make_src(tmp_path, extra_content="# secret-corp pattern here\n")
        runner = CliRunner()
        result = runner.invoke(brain_app, [str(tmp_path)])
        # No .zenzic.dev.toml → gate disabled → no D002
        assert "D002" not in result.output

    def test_d002_clean_when_no_violations(self, tmp_path: Path) -> None:
        from typer.testing import CliRunner

        from zenzic.cli._brain import brain_app

        self._make_src(tmp_path)
        self._write_dev_toml(tmp_path, ["totally-absent-pattern"])
        runner = CliRunner()
        result = runner.invoke(brain_app, [str(tmp_path)])
        assert result.exit_code == 0
        assert "D002" not in result.output

    def test_d002_phase_b_catches_hash_comment(self, tmp_path: Path) -> None:
        from typer.testing import CliRunner

        from zenzic.cli._brain import brain_app

        self._make_src(tmp_path, extra_content="# LEAK: secret-corp\n")
        self._write_dev_toml(tmp_path, ["secret-corp"])
        runner = CliRunner()
        result = runner.invoke(brain_app, [str(tmp_path)])
        assert result.exit_code == 1
        assert "D002" in result.output or "D002" in (result.stderr or "")
        assert "Phase B" in result.output or "Phase B" in (result.stderr or "")

    def test_d002_phase_a_catches_docstring(self, tmp_path: Path) -> None:
        from typer.testing import CliRunner

        from zenzic.cli._brain import brain_app

        # Pattern only in docstring (appears in AST → generated map)
        pkg = tmp_path / "src" / "mypkg"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "core.py").write_text(
            '"""secret-corp integration module."""\n\ndef run() -> None:\n    pass\n',
            encoding="utf-8",
        )
        self._write_dev_toml(tmp_path, ["secret-corp"])
        runner = CliRunner()
        result = runner.invoke(brain_app, [str(tmp_path)])
        assert result.exit_code == 1
        assert "D002" in result.output or "D002" in (result.stderr or "")


# ─── brain_map --format / --output (CEO-262) ──────────────────────────────────


class TestBrainMapFormat:
    """Tests for ``--format`` and ``--output`` flags on ``brain_map``."""

    def _make_src(self, base: Path) -> None:
        pkg = base / "src" / "mypkg"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "core.py").write_text(
            '"""Core module."""\n\ndef run() -> None:\n    pass\n', encoding="utf-8"
        )

    def test_format_json_stdout_is_valid_json(self, tmp_path: Path) -> None:
        from typer.testing import CliRunner

        from zenzic.cli._brain import brain_app

        self._make_src(tmp_path)
        runner = CliRunner()
        result = runner.invoke(brain_app, [str(tmp_path), "--format", "json"])
        assert result.exit_code == 0, result.output
        # The scanning prefix + trailing messages appear on stdout too.
        # Use raw_decode to parse just the JSON array, ignoring prefix/suffix.
        m = re.search(r"^\[\n", result.output, re.MULTILINE)
        assert m is not None, f"No JSON array found in output: {result.output!r}"
        parsed, _ = json.JSONDecoder().raw_decode(result.output, m.start())
        assert isinstance(parsed, list)

    def test_format_json_contains_rel_path_key(self, tmp_path: Path) -> None:
        from typer.testing import CliRunner

        from zenzic.cli._brain import brain_app

        self._make_src(tmp_path)
        runner = CliRunner()
        result = runner.invoke(brain_app, [str(tmp_path), "--format", "json"])
        assert result.exit_code == 0, result.output
        m = re.search(r"^\[\n", result.output, re.MULTILINE)
        assert m is not None
        parsed, _ = json.JSONDecoder().raw_decode(result.output, m.start())
        assert all("rel_path" in mod for mod in parsed)

    def test_output_flag_writes_markdown_file(self, tmp_path: Path) -> None:
        from typer.testing import CliRunner

        from zenzic.cli._brain import brain_app

        self._make_src(tmp_path)
        out_file = tmp_path / "cortex.md"
        runner = CliRunner()
        result = runner.invoke(brain_app, [str(tmp_path), "--output", str(out_file)])
        assert result.exit_code == 0, result.output
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        # The output file contains the raw markdown table (no MAP_START wrapper)
        assert "core.py" in content or "|" in content

    def test_output_flag_writes_json_file(self, tmp_path: Path) -> None:
        from typer.testing import CliRunner

        from zenzic.cli._brain import brain_app

        self._make_src(tmp_path)
        out_file = tmp_path / "cortex.json"
        runner = CliRunner()
        result = runner.invoke(
            brain_app, [str(tmp_path), "--format", "json", "--output", str(out_file)]
        )
        assert result.exit_code == 0, result.output
        assert out_file.exists()
        parsed = json.loads(out_file.read_text(encoding="utf-8"))
        assert isinstance(parsed, list)

    def test_check_with_format_json_emits_warning(self, tmp_path: Path) -> None:
        from typer.testing import CliRunner

        from zenzic.cli._brain import brain_app
        from zenzic.core.cartography import render_markdown_table, scan_python_sources

        self._make_src(tmp_path)
        src_root = tmp_path / "src" / "mypkg"
        modules = scan_python_sources(src_root)
        current_map = render_markdown_table(modules)
        ledger = tmp_path / "ZENZIC_BRAIN.md"
        ledger.write_text(
            f"# Header\n\n{MAP_START}\n{current_map}\n{MAP_END}\n\nFooter\n",
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(brain_app, [str(tmp_path), "--check", "--format", "json"])
        # WARNING emitted, but check still proceeds to pass
        assert "WARNING" in result.output or "ignored" in result.output
        assert result.exit_code == 0, result.output
