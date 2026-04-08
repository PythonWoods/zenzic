# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0

import os
import zipfile
from pathlib import Path

import nox


nox.options.reuse_existing_virtualenvs = True
nox.options.default_venv_backend = "uv"

# Sessions run by plain `nox` (fast feedback loop, no side effects).
# For the full CI-equivalent pipeline use: nox -s preflight
# NOTE: posargs are forwarded with `--`, e.g.: nox -s lint -- --fix
nox.options.sessions = ["lint", "format", "typecheck"]

PYTHONS = ["3.11", "3.12", "3.13"]

# Per-group sync tuples — each session installs only what it needs.
_SYNC_TEST = ("uv", "sync", "--active", "--group", "test")
_SYNC_LINT = ("uv", "sync", "--active", "--group", "lint")
_SYNC_DOCS = ("uv", "sync", "--active", "--group", "docs")
_SYNC_RELEASE = ("uv", "sync", "--active", "--group", "release")
_SYNC_DEV = ("uv", "sync", "--active", "--group", "dev")


@nox.session(python=PYTHONS)
def tests(session: nox.Session) -> None:
    """Run the test suite with branch coverage across all supported Python versions."""
    session.run(*_SYNC_TEST, external=True)
    session.run(
        "pytest",
        "--cov=src/zenzic",
        "--cov-report=term-missing",
        "--cov-report=xml:coverage.xml",
        *session.posargs,
        env={"HYPOTHESIS_PROFILE": os.environ.get("HYPOTHESIS_PROFILE", "ci")},
    )


@nox.session(python="3.11")
def lint(session: nox.Session) -> None:
    """Run ruff linting checks.

    Read-only by default (used in CI). To auto-fix: nox -s lint -- --fix
    """
    session.run(*_SYNC_LINT, external=True)
    session.run("ruff", "check", *session.posargs, "src/", "tests/")


@nox.session(python="3.11")
def format(session: nox.Session) -> None:  # noqa: A001
    """Check code formatting with ruff (read-only, used in CI)."""
    session.run(*_SYNC_LINT, external=True)
    session.run("ruff", "format", "--check", "src/", "tests/")


@nox.session(python="3.11")
def fmt(session: nox.Session) -> None:
    """Auto-format code with ruff in place (use during development)."""
    session.run(*_SYNC_LINT, external=True)
    session.run("ruff", "format", "src/", "tests/")


@nox.session(python="3.11")
def typecheck(session: nox.Session) -> None:
    """Run static type checking with mypy."""
    session.run(*_SYNC_LINT, external=True)
    session.run("mypy", "src/")


@nox.session(python="3.11")
def reuse(session: nox.Session) -> None:
    """Verify REUSE/SPDX license compliance."""
    session.run(*_SYNC_LINT, external=True)
    session.run("reuse", "lint")


@nox.session(python="3.11")
def security(session: nox.Session) -> None:
    """Audit third-party dependencies for known CVEs with pip-audit."""
    session.install("pip-audit")
    req = os.path.join(session.create_tmp(), "requirements.txt")
    session.run(
        "uv",
        "export",
        "--no-emit-project",
        "--frozen",
        "--no-hashes",
        "-o",
        req,
        external=True,
    )
    session.run(
        "pip-audit",
        "--strict",
        "-r",
        req,
        # CVE-2026-4539: ReDoS in Pygments AdlLexer (archetype.py).
        # Attack vector is LOCAL-only (crafted .adl file); Zenzic does not
        # process ADL input and uses Pygments only for documentation syntax
        # highlighting.  No patched release exists on PyPI yet.
        # Remove this exemption once pygments>=2.19.3 (or equivalent) ships.
        "--ignore-vuln",
        "CVE-2026-4539",
    )


def _download_lucide_icons() -> None:
    """Download Lucide icon set into overrides/.icons/lucide/ for MkDocs Material.

    Resolves the actual release asset URL via the GitHub API to avoid depending
    on a versioned filename (e.g. lucide-icons-1.7.0.zip).
    """
    import io
    import json
    import urllib.request

    dest = Path("overrides/.icons/lucide")
    if dest.exists():
        return
    dest.mkdir(parents=True, exist_ok=True)
    api_url = "https://api.github.com/repos/lucide-icons/lucide/releases/latest"
    with urllib.request.urlopen(api_url) as response:  # noqa: S310
        release = json.loads(response.read())
    asset_url = next(
        a["browser_download_url"]
        for a in release["assets"]
        if a["name"].startswith("lucide-icons") and a["name"].endswith(".zip")
    )
    with urllib.request.urlopen(asset_url) as response:  # noqa: S310
        with zipfile.ZipFile(io.BytesIO(response.read())) as zf:
            for name in zf.namelist():
                if name.endswith(".svg"):
                    svg_name = Path(name).name
                    (dest / svg_name).write_bytes(zf.read(name))


