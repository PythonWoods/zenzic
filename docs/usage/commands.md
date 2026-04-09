---
icon: lucide/terminal
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# CLI Commands {#cli-commands}

Complete reference for every Zenzic command, flag, and exit code.

---

## Checks

```bash
# Individual checks
zenzic check links        # Internal links; add --strict for external HTTP validation
zenzic check orphans      # Pages on disk missing from nav
zenzic check snippets     # Python code blocks that fail to compile
zenzic check placeholders # Stub pages: low word count or forbidden patterns
zenzic check assets       # Media files not referenced by any page
zenzic check references   # Reference-style links + Zenzic Shield (credential detection)

# All checks in sequence
zenzic check all                    # Run all checks
zenzic check all --strict           # Also validate external URLs; treat warnings as errors
zenzic check all --format json      # Machine-readable output
zenzic check all --exit-zero        # Report issues but always exit 0
zenzic check all --quiet            # Minimal one-line output for pre-commit and CI hooks
zenzic check all --engine mkdocs    # Override detected build engine adapter
zenzic check links --show-info      # Show info-level findings (e.g. circular links)
```

## Global flags {#global-flags}

These flags control Zenzic's signal-to-noise profile across routine scans, CI gates,
and incident response workflows.

### `--strict`

| Command | Effect |
| :--- | :--- |
| `check links --strict` | Validates external HTTP/HTTPS URLs via concurrent network requests |
| `check all --strict` | Validates external URLs + treats warnings as errors |
| `check references --strict` | Treats Dead Definitions (unused reference links) as hard errors |
| `score --strict` / `diff --strict` | Runs link check in strict mode |

You can also set `strict = true` in `zenzic.toml` to make it the permanent default.

### `--exit-zero`

Always exits with code `0` even when issues are found. All findings are still printed and
scored — only the exit code is suppressed. Useful for observation-only pipelines.

Security events are never downgraded by this flag: Exit 2 (Shield credential breach) and
Exit 3 (Blood Sentinel system-path incident) always keep priority over ordinary failures.

You can also set `exit_zero = true` in `zenzic.toml` to make it the permanent default.

### `--show-info`

By default, info-level findings are hidden to keep everyday output focused on actionable
violations. Use `--show-info` when you want full Sentinel visibility into non-blocking
signals such as link-cycle topology (`CIRCULAR_LINK`).

Available on all `zenzic check` commands.

```bash
zenzic check links --show-info
zenzic check all --show-info
```

### `--quiet`

`--quiet` is available on `zenzic check all` and is designed for silent builders
(pre-commit and CI hooks) that need minimal output.

- Suppresses the rich Sentinel panel and per-file verbose report.
- Prints a compact one-line summary for error/warning totals.
- Prints an explicit security one-liner for Shield breaches (Exit 2).
- Still enforces fatal exit behavior, including security priority (`3 > 2 > 1`).

```bash
zenzic check all --quiet
```

---

## Initialization

```bash
zenzic init                               # Scaffold zenzic.toml in the current project
zenzic init --pyproject                   # Write config into pyproject.toml [tool.zenzic]
zenzic init --force                       # Overwrite existing config without prompting
zenzic init --plugin plugin-scaffold-demo # Scaffold a plugin SDK package
```

**Smart detection** — when `pyproject.toml` exists in the project root, `zenzic init`
asks whether to embed the configuration there as a `[tool.zenzic]` table instead of
creating a separate `zenzic.toml`.  Pass `--pyproject` to skip the prompt and write
directly into `pyproject.toml`.

Engine auto-detection is included in both modes: if `mkdocs.yml` or `zensical.toml`
is present, the generated configuration pre-sets the `engine` field accordingly.
When no engine config file is found, vanilla (engine-agnostic) defaults apply.

`zenzic init --plugin <name>` generates a Python package skeleton with a ready
`zenzic.rules` entry-point and a `BaseRule` template (`src/<module>/rules.py`).
It also includes a minimal docs fixture so the generated project can immediately
run `zenzic check all` as a smoke test.

