---
icon: lucide/play
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Usage

Zenzic reads directly from the filesystem and works with any project, including those that do not
use MkDocs as their build driver. Use it in local development, as a pre-commit hook, in CI
pipelines, or for one-off audits.

!!! tip "Just want to run it now?"

    ```bash
    uvx zenzic check all
    ```

    No installation required. `uvx` downloads and runs Zenzic in a throwaway environment.

---

## Init → Config → Check workflow

The standard workflow for adopting Zenzic in a project:

### 1. Init — scaffold a configuration file

Bootstrap a `zenzic.toml` with a single command. Zenzic auto-detects the documentation engine and
pre-populates `[build_context]` accordingly:

```bash
zenzic init
```

**Example output when `mkdocs.yml` is present:**

```text
Created zenzic.toml
  Engine pre-set to mkdocs (detected from mkdocs.yml).

Edit the file to enable rules, adjust directories, or set a quality threshold.
Run zenzic check all to validate your documentation.
```

If no engine config file is found, `zenzic init` produces an engine-agnostic scaffold (Vanilla
mode). In either case, all settings are commented out by default — uncomment and adjust only the
fields you need.

Run Zenzic without a `zenzic.toml` and it falls back to built-in defaults, printing a Helpful
Hint panel that suggests `zenzic init`:

```text
╭─ 💡 Zenzic Tip ─────────────────────────────────────────────────────╮
│ Using built-in defaults — no zenzic.toml found.                      │
│ Run zenzic init to create a project configuration file.              │
│ Customise docs directory, excluded paths, engine adapter, and rules. │
╰──────────────────────────────────────────────────────────────────────╯
```

### 2. Config — tune to your project

Edit the generated `zenzic.toml` to suppress noise and set thresholds appropriate to your project:

```toml
# zenzic.toml — place at the repository root
excluded_assets = [
    "assets/favicon.svg",      # referenced by mkdocs.yml, not by any .md page
    "assets/social-preview.png",
]
placeholder_max_words = 30     # technical reference pages are intentionally brief
fail_under = 70                # establish an initial quality floor
```

See the [Configuration Reference](../configuration/index.md) for the full field list.

### 3. Check — run continuously

With the baseline established, run Zenzic on every commit and pull request:

```bash
# Pre-commit hook or CI step
zenzic check all --strict

# Save a quality baseline on main
zenzic score --save

# Block PRs that regress the baseline
zenzic diff --threshold 5
```

---

## Vanilla mode vs engine-aware mode

Zenzic operates in one of two modes depending on whether it can discover a build-engine
configuration file:

### Engine-aware mode

When `mkdocs.yml` (MkDocs/Zensical) or `zensical.toml` (Zensical) is present at the repository
root, Zenzic loads the corresponding **adapter** which provides:

- **Nav awareness** — the full navigation tree is known, so orphan detection can tell the
  difference between "this file is not in the nav" and "this file is not supposed to be in the
  nav" (e.g. i18n locale files).
- **i18n fallback** — cross-locale links are resolved correctly instead of being flagged as
  broken.
- **Locale directory suppression** — files under `docs/it/`, `docs/fr/`, etc. are not reported
  as orphans.

This is the mode used by the vast majority of Zenzic users.

### Vanilla mode

When no build-engine configuration is found — or when an unknown engine name is specified — Zenzic
falls back to `VanillaAdapter`. In this mode:

- **Orphan check is skipped.** Without a nav declaration, every Markdown file would appear to be
  an orphan, which would produce useless noise rather than actionable findings.
- **All other checks run normally** — links, snippets, placeholders, assets, and references are
  all validated as usual.

Vanilla mode is the right choice for plain Markdown wikis, GitHub-wiki repos, or any project
where navigation is implicit rather than declared.

!!! tip "Force a specific mode"
    Use `--engine` to override the detected adapter for a single run:

    ```bash
    zenzic check all --engine vanilla    # skip orphan check regardless of config files
    zenzic check all --engine mkdocs     # force MkDocs adapter
    ```

---

## Installation options

### Ephemeral — no installation required

=== ":simple-astral: uv"

    ```bash
    uvx zenzic check all
    ```

    `uvx` resolves and runs Zenzic from PyPI in a throwaway environment. Nothing is installed on
    your system. This is the right choice for one-off audits, `git hooks`, and CI jobs where you
    want to avoid pinning a dev dependency.