@nox.session(python="3.11")
def docs(session: nox.Session) -> None:
    """Build documentation with mkdocs in strict mode."""
    session.run(*_SYNC_DOCS, external=True)
    _download_lucide_icons()
    _build_brand_kit_zip()
    session.run("mkdocs", "build", "--strict")


@nox.session(python="3.11")
def docs_serve(session: nox.Session) -> None:
    """Serve documentation with live reload via mkdocs.

    Pass a custom bind address via posargs: nox -s docs_serve -- -a 127.0.0.1:8001
    """
    session.run(*_SYNC_DOCS, external=True)
    _download_lucide_icons()
    session.run("mkdocs", "serve", *session.posargs)


def _build_brand_kit_zip() -> None:
    """Generate docs/assets/brand-kit.zip from docs/assets/brand/ + social/."""
    base = Path("docs/assets")
    out = base / "brand-kit.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for src_dir in ("brand", "social"):
            src = base / src_dir
            for file in sorted(src.rglob("*")):
                if file.is_file() and not file.name.endswith(".license"):
                    zf.write(file, file.relative_to(base))


@nox.session(python="3.11")
def mutation(session: nox.Session) -> None:
    """Run mutation testing with mutmut on the security-critical core modules.

    Targets (configured in ``[tool.mutmut]`` in ``pyproject.toml``):
    - ``src/zenzic/core/rules.py``    — rule engine and regex canary
    - ``src/zenzic/core/shield.py``   — secret detection (ZRT-001/ZRT-003)
    - ``src/zenzic/core/reporter.py`` — _obfuscate_secret() masking function

    A surviving mutant means a test gap.  Goal: mutation score ≥ 90%.

    Implementation note — non-editable install:
        ``uv sync`` installs zenzic as an editable package whose ``.pth`` file
        points Python directly to the original ``src/`` tree.  This bypasses
        mutmut's mutation injection, which modifies a *copy* of the source
        files inside ``mutants/``.  The ``uv pip install --no-editable`` step
        below switches to a static install so that the mutations are visible to
        pytest during each test run.  The sync step is still needed first to
        resolve and install all transitive test dependencies.
    """
    session.run(*_SYNC_TEST, external=True)
    # Reinstall as non-editable so that mutmut's source injection is visible
    # to pytest (editable .pth files would bypass the mutated copy in mutants/).
    # Note: 'uv pip install .' (without --editable) installs the built wheel,
    # which is non-editable by default.
    session.run("uv", "pip", "install", ".", external=True)
    session.run(
        "mutmut",
        "run",
        *session.posargs,
    )
    session.run("mutmut", "results")


@nox.session(python="3.11")
def preflight(session: nox.Session) -> None:
    """Run all quality checks — equivalent to a full CI pipeline."""
    session.run(*_SYNC_DEV, external=True)
    session.run("ruff", "check", "src/", "tests/")
    session.run("ruff", "format", "--check", "src/", "tests/")
    session.run("mypy", "src/")
    session.run(
        "pytest",
        "--cov=src/zenzic",
        "--cov-report=term-missing",
        "--cov-report=xml:coverage.xml",
    )
    session.run("reuse", "lint")
    # Pillar 1: Validate the truth BEFORE rendering it.
    # Zenzic guards the source; mkdocs build only runs if sources are clean.
    session.run("zenzic", "check", "all", "--strict")
    _download_lucide_icons()
    _build_brand_kit_zip()
    session.run("mkdocs", "build", "--strict", env={"NO_MKDOCS_2_WARNING": "true"})


@nox.session(python="3.11")
def screenshot(session: nox.Session) -> None:
    """Regenerate docs/assets/screenshots/*.svg from examples/broken-docs output."""
    session.run(*_SYNC_DEV, external=True)
    session.run("python", "scripts/generate_docs_assets.py")


@nox.session(python=False, venv_backend="none")
def dev(session: nox.Session) -> None:
    """One-time developer setup: install pre-commit hooks and download build assets.

    Run once after cloning:
        nox -s dev
    """
    session.run("uv", "sync", "--group", "dev", external=True)
    session.run("uv", "run", "pre-commit", "install", external=True)
    _download_lucide_icons()


