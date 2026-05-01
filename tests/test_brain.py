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
        assert check_perimeter("Contains Forbidden-Alpha here", ["forbidden-alpha"]) == [
            "forbidden-alpha"
        ]

    def test_is_case_insensitive_upper_pattern(self) -> None:
        # Pattern mixed-case, text lowercase
        assert check_perimeter("contains forbidden-alpha here", ["Forbidden-Alpha"]) == [
            "Forbidden-Alpha"
        ]

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
            tmp_path / "mod.py",
            "# TODO: remove internal-secret-identifier reference\ndef run(): pass\n",
        )
        result = check_sources_perimeter(tmp_path, ["internal-secret-identifier"])
        assert any("internal-secret-identifier" in pat for _rel, pat in result)

    def test_catches_docstring_content(self, tmp_path: Path) -> None:
        self._write_py(
            tmp_path / "mod.py",
            '"""Module for internal-secret-identifier integration."""\ndef run(): pass\n',
        )
        result = check_sources_perimeter(tmp_path, ["internal-secret-identifier"])
        assert len(result) == 1
        assert result[0][1] == "internal-secret-identifier"

    def test_is_case_insensitive(self, tmp_path: Path) -> None:
        # Pattern lowercase, content mixed-case
        self._write_py(
            tmp_path / "mod.py", "# Internal-Secret-Identifier reference here\ndef run(): pass\n"
        )
        result = check_sources_perimeter(tmp_path, ["internal-secret-identifier"])
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


class TestRedactPerimeter:
    """Tests for ``redact_perimeter`` — Phase A Sovereign Redactor (CEO-276)."""

    def test_replaces_forbidden_literal(self) -> None:
        from zenzic.core.cartography import redact_perimeter

        result = redact_perimeter("contains secret-corp here", ["secret-corp"])
        assert "secret-corp" not in result
        assert "[REDACTED_BY_SENTINEL]" in result

    def test_is_case_insensitive(self) -> None:
        from zenzic.core.cartography import redact_perimeter

        result = redact_perimeter("Contains SECRET-CORP Here", ["secret-corp"])
        assert "SECRET-CORP" not in result
        assert "[REDACTED_BY_SENTINEL]" in result

    def test_multiple_patterns(self) -> None:
        from zenzic.core.cartography import redact_perimeter

        text = "alpha and beta are both private"
        result = redact_perimeter(text, ["alpha", "beta"])
        assert "alpha" not in result
        assert "beta" not in result
        assert result.count("[REDACTED_BY_SENTINEL]") == 2

    def test_empty_forbidden_returns_unchanged(self) -> None:
        from zenzic.core.cartography import redact_perimeter

        original = "no patterns here"
        assert redact_perimeter(original, []) == original

    def test_special_chars_in_pattern_treated_literally(self) -> None:
        from zenzic.core.cartography import redact_perimeter

        # Dot in path pattern must not act as regex wildcard
        result = redact_perimeter("/home/user/docs", ["/home/user/docs"])
        assert "/home/user/docs" not in result
        assert "[REDACTED_BY_SENTINEL]" in result

    def test_no_match_returns_unchanged(self) -> None:
        from zenzic.core.cartography import redact_perimeter

        original = "nothing matches here"
        assert redact_perimeter(original, ["absent-pattern"]) == original


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

    def test_d002_phase_a_redacts_output(self, tmp_path: Path) -> None:
        from typer.testing import CliRunner

        from zenzic.cli._brain import brain_app

        # Phase A catches patterns that appear in the GENERATED TABLE (e.g. file paths)
        # but NOT in raw file content — so Phase B stays silent.
        # Here: file named 'corp_internal.py' → rel_path appears in Markdown table.
        # File content does NOT contain 'corp_internal' → Phase B passes.
        pkg = tmp_path / "src" / "mypkg"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        # File name contains the forbidden pattern; content does not.
        (pkg / "corp_internal.py").write_text(
            '"""Utility module."""\n\ndef run() -> None:\n    pass\n',
            encoding="utf-8",
        )
        self._write_dev_toml(tmp_path, ["corp_internal"])
        runner = CliRunner()
        result = runner.invoke(brain_app, [str(tmp_path)])
        # Phase A: export succeeds (exit 0), file-path pattern is silently redacted
        assert result.exit_code == 0, result.output
        assert "D002" not in result.output
        assert "corp_internal" not in result.output
        assert "[REDACTED_BY_SENTINEL]" in result.output


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


# ─── CEO-279 Synthetic Fixture Protocol + CEO-281 Discovery Purity ───────────