=== ":simple-pypi: pip"

    ```bash
    pip install zenzic
    zenzic check all
    ```

    Standard installation into the active environment. Use inside a virtual environment to keep
    your system Python clean.

### Global tool — available in every project

=== ":simple-astral: uv"

    ```bash
    uv tool install zenzic
    zenzic check all
    ```

    Install once, use in any project. The binary is available on your `PATH` without activating
    a virtual environment. Suitable for developers who work across multiple documentation projects
    and want a consistent global tool.

=== ":simple-pypi: pip"

    ```bash
    python -m venv ~/.local/zenzic-env
    source ~/.local/zenzic-env/bin/activate   # Windows: .venv\Scripts\activate
    pip install zenzic
    ```

    Install into a dedicated virtual environment, then add the `bin/` directory to your `PATH`.

### Project dev dependency — version pinned per project

=== ":simple-astral: uv"

    ```bash
    uv add --dev zenzic
    uv run zenzic check all
    ```

    Installs Zenzic into the project's virtual environment and pins the version in `uv.lock`.
    This is the right choice for team projects where everyone must use the same version, and for
    CI pipelines that install project dependencies before running checks.

=== ":simple-pypi: pip"

    ```bash
    python -m venv .venv
    source .venv/bin/activate   # Windows: .venv\Scripts\activate
    pip install zenzic
    zenzic check all
    ```

    Standard dev-dependency pattern with a project-local virtual environment.

### Commands

```bash
# Individual checks
zenzic check links        # Internal links; add --strict for external HTTP validation
zenzic check orphans      # Pages on disk missing from nav
zenzic check snippets     # Python code blocks that fail to compile
zenzic check placeholders # Stub pages: low word count or forbidden patterns
zenzic check assets       # Media files not referenced by any page

# Autofix & Cleanup
zenzic clean assets       # Delete unused assets interactively
zenzic clean assets -y    # Delete unused assets immediately
zenzic clean assets --dry-run # Preview what would be deleted

# Reference pipeline (v0.2.0)
zenzic check references              # Harvest → Cross-Check → Shield → Integrity score
zenzic check references --strict     # Treat Dead Definitions as errors
zenzic check references --links      # Also validate reference URLs via async HTTP

# All checks in sequence
zenzic check all                    # Run all six checks
zenzic check all --strict           # Treat warnings as errors
zenzic check all --format json      # Machine-readable output for downstream processing
zenzic check all --exit-zero        # Report issues but always exit 0

# Quality score
zenzic score                        # Compute 0–100 quality score
zenzic score --save                 # Compute and persist snapshot to .zenzic-score.json
zenzic score --fail-under 80        # Exit 1 if score is below threshold
zenzic score --format json          # Machine-readable score report

# Regression detection
zenzic diff                         # Compare current score against saved snapshot
zenzic diff --threshold 5           # Exit 1 only if score dropped by more than 5 points
zenzic diff --format json           # Machine-readable diff report
```

### Autofix & Cleanup

Instead of just reporting issues, Zenzic can actively clean your repository. `zenzic clean assets` reads your documentation, finds all unused files in `docs_dir` (respecting `excluded_assets`, `excluded_dirs`, and `excluded_build_artifacts`), and prompts you to safely delete them. Use `--dry-run` to preview changes safely or `-y` to automate deletion in CI pipelines.

### Development server

```bash
# Start dev server with pre-flight quality check
zenzic serve

# Force a specific engine
zenzic serve --engine mkdocs
zenzic serve --engine zensical

# Custom port (scans up to 10 consecutive ports if busy)
zenzic serve --port 9000
zenzic serve -p 9000

# Skip pre-flight and jump straight to the server
zenzic serve --no-preflight
```

`zenzic serve` auto-detects the documentation engine from the repository root:

| Config file present | Engine binary available | Result |
| :--- | :--- | :--- |
| `zensical.toml` | `zensical` or `mkdocs` | Starts available engine |
| `zensical.toml` | neither | Error — install an engine |
| `mkdocs.yml` only | `mkdocs` or `zensical` | Starts available engine |
| `mkdocs.yml` only | neither | Error — install an engine |
| neither | any | Static file server on `site/` (no hot-reload) |