---

## Autofix & Cleanup

```bash
zenzic clean assets           # Delete unused assets interactively (prompt before each)
zenzic clean assets -y        # Delete unused assets immediately (no prompt)
zenzic clean assets --dry-run # Preview what would be deleted without deleting
```

`zenzic clean assets` respects `excluded_assets`, `excluded_dirs`, and
`excluded_build_artifacts` from `zenzic.toml` — it will never delete files that match these
patterns.

---

## Development server

```bash
zenzic serve                  # Start dev server with pre-flight quality check
zenzic serve --engine mkdocs  # Force a specific engine
zenzic serve --engine zensical
zenzic serve --port 9000      # Custom starting port (tries up to 10 consecutive ports)
zenzic serve -p 9000
zenzic serve --no-preflight   # Skip pre-flight and start server immediately
```

`zenzic serve` auto-detects the documentation engine from the repository root:

| Config file present | Engine binary available | Result |
| :--- | :--- | :--- |
| `zensical.toml` | `zensical` or `mkdocs` | Starts available engine |
| `zensical.toml` | neither | Error — install an engine |
| `mkdocs.yml` only | `mkdocs` or `zensical` | Starts available engine |
| `mkdocs.yml` only | neither | Error — install an engine |
| neither | any | Static file server on `site/` (no hot-reload) |

Before launching the server, Zenzic runs a silent pre-flight check (orphans, snippets,
placeholders, unused assets). Issues are printed as warnings but never block startup. External
link validation is intentionally excluded from the pre-flight. Use `--no-preflight` to skip the
quality check entirely when you are mid-fix.

**Port handling.** Zenzic probes for a free port via socket before launching the engine
subprocess, then passes `--dev-addr 127.0.0.1:{port}` to mkdocs or zensical. The
`Address already in use` error can never appear from the engine.

---

## Exit codes {#exit-codes}

| Code | Meaning |
| :---: | :--- |
| `0` | All selected checks passed (or `--exit-zero` was set) |
| `1` | One or more checks reported issues |
| **`2`** | **SECURITY CRITICAL — Zenzic Shield detected a leaked credential** |
| **`3`** | **SECURITY INCIDENT — Blood Sentinel: link targets an OS system directory** |

!!! danger "Exit code 2 is reserved for security events"
    Exit code 2 is issued exclusively by `zenzic check references` when the Shield detects a
    known credential pattern embedded in a reference URL. It is never used for ordinary check
    failures. If you receive exit code 2, treat it as a build-blocking security incident and
    **rotate the exposed credential immediately**.