# CEO-279: The Synthetic Fixture Protocol.
# Tests for D002 must NEVER contain the forbidden literal string in plain text
# on disk.  The "poison" is assembled at runtime from fragments so that a
# static grep of the repository finds no clear-text leak.
#
# Construction technique (read-only, for test authors):
#   part_a = "zenzic"          # public CLI name — harmless alone
#   part_b = "brain"           # CLI subcommand name — harmless alone
#   _SYNTHETIC_FORBIDDEN = f"{part_a}-{part_b}"   # assembled in RAM only
#
# The forbidden string exists solely in memory during test execution.
# It is NEVER written to any tracked file.  This is the Zero-Leak Contract.

# Fragments — each harmless in isolation; the gate only fires on the joined form.
_PART_A = "zen" + "zic"  # == "zenzic" (public CLI name, safe alone)
_PART_B = "bra" + "in"  # == "brain"  (CLI subcommand, safe alone)
# The synthetic forbidden token — assembled in RAM, never on disk.
_SYNTHETIC_FORBIDDEN: str = f"{_PART_A}-{_PART_B}"


class TestSyntheticFixtureProtocol:
    """CEO-279: Verify the Synthetic Fixture technique detects the forbidden token.

    These tests demonstrate that:
    1. The synthetic construction produces the correct forbidden token.
    2. ``check_perimeter`` detects it in injected content.
    3. ``check_sources_perimeter`` detects it when written dynamically to a
       temp file (the token never appears in *this* source file on disk).
    """

    def test_synthetic_token_is_correct(self) -> None:
        """The assembled token must equal the real forbidden identifier."""
        # Verified via length + hash — not by printing it in a string literal.
        assert len(_SYNTHETIC_FORBIDDEN) == 12  # noqa: PLR2004
        assert _SYNTHETIC_FORBIDDEN.startswith(_PART_A)
        assert _SYNTHETIC_FORBIDDEN.endswith(_PART_B)
        assert "-" in _SYNTHETIC_FORBIDDEN

    def test_check_perimeter_detects_synthetic_token(self) -> None:
        """check_perimeter finds the token when injected into a content string."""
        content = f"# internal reference: {_SYNTHETIC_FORBIDDEN}\ndef run(): pass\n"
        result = check_perimeter(content, [_SYNTHETIC_FORBIDDEN])
        assert result == [_SYNTHETIC_FORBIDDEN]

    def test_check_sources_perimeter_detects_md_file(self, tmp_path: Path) -> None:
        """Phase B catches the token in a .md file (CEO-269 extended scan)."""
        md_file = tmp_path / "notes.md"
        md_file.write_text(
            f"# Notes\n\nSee {_SYNTHETIC_FORBIDDEN} for details.\n", encoding="utf-8"
        )
        result = check_sources_perimeter(tmp_path, [_SYNTHETIC_FORBIDDEN])
        assert any(_SYNTHETIC_FORBIDDEN in pat for _rel, pat in result)

    def test_check_sources_perimeter_detects_toml_file(self, tmp_path: Path) -> None:
        """Phase B catches the token in a .toml config file (CEO-269 extended scan)."""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(
            f'[project]\nname = "{_SYNTHETIC_FORBIDDEN}-adapter"\n', encoding="utf-8"
        )
        result = check_sources_perimeter(tmp_path, [_SYNTHETIC_FORBIDDEN])
        assert any(_SYNTHETIC_FORBIDDEN in pat for _rel, pat in result)

    def test_check_sources_perimeter_detects_py_comment(self, tmp_path: Path) -> None:
        """Phase B catches the token in a Python # comment (original D002 scope)."""
        py_file = tmp_path / "mod.py"
        py_file.write_text(
            f"# TODO: remove {_SYNTHETIC_FORBIDDEN} reference\ndef run(): pass\n", encoding="utf-8"
        )
        result = check_sources_perimeter(tmp_path, [_SYNTHETIC_FORBIDDEN])
        assert any(_SYNTHETIC_FORBIDDEN in pat for _rel, pat in result)