`zensical.toml` always takes priority because Zensical is a superset of MkDocs and reads
`mkdocs.yml` natively. The static fallback lets `zenzic serve` work in any environment — even
without mkdocs or zensical installed — as long as a pre-built `site/` directory exists.

When `--engine` is specified explicitly, Zenzic validates both that the binary is on `$PATH` and
that the required config file exists. `--engine zensical` accepts `mkdocs.yml` as a valid config
for backwards compatibility.

**Port handling.** Zenzic resolves a free port via socket probing *before* launching the engine
subprocess, then passes `--dev-addr 127.0.0.1:{port}` to mkdocs or zensical. This means the
`Address already in use` error can never appear from the engine; if the requested port (default
`8000`) is busy, Zenzic silently tries the next port up to ten times and reports which port is
actually used.

Before launching the server, Zenzic runs a silent pre-flight check — orphans, snippets,
placeholders, and unused assets. Issues are printed as warnings but never block startup; the intent
is to make them visible while you iterate. External link validation (`check links --strict`) is
intentionally excluded from the pre-flight: there is no value in waiting for network roundtrips
when you are about to fix the documentation live.

The server process inherits your terminal so hot-reload logs and request output appear unfiltered.
Use `--no-preflight` to skip the quality check entirely when you are mid-fix and do not need the
noise.

### Exit codes

| Code | Meaning |
| :---: | :--- |
| `0` | All selected checks passed (or `--exit-zero` was set) |
| `1` | One or more checks reported issues |
| **`2`** | **SECURITY CRITICAL — Zenzic Shield detected a leaked credential** |

!!! danger "Exit code 2 is reserved for security events"
    Exit code 2 is issued exclusively by `zenzic check references` when the Shield detects a
    known credential pattern embedded in a reference URL. It is never used for ordinary check
    failures. If you receive exit code 2, treat it as a build-blocking security incident and
    **rotate the exposed credential immediately**.

### JSON output

Pass `--format json` to `check all` for structured output suitable for downstream processing,
dashboards, or custom reporting tools:

```bash
zenzic check all --format json | jq '.orphans'
zenzic check all --format json > report.json
```

The JSON report contains keys matching each check name: `links`, `orphans`, `snippets`,
`placeholders`, `unused_assets`, `references`. Each key holds a list of issue strings or objects.
An empty list means the check passed.

### Overriding the adapter engine

The `--engine` flag overrides the build engine adapter for a single run without modifying
`zenzic.toml`. It is accepted by `check orphans` and `check all`:

```bash
# Force the MkDocs adapter even if zenzic.toml says otherwise
zenzic check orphans --engine mkdocs
zenzic check all --engine mkdocs

# Use the Zensical adapter (requires zensical.toml to be present)
zenzic check orphans --engine zensical
zenzic check all --engine zensical
```

If you pass an engine name that has no registered adapter, Zenzic lists the available adapters
and exits with code 1:

```text
ERROR: Unknown engine adapter 'hugo'.
Installed adapters: mkdocs, vanilla, zensical
Install a third-party adapter or choose from the list above.
```

Third-party adapters (e.g. `zenzic-hugo-adapter`) are discovered automatically once installed —
no Zenzic update required. See [Writing an Adapter](../developers/writing-an-adapter.md).

---

### Quality scoring

Individual checks answer a binary question: pass or fail. `zenzic score` answers a different one:
*how healthy is this documentation, and is it getting better or worse over time?*

`zenzic score` runs all checks and aggregates their results into a single integer between 0 and
100. The score is deterministic — given the same documentation state, it always produces the same
number — which makes it safe to track in version control and compare across branches.

### How the score is computed

Each check category carries a fixed weight that reflects its impact on the reader experience:

| Category | Weight | Rationale |
| :--- | ---: | :--- |
| links | 35 % | A broken link is an immediate dead end for the reader |
| orphans | 20 % | Unreachable pages are invisible — they might as well not exist |
| snippets | 20 % | Invalid code examples actively mislead developers |
| placeholders | 15 % | Stub content signals an unfinished or abandoned page |
| assets | 10 % | Unused assets are waste, but they do not block the reader |