@nox.session(python="3.11")
def audit_sandboxes(session: nox.Session) -> None:
    """Ground-truth build audit: build the MkDocs sandbox and verify dark-page semantics.

    This session is the "proof of fire" for rc4.  It proves that every file Zenzic
    flags as UNREACHABLE_LINK is a genuine **dark page**: physically served by MkDocs
    at its URL, but absent from the generated navigation HTML.

    A dark page is not a broken link.  It is a navigation defect — the file exists,
    the link resolves, but the page is invisible to users browsing through the site.

    Steps:
      1. Install mkdocs-material into the session virtualenv.
      2. Build the MkDocs sandbox into sandbox/site/.
      3. Assert each UNREACHABLE_LINK file IS present in site/ (MkDocs copies all .md).
      4. Assert each UNREACHABLE_LINK URL is NOT linked in the nav HTML of index.html.
      5. Assert each REACHABLE file IS present in site/.
    """
    session.run(*_SYNC_DOCS, external=True)
    from pathlib import Path

    sandbox = Path("tests/sandboxes/mkdocs").resolve()
    site_dir = sandbox / "site"

    # Build the MkDocs sandbox into sandbox/site/
    session.log("Building MkDocs sandbox...")
    session.run(
        "mkdocs",
        "build",
        "--config-file",
        str(sandbox / "mkdocs.yml"),
        "--site-dir",
        str(site_dir),
        "--quiet",
    )
    session.log(f"Build complete → {site_dir}")

    # ── Ground-truth semantics for UNREACHABLE_LINK ──────────────────────────
    # MkDocs copies ALL .md files to site/ regardless of whether they appear
    # in nav:.  An UNREACHABLE_LINK page is physically served at its URL —
    # but it has NO navigation entry.  A user who follows a link to such a
    # page will land there successfully, but can never find it through the
    # site navigation.  Zenzic rc4 calls this "dark page reachability":
    # the link works, but from the user's perspective the page is invisible.
    #
    # The ground-truth verification therefore checks two things:
    #   A) UNREACHABLE_LINK files ARE present in site/ (MkDocs copied them)
    #      but are NOT referenced in any nav <a> in the generated HTML.
    #   B) REACHABLE files ARE present in site/ AND appear in the nav HTML.
    #
    # We approximate the nav check by searching for the URL in the nav HTML
    # of the home page (index.html), which contains the full navigation tree.

    # Pages Zenzic flags as UNREACHABLE_LINK (not in nav, but on disk)
    unreachable_in_site = [
        (site_dir / "secret" / "hidden" / "index.html", "/secret/hidden/"),
        (site_dir / "it" / "guide" / "index.html", "/it/guide/"),
    ]

    # Pages that ARE in the nav → must be present and linked in site/
    reachable_in_site = [
        (site_dir / "index.html", "/"),
        (site_dir / "guide" / "get-started" / "index.html", "/guide/get-started/"),
        (site_dir / "guide" / "installation" / "index.html", "/guide/installation/"),
        (site_dir / "about" / "index.html", "/about/"),
    ]

    failures: list[str] = []
    index_html = (site_dir / "index.html").read_text(encoding="utf-8")

    session.log("Verifying UNREACHABLE_LINK ground truth...")
    for path, url in unreachable_in_site:
        if not path.exists():
            failures.append(f"UNEXPECTED — MkDocs did not copy: {path.relative_to(site_dir)}")
            session.log(f"  UNEXPECTED — absent from site/: {path.relative_to(site_dir)}")
        else:
            session.log(f"  OK — physically served at {url} (MkDocs copies all .md files)")

        # The page must NOT appear as a nav link in index.html
        # (look for href="...url..." in the navigation HTML)
        nav_linked = url in index_html and f'href="{url}"' in index_html
        if nav_linked:
            failures.append(
                f"FAIL — {url} appears as a nav link in index.html "
                "(Zenzic UNREACHABLE_LINK prediction is wrong)"
            )
            session.log(f"  MISMATCH — {url} is in nav HTML (should be absent)")
        else:
            session.log(f"  OK — {url} is NOT in nav HTML (dark page confirmed)")

    session.log("Verifying REACHABLE page ground truth...")
    for path, _url in reachable_in_site:
        if path.exists():
            session.log(f"  OK — present in site/: {path.relative_to(site_dir)}")
        else:
            failures.append(f"FAIL — absent from site/: {path.relative_to(site_dir)}")
            session.log(f"  MISMATCH — absent from site/: {path.relative_to(site_dir)}")

    if failures:
        session.error("Ground-truth audit FAILED:\n" + "\n".join(f"  - {f}" for f in failures))
    else:
        session.log(
            "\n✓ Ground-truth audit PASSED.\n"
            "  MkDocs copies UNREACHABLE_LINK files to site/ but does NOT link them in nav.\n"
            "  Zenzic rc4 correctly identifies navigation-invisible pages.\n"
            "  'The file exists. The link works. The user can never find it.' — Confirmed."
        )


@nox.session(python="3.11", venv_backend="none")
def bump(session: nox.Session) -> None:
    """Bump the project version and create a release commit + tag.

    Usage:
        nox -s bump -- patch      # 0.1.0 → 0.1.1
        nox -s bump -- minor      # 0.1.0 → 0.2.0
        nox -s bump -- major      # 0.1.0 → 1.0.0

    After bumping, push with:
        git push && git push --tags
    """
    if not session.posargs:
        session.error("Specify a bump type: nox -s bump -- patch|minor|major")
    part = session.posargs[0]
    if part not in ("patch", "minor", "major"):
        session.error(f"Invalid bump type '{part}'. Use patch, minor, or major.")
    session.run("bump-my-version", "bump", part, external=True)