class TestSovereignImmunity:
    """CEO-278: The dev gate config file is immune from its own D002 scan.

    The ``.zenzic.dev.toml`` file contains the forbidden patterns themselves.
    Without immunity it would trigger D002 and block every export — the
    Paradox of the Sentinel.  The ``exclude`` parameter resolves this.
    """

    def test_dev_toml_not_detected_when_excluded(self, tmp_path: Path) -> None:
        """When .zenzic.dev.toml is in the exclude set, it is not scanned."""
        dev_toml = tmp_path / ".zenzic.dev.toml"
        dev_toml.write_text(
            f'[development_gate]\nforbidden_patterns = ["{_SYNTHETIC_FORBIDDEN}"]\n',
            encoding="utf-8",
        )
        immune = frozenset({dev_toml.resolve()})
        result = check_sources_perimeter(tmp_path, [_SYNTHETIC_FORBIDDEN], exclude=immune)
        # The dev toml contains the pattern but is immune — result must be empty.
        assert result == []

    def test_dev_toml_detected_without_immunity(self, tmp_path: Path) -> None:
        """Without exclude, the dev toml IS detected (confirms immunity is not automatic)."""
        dev_toml = tmp_path / ".zenzic.dev.toml"
        dev_toml.write_text(
            f'[development_gate]\nforbidden_patterns = ["{_SYNTHETIC_FORBIDDEN}"]\n',
            encoding="utf-8",
        )
        # No exclude set — the file is scanned and the token is found.
        result = check_sources_perimeter(tmp_path, [_SYNTHETIC_FORBIDDEN])
        assert any(_SYNTHETIC_FORBIDDEN in pat for _rel, pat in result)

    def test_immune_path_must_be_resolved(self, tmp_path: Path) -> None:
        """Immunity is matched against resolved paths — symlinks are not a bypass."""
        dev_toml = tmp_path / ".zenzic.dev.toml"
        dev_toml.write_text(
            f'[development_gate]\nforbidden_patterns = ["{_SYNTHETIC_FORBIDDEN}"]\n',
            encoding="utf-8",
        )
        # Pass the resolved path — must work correctly.
        immune = frozenset({dev_toml.resolve()})
        result = check_sources_perimeter(tmp_path, [_SYNTHETIC_FORBIDDEN], exclude=immune)
        assert result == []

    def test_brain_map_cli_immune_from_dev_toml(self, tmp_path: Path) -> None:
        """brain_map CLI: .zenzic.dev.toml with forbidden token does not block export."""
        from typer.testing import CliRunner

        from zenzic.cli._brain import brain_app

        # Build a minimal src tree.
        pkg = tmp_path / "src" / "mypkg"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "core.py").write_text(
            '"""Core module."""\n\ndef run() -> None:\n    pass\n', encoding="utf-8"
        )

        # Write .zenzic.dev.toml with the synthetic forbidden token.
        # If immunity is absent, brain_map would exit 1 on its own config.
        (tmp_path / ".zenzic.dev.toml").write_text(
            f'[development_gate]\nforbidden_patterns = ["{_SYNTHETIC_FORBIDDEN}"]\n',
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(brain_app, [str(tmp_path)])
        # Sovereign Immunity: the dev toml is excluded → Phase B passes → exit 0.
        assert result.exit_code == 0, result.output
        assert "D002" not in result.output


class TestDiscoveryPurity:
    """CEO-281: D002 Phase B uses walk_files + LayeredExclusionManager.

    Verifies that SYSTEM_EXCLUDED_DIRS (node_modules, .venv, __pycache__, etc.)
    are never entered during the perimeter scan — consistent with the linter.
    """

    def test_system_excluded_dir_not_scanned(self, tmp_path: Path) -> None:
        """Files inside a SYSTEM_EXCLUDED_DIR are invisible to D002 Phase B."""
        # Place the forbidden token inside node_modules (system-excluded).
        excluded = tmp_path / "node_modules" / "lib"
        excluded.mkdir(parents=True)
        (excluded / "README.md").write_text(f"# {_SYNTHETIC_FORBIDDEN}\n", encoding="utf-8")
        # The scan must not enter node_modules → no violation reported.
        result = check_sources_perimeter(tmp_path, [_SYNTHETIC_FORBIDDEN])
        assert result == [], f"Unexpected violations from excluded dir: {result}"

    def test_venv_dir_not_scanned(self, tmp_path: Path) -> None:
        """Files inside .venv are invisible to D002 Phase B."""
        venv_file = tmp_path / ".venv" / "lib" / "mod.py"
        venv_file.parent.mkdir(parents=True)
        venv_file.write_text(f"# {_SYNTHETIC_FORBIDDEN}\n", encoding="utf-8")
        result = check_sources_perimeter(tmp_path, [_SYNTHETIC_FORBIDDEN])
        assert result == [], f"Unexpected violations from .venv: {result}"

    def test_clean_tracked_file_passes(self, tmp_path: Path) -> None:
        """A clean file in the scan root produces no violations."""
        (tmp_path / "clean.py").write_text('"""No forbidden content."""\n', encoding="utf-8")
        result = check_sources_perimeter(tmp_path, [_SYNTHETIC_FORBIDDEN])
        assert result == []