Within each category, the score decays linearly: the first issue costs 20 points out of 100 for
that category, the second costs another 20, and so on, floored at zero. A category with five or
more issues contributes nothing to the total. The weighted contributions are summed and rounded
to an integer.

This means a single broken link drops the total score by roughly 7 points (35 % weight × 20 %
decay), while a single unused asset costs about 2 points. The weights encode an intentional
judgement about severity.

### Tracking regressions in CI

The score becomes most useful when compared against a known baseline. The `--save` flag writes the
current report to `.zenzic-score.json` at the repository root. Once a baseline exists,
`zenzic diff` computes the delta and exits non-zero if the documentation has regressed.

A typical CI setup on a team project:

```bash
# Establish or refresh the baseline on the main branch
zenzic score --save

# On every pull request, block merges that degrade documentation quality
zenzic diff --threshold 5
```

`--threshold 5` gives contributors a five-point margin — small, unrelated changes (a new stub
page, a temporary TODO comment) do not block a PR. Set it to `0` for a strict gate where any
regression fails the pipeline.

### Enforcing a minimum score

Use `--fail-under` when you want an absolute floor rather than a relative check:

```bash
zenzic score --fail-under 80
```

This is useful for documentation-as-a-feature policies where the team has committed to maintaining
a defined quality level, regardless of what the score was last week.

### Soft reporting

To surface the score without blocking the pipeline — useful during an active documentation
improvement sprint — combine `check all --exit-zero` with `score` in separate steps:

```bash
zenzic check all --exit-zero   # full report, exit 0 regardless
zenzic score                   # show score for visibility
```

---

## Reference integrity (v0.2.0)

`zenzic check references` is the most thorough check in the suite. Unlike the other checks, which
operate on individual pages in isolation, the reference pipeline builds a **global view** of all
Markdown reference link definitions across your entire documentation before validating any usage.

### Why two passes?

A single-pass scanner would produce false positives for *forward references* — cases where
`[text][id]` appears on a page before `[id]: url` is defined later in the same file. The
[Two-Pass Pipeline][arch-two-pass] solves this cleanly:

- **Pass 1 — Harvest**: reads every file, collects all `[id]: url` definitions into a
  per-file [ReferenceMap][arch-refmap], and runs the Zenzic Shield on every URL.
- **Pass 2 — Cross-Check**: resolves every `[text][id]` usage against the fully-populated
  ReferenceMap and reports any Dangling References.
- **Pass 3 — Integrity**: computes the per-file integrity score from the resolved usage data.

!!! warning "Do not merge the passes"
    Merging harvesting and cross-check into a single loop produces false *Phantom Reference* errors
    on forward references — a common pattern in large documentation projects. The two-pass
    separation is not an optimisation; it is a correctness requirement.

### Commands

```bash
zenzic check references              # Full pipeline: Harvest → Cross-Check → Shield → score
zenzic check references --strict     # Treat Dead Definitions (defined but never used) as errors
zenzic check references --links      # Also validate reference URLs via async HTTP (1 ping/URL)
```

`--links` triggers [global URL deduplication][arch-dedup]: every unique URL across all files is
pinged exactly once, regardless of how many definitions reference it.

### Zenzic Shield

!!! danger "Security — Exit Code 2"
    If `zenzic check references` exits with code **2**, a secret was found embedded in a reference
    URL inside your documentation. **Rotate the exposed credential immediately.**

The Shield scans every reference URL for known credential patterns during Pass 1 — before Pass 2
validates links, and before `--links` issues any HTTP request. A document containing a leaked
credential is never used to make outbound requests.

| Credential type | Pattern |
| :--- | :--- |
| OpenAI API key | `sk-[a-zA-Z0-9]{48}` |
| GitHub token | `gh[pousr]_[a-zA-Z0-9]{36}` |
| AWS access key | `AKIA[0-9A-Z]{16}` |

Patterns use exact-length quantifiers — no backtracking, O(1) per line regardless of line length.

When the Shield fires, Zenzic emits a SECURITY CRITICAL banner and exits immediately with code 2:

```text
╔══════════════════════════════════════╗
║        SECURITY CRITICAL             ║
║  Secret(s) detected in documentation ║
╚══════════════════════════════════════╝

  [SHIELD] docs/api.md:12 — openai-api-key detected in URL
    https://api.example.com/?key=sk-AbCdEfGhIj...

Build aborted. Rotate the exposed credential immediately.
```

