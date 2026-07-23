# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Nox automation for zenzic-action — the official GitHub Action.

Sovereign verification model (shared across zenzic family repositories):
    - Explicit override: ZENZIC_CORE_PATH
    - CI topology: ./_zenzic_core
    - Dev topology: ../zenzic
    - Fail-closed policy: PyPI fallback is prohibited for repository gates

Quick reference:
    nox -s reuse       — REUSE/SPDX licence compliance
    nox -s check       — Run Zenzic quality gate on action documentation
    nox -s preflight   — Full CI-equivalent pipeline (reuse + check)
"""

import os
from pathlib import Path

import nox

nox.options.reuse_existing_virtualenvs = True

# Default sessions for fast feedback
nox.options.sessions = ["reuse", "check"]


def _normalize_candidate(root: Path, raw_path: str) -> Path:
    """Resolve candidate paths relative to repository root when needed."""
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = (root / candidate).resolve()
    else:
        candidate = candidate.resolve()
    return candidate


def _display_path(root: Path, path: Path) -> str:
    """Render stable display path for session logs."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _resolve_core_path(root: Path, session: nox.Session) -> Path:
    """Resolve local Zenzic core path using sovereign precedence and fail-closed policy."""
    candidates: list[tuple[str, str]] = []

    env_override = os.environ.get("ZENZIC_CORE_PATH")
    if env_override:
        candidates.append(("ZENZIC_CORE_PATH", env_override))

    candidates.extend(
        [
            ("_zenzic_core", "_zenzic_core"),
            ("../zenzic", "../zenzic"),
        ]
    )

    checked: list[str] = []
    for label, raw in candidates:
        candidate = _normalize_candidate(root, raw)
        checked.append(f"{label} -> {_display_path(root, candidate)}")
        if (candidate / "src" / "zenzic").is_dir():
            session.log(
                f"[Zenzic] Local core found at '{_display_path(root, candidate)}' "
                "— using local source metadata."
            )
            return candidate

    session.error(
        "[Zenzic] Core repository not found in sovereign search order.\n"
        "Required precedence: ZENZIC_CORE_PATH -> ./_zenzic_core -> ../zenzic\n"
        "Each candidate must contain src/zenzic.\n"
        f"Checked: {checked}\n"
        "Fail-closed policy active: PyPI fallback is prohibited."
    )
    raise RuntimeError("unreachable")


def _run_zenzic_check(session: nox.Session) -> None:
    """Run Zenzic check using shared sovereign path resolution (fail-closed)."""
    root = Path(__file__).parent
    core_path = _resolve_core_path(root, session)
    session.run(
        "uv",
        "run",
        "--project",
        str(core_path),
        "zenzic",
        "check",
        "all",
        "--strict",
        external=True,
    )


@nox.session(venv_backend="none")
def reuse(session: nox.Session) -> None:
    """Verify REUSE/SPDX licence compliance."""
    session.run("uvx", "reuse", "lint", external=True)


@nox.session(venv_backend="none")
def check(session: nox.Session) -> None:
    """Run the Zenzic quality gate on action documentation."""
    _run_zenzic_check(session)


@nox.session(venv_backend="none")
def tests(session: nox.Session) -> None:
    """Run action smoke tests and shell validation."""
    session.run("bash", "-n", "zenzic-action-wrapper.sh", external=True)
    _run_zenzic_check(session)


@nox.session(venv_backend="none")
def preflight(session: nox.Session) -> None:
    """Full CI-equivalent pipeline: reuse → check."""
    session.run("uvx", "reuse", "lint", external=True)
    _run_zenzic_check(session)