!!! danger "Exit code 3 — Blood Sentinel Incident"
    Exit code 3 is issued when the Blood Sentinel detects a link that resolves to an OS
    system directory (`/etc/`, `/root/`, `/var/`, `/proc/`, `/sys/`, `/usr/`). Unlike exit
    code 1, this is a security incident and takes priority over all other exit codes. It is
    never suppressed by `--exit-zero`. See
    [Checks: Blood Sentinel](../checks.md#blood-sentinel-system-path-traversal) for details.

---

## JSON output

Pass `--format json` to `check all` for structured output:

```bash
zenzic check all --format json | jq '.orphans'
zenzic check all --format json > report.json
```

The JSON report contains seven keys:

```json
{
  "links":         [],
  "orphans":       [],
  "snippets":      [],
  "placeholders":  [],
  "unused_assets": [],
  "references":    [],
  "nav_contract":  []
}
```

Each key holds a list of issue strings or objects. An empty list means the check passed.
`nav_contract` validates `extra.alternate` links in `mkdocs.yml` against the Virtual Site Map
— always empty for non-MkDocs projects.

---

## Engine override

The `--engine` flag overrides the build engine adapter for a single run without modifying
`zenzic.toml`. Accepted by `check orphans` and `check all`:

```bash
zenzic check orphans --engine mkdocs
zenzic check all --engine zensical
zenzic check all --engine vanilla    # disable orphan check regardless of config
```

If you pass an engine name with no registered adapter, Zenzic lists available adapters and
exits with code 1:

```text
ERROR: Unknown engine adapter 'hugo'.
Installed adapters: mkdocs, vanilla, zensical
Install a third-party adapter or choose from the list above.
```

Third-party adapters are discovered automatically once installed — no Zenzic update required.
See [Writing an Adapter](../developers/writing-an-adapter.md).

---

## Quality scoring

Individual checks answer a binary question: pass or fail. `zenzic score` answers a different one:
*how healthy is this documentation, and is it getting better or worse over time?*

```bash
zenzic score                   # Compute 0–100 quality score
zenzic score --save            # Compute and persist snapshot to .zenzic-score.json
zenzic score --fail-under 80   # Exit 1 if score is below threshold
zenzic score --format json     # Machine-readable score report

zenzic diff                    # Compare current score against saved snapshot
zenzic diff --threshold 5      # Exit 1 only if score dropped by more than 5 points
zenzic diff --format json      # Machine-readable diff report
```

### How the score is computed

Each check category carries a fixed weight that reflects its impact on the reader experience:

| Category | Weight | Rationale |
| :--- | ---: | :--- |
| links | 35 % | A broken link is an immediate dead end for the reader |
| orphans | 20 % | Unreachable pages are invisible — they might as well not exist |
| snippets | 20 % | Invalid code examples actively mislead developers |
| placeholders | 15 % | Stub content signals an unfinished or abandoned page |
| assets | 10 % | Unused assets are waste, but they do not block the reader |

Within each category, the score decays linearly: the first issue costs 20 % of the category
weight, the second costs another 20 %, floored at zero. A category with five or more issues
contributes nothing to the total. The weighted contributions are summed and rounded to an integer.

### Regression tracking

```bash
# On main — establish or refresh the baseline
zenzic score --save

# On every pull request — block documentation regressions
zenzic diff --threshold 5
```

`--threshold 5` gives contributors a five-point margin. Set it to `0` for a strict gate where
any regression fails the pipeline.

### Minimum score floor

```bash
zenzic score --fail-under 80
```

Use this when the team has committed to maintaining a defined quality level, regardless of what
the score was last week. You can also set `fail_under = 80` in `zenzic.toml` to make it
persistent.

### Soft reporting

To surface the score without blocking the pipeline:

```bash
zenzic check all --exit-zero   # full report, exit 0 regardless
zenzic score                   # show score for visibility
```

---

## Plugin inspection

```bash
zenzic plugins list   # List all rules registered in the zenzic.rules entry-point group
```

`zenzic plugins list` shows every lint rule the engine knows about — Core rules bundled with
Zenzic and any third-party rules installed from external packages:

```text
Installed plugin rules (1 found)

  broken-links  Z001  (core)  zenzic.core.rules.VSMBrokenLinkRule
```

Each row shows the entry-point name, the rule's stable `rule_id` (used in findings and
suppression lists), the origin distribution (`(core)` for built-in rules, or the package
name for third-party plugins), and the fully qualified Python class name.

Use this command to verify which rules are active after installing a plugin package.

---

## `uvx` vs `uv run` vs bare `zenzic`

| Invocation | Behaviour | When to use |
| :--- | :--- | :--- |
| `uvx zenzic ...` | Downloads and runs in an **isolated, ephemeral** environment | One-off jobs, pre-commit hooks, CI with no project install phase |
| `uv run zenzic ...` | Runs from the **project's virtual environment** (requires `uv sync`) | When Zenzic is in `pyproject.toml` and you need version-pinned behaviour |
| `zenzic ...` (bare) | Requires Zenzic on `$PATH` | Developer machines with a global install |

!!! tip "CI recommendation"
    Prefer `uvx zenzic ...` for CI steps that do not already install project dependencies — it
    avoids adding Zenzic to your production dependency set.