!!! tip "Pre-commit integration"
    Add `zenzic check references` to your [pre-commit hooks][pre-commit] to catch leaked
    credentials before they are ever committed to version control.

### Integrity score

Each file receives a per-file **integrity score** (0–100): the ratio of *used* reference
definitions to *total* definitions. A score of 100 means every definition is referenced at least
once; lower scores indicate Dead Definitions that may be dead weight or copy-paste residue.

```text
File integrity: docs/api.md      — 100.0  (8/8 definitions used)
File integrity: docs/index.md    —  75.0  (3/4 definitions used)
File integrity: docs/roadmap.md  —  50.0  (2/4 definitions used)
```

Use `--strict` to treat Dead Definitions as hard errors and fail the pipeline when any file
scores below 100.

The formula is deterministic — no weights, no thresholds, just the ratio of Resolved References
to total Reference Definitions:

$$
Reference\ Integrity = \frac{Resolved\ References}{Total\ Reference\ Definitions}
$$

### Alt-text accessibility

The reference pipeline also emits `WARNING` findings for images without alt text:

```markdown
<!-- WARNING: no alt text -->
![](docs/assets/screenshot.png)

<!-- OK -->
![Zenzic CLI output showing pass/fail summary](docs/assets/screenshot.png)
```

These are warnings, not errors. They do not affect the exit code unless `--strict` is set.

---

## CI/CD integration

Zenzic is designed for pipeline-first workflows. All commands exit non-zero on failure — no
wrappers required. The examples below use GitHub Actions and [`uv`][uv]; the patterns apply to
any CI provider.

### `uvx` vs `uv run` vs bare `zenzic`

| Invocation | Behaviour | When to use |
| :--- | :--- | :--- |
| `uvx zenzic ...` | Downloads and runs Zenzic in an **isolated, ephemeral** environment | One-off jobs, pre-commit hooks, CI steps with no project install phase |
| `uv run zenzic ...` | Runs Zenzic from the **project's virtual environment** (requires `uv sync` first) | When Zenzic is in `pyproject.toml` and you need version-pinned behaviour |
| `zenzic ...` (bare) | Requires Zenzic on `$PATH` (after `uv tool install` or `pip install`) | Developer machines with a persistent global install |

!!! tip "CI recommendation"
    Prefer `uvx zenzic ...` for CI steps that do not already install project dependencies.
    It avoids adding Zenzic to your production dependency set while still benefiting from
    [uv][uv]'s dependency cache.

### GitHub Actions — documentation quality gate

```yaml
# .github/workflows/zenzic-scan.yml
name: Documentation quality

on: [push, pull_request]

jobs:
  docs-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Lint documentation
        run: uvx zenzic check all --strict
        # Exit 1 on any check failure

      - name: Reference integrity + Shield
        run: uvx zenzic check references
        # Exit 1 on Dangling References
        # Exit 2 immediately if Shield detects a leaked credential

      - name: Score regression check
        run: uvx zenzic diff --threshold 5
        # Exit 1 if score dropped more than 5 points vs the saved baseline
```

### Handling Exit Code 2 in CI

```yaml
- name: Reference integrity + Shield
  id: shield
  run: uvx zenzic check references
  # Do NOT set continue-on-error: true — a Shield failure is a security event

- name: Shield failure annotation
  if: failure() && steps.shield.outcome == 'failure'
  run: |
    echo "::error::Zenzic Shield triggered. Rotate exposed credentials before re-running."
```

!!! danger "Never suppress Exit Code 2"
    Setting `continue-on-error: true` on a step that runs `check references` defeats the
    Shield entirely. Exit code 2 must block the pipeline — it means a live credential was found
    in your documentation source.

### Baseline management

```yaml
# On the main branch — establish or refresh the score baseline
- name: Save quality baseline
  if: github.ref == 'refs/heads/main'
  run: uvx zenzic score --save
  # Writes .zenzic-score.json — commit this file to version control

# On pull requests — block regressions
- name: Score regression check
  if: github.event_name == 'pull_request'
  run: uvx zenzic diff --threshold 5
```

### Pre-commit hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: zenzic-references
        name: Zenzic Shield + reference integrity
        language: system
        entry: uvx zenzic check references
        types: [markdown]
        pass_filenames: false
```

!!! tip
    Because the Shield runs in Pass 1 — before any URL is validated or any HTTP request is
    issued — this hook catches leaked credentials before they are ever committed, not just
    before they are pushed.

---

## Choosing between modes

The two modes are not mutually exclusive. Many projects use both: the CLI for pre-commit hooks and
quick local audits, and as the definitive gate in CI.

| Scenario | Recommended approach |
| --- | --- |
| One-off audit, no install | `uvx zenzic check all` |
| Local development, quick feedback | `zenzic check all` (global or project install) |
| Pre-commit hook | `uvx zenzic check all` or `uv run zenzic check all` |
| CI: no MkDocs build step | CLI — `uv run zenzic check all` |
| Track quality over time | `zenzic score --save` on main + `zenzic diff` on PRs |
| Enforce a minimum quality floor | `zenzic score --fail-under 80` |
| Report without blocking (cleanup sprint) | `zenzic check all --exit-zero` or `fail_on_error: false` |
| Local development with live preview | `zenzic serve` |
| Link validation (always CLI only) | `zenzic check links [--strict]` |
| Reference integrity + secret scanning | `zenzic check references [--strict] [--links]` |
| Catch leaked credentials pre-commit | `zenzic check references` in pre-commit hook |

The link check and reference check are always CLI-only. The native link extractor and reference
— `zenzic check links --strict` and `zenzic check references` are the recommended way to validate
links and reference integrity in CI.

---

## Programmatic usage

Zenzic's core is a library first. Import `ReferenceScanner` and `ReferenceMap` directly into
your build tools or test suites.

### Single-file scan

```python
from pathlib import Path

from zenzic.core.scanner import ReferenceScanner
from zenzic.models.references import ReferenceMap

# Each scanner operates on a single Markdown file
scanner = ReferenceScanner(Path("docs/api.md"))

# Pass 1: harvest definitions + run the Shield
# Each event is a (lineno, event_type, data) tuple
# event_type in {"DEF", "DUPLICATE_DEF", "IMG", "MISSING_ALT", "SECRET"}
security_findings = []
for lineno, event, data in scanner.harvest():
    if event == "SECRET":
        # Shield fired — credential detected before any HTTP request is issued
        security_findings.append(data)
    elif event == "DUPLICATE_DEF":
        print(f"  WARN [{lineno}]: duplicate definition '{data}' (first wins per CommonMark §4.7)")

# Pass 2: resolve usages against the fully-populated ReferenceMap
# Must be called after harvest() completes — never interleave the passes
cross_check_findings = scanner.cross_check()
for finding in cross_check_findings:
    print(f"  {finding.level}: {finding.message}")

# Pass 3: integrity report
report = scanner.get_integrity_report(
    cross_check_findings=cross_check_findings,
    security_findings=security_findings,
)
print(f"Integrity: {report.integrity_score:.1f}%")
```

### Multi-file orchestration

For scanning an entire documentation tree with global URL deduplication, use the high-level
orchestrator:

```python
from pathlib import Path

from zenzic.core.scanner import scan_docs_references_with_links

reports, link_errors = scan_docs_references_with_links(
    repo_root=Path("."),
    validate_links=False,  # set True to also ping every unique reference URL (1 request/URL)
)

for report in reports:
    print(f"{report.file_path}: {report.integrity_score:.1f}%")

for err in link_errors:
    print(f"  LINK ERROR: {err}")
```

`scan_docs_references_with_links` enforces the Shield-as-firewall contract automatically:
if Pass 1 finds any secrets in any file, it raises `SystemExit(2)` before Pass 2 runs
on any file. No URL in a document containing a leaked credential is ever pinged.

<!-- ─── Reference link definitions ──────────────────────────────────────────── -->

[arch-two-pass]:  ../architecture.md#two-pass-reference-pipeline-v020
[arch-refmap]:    ../architecture.md#referencemap-state-management-between-passes
[arch-dedup]:     ../architecture.md#global-url-deduplication-via-linkvalidator
[pre-commit]:     https://pre-commit.com/
[uv]:             https://docs.astral.sh/uv/
