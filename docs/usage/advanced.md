---
icon: lucide/shield-check
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Advanced Features

Deep reference for the Three-Pass Pipeline, Zenzic Shield, accessibility checks, and
programmatic usage from Python.

---

## Reference integrity (v0.2.0)

`zenzic check references` runs the **Three-Pass Reference Pipeline** — the core engine behind
every reference-quality and security check Zenzic performs.

### Why three passes?

Markdown [reference-style links][syntax] separate *where a link points* (the definition) from
*where it appears* (the usage). A single-pass scanner cannot resolve a reference that appears
before its definition. Zenzic solves this with a deliberate three-pass structure:

| Pass | Name | What happens |
| :---: | :--- | :--- |
| 1 | **Harvest** | Stream the file line-by-line; record all `[id]: url` definitions into a `ReferenceMap`; run the Shield on every URL and line |
| 2 | **Cross-Check** | Re-stream the file; for every `[text][id]` usage, look up `id` in the now-complete `ReferenceMap`; flag missing IDs as **Dangling References** |
| 3 | **Integrity Report** | Compute the integrity score; append **Dead Definitions**, duplicate-ID warnings, and alt-text warnings to the findings list |

Pass 2 only begins when Pass 1 completes without security findings. If the Shield fires during
harvesting, Zenzic exits immediately with code 2 — no reference resolution occurs on files that
contain leaked credentials.

### What the pipeline catches

| Issue | Type | Blocks exit? |
| :--- | :---: | :---: |
| **Dangling Reference** — `[text][id]` where `id` has no definition | error | Yes |
| **Dead Definition** — `[id]: url` defined but never used by any link | warning | No (yes with `--strict`) |
| **Duplicate Definition** — same `id` defined twice; first wins (CommonMark §4.7) | warning | No |
| **Missing alt-text** — `![](url)` or `<img>` with blank/absent alt | warning | No |
| **Secret detected** — credential pattern found in a reference URL or line | security | **Exit 2** |

### Reference Integrity Score

Each file receives a per-file score:

```text
Reference Integrity = (resolved definitions / total definitions) × 100
```

A file where every defined reference is used at least once scores 100. Unused (dead) definitions
pull the score down. When a file has no definitions at all, the score is 100 by convention.

The integrity score is a **per-file diagnostic** — it does not feed into the `zenzic score`
overall quality score. Use it to identify files that accumulate unused reference link
boilerplate.

---

## Zenzic Shield

The Shield runs **inside Pass 1** — every URL extracted from a reference definition is scanned
the moment the harvester encounters it, before any other processing continues. The Shield also
applies a defence-in-depth pass to non-definition lines to catch secrets in plain prose.

### Detected credential patterns

| Pattern name | Regex | What it catches |
| :--- | :--- | :--- |
| `openai-api-key` | `sk-[a-zA-Z0-9]{48}` | OpenAI API keys |
| `github-token` | `gh[pousr]_[a-zA-Z0-9]{36}` | GitHub personal/OAuth tokens |
| `aws-access-key` | `AKIA[0-9A-Z]{16}` | AWS IAM access key IDs |
| `stripe-live-key` | `sk_live_[0-9a-zA-Z]{24}` | Stripe live secret keys |
| `slack-token` | `xox[baprs]-[0-9a-zA-Z]{10,48}` | Slack bot/user/app tokens |
| `google-api-key` | `AIza[0-9A-Za-z\-_]{35}` | Google Cloud / Maps API keys |
| `private-key` | `-----BEGIN [A-Z ]+ PRIVATE KEY-----` | PEM private keys (RSA, EC, etc.) |

### Shield behaviour

- **Every line is scanned** — including lines inside fenced code blocks (labelled or unlabelled).
  A credential committed in a `bash` example is still a committed credential.
- Detection is **non-suppressible** — `--exit-zero`, `exit_zero = true` in `zenzic.toml`, and
  `--strict` have no effect on Shield findings.
- Exit code 2 is reserved **exclusively** for Shield events. It is never used for ordinary check
  failures.
- Files with security findings are **excluded from link validation** — Zenzic does not ping URLs
  that may contain leaked credentials.
- **Code block link isolation** — while the Shield scans inside fenced blocks, the link and
  reference validators do not. Example URLs inside code blocks (e.g. `https://api.example.com`)
  never produce false-positive link errors.

!!! danger "If you receive exit code 2"
    Treat it as a build-blocking security incident. Rotate the exposed credential immediately,
    then remove or replace the offending reference URL. Do not commit the secret into history.

---

## Hybrid scanning logic

Zenzic applies different scanning rules to prose and code blocks because the two contexts have
different risk profiles:

| Content location | Shield (secrets) | Snippet syntax | Link / ref validation |
| :--- | :---: | :---: | :---: |
| Prose and reference definitions | ✓ | — | ✓ |
| Fenced block — supported language (`python`, `yaml`, `json`, `toml`) | ✓ | ✓ | — |
| Fenced block — unsupported language (`bash`, `javascript`, …) | ✓ | — | — |
| Fenced block — unlabelled (` ``` `) | ✓ | — | — |

**Why links are excluded from fenced blocks:** documentation examples routinely contain
illustrative URLs (`https://api.example.com/v1/users`) that do not exist as real endpoints.
Checking them would produce hundreds of false positives with no security value.

**Why secrets are included everywhere:** a credential embedded in a `bash` example is still
a committed secret. It lives in git history, is indexed by code-search tools, and can be
extracted by automated scanners that do not respect Markdown formatting.

**Why syntax checking is limited to known parsers:** validating Bash or JavaScript would
require third-party parsers or subprocesses, violating the No-Subprocess Pillar. Zenzic
validates what it can validate purely in Python.

---

## Alt-text accessibility

`zenzic check references` also flags images that lack meaningful alt text:

- **Markdown inline images** — `![](url)` or `![   ](url)` (blank alt string)
- **HTML `<img>` tags** — `<img src="...">` with no `alt` attribute, or `alt=""` with no
  content

An explicitly empty `alt=""` is treated as intentionally decorative and is **not** flagged.
A completely absent `alt` attribute, or whitespace-only alt text, is flagged as a warning.

Alt-text findings are warnings — they appear in the report but do not affect the exit code
unless `--strict` is active.

---

## Programmatic usage

Import Zenzic's scanner functions directly into your own Python tooling.

### Single-file scan

Use `ReferenceScanner` to run the three-pass pipeline on one file:

```python
from pathlib import Path
from zenzic.core.scanner import ReferenceScanner

scanner = ReferenceScanner(Path("docs/guide.md"))

# Pass 1 — harvest definitions; collect Shield findings
security_findings = []
for lineno, event_type, data in scanner.harvest():
    if event_type == "SECRET":
        security_findings.append(data)
        # In production: raise SystemExit(2) or typer.Exit(2) here

# Pass 2 — resolve reference links (must be after harvest)
cross_check_findings = scanner.cross_check()

# Pass 3 — compute integrity score and consolidate all findings
report = scanner.get_integrity_report(cross_check_findings, security_findings)

print(f"Integrity score: {report.score:.1f}")
for f in report.findings:
    level = "WARN" if f.is_warning else "ERROR"
    print(f"  [{level}] {f.file_path}:{f.line_no} — {f.detail}")
```

### Multi-file scan

Use `scan_docs_references_with_links` to scan every `.md` file in a repository and optionally
validate external URLs:

```python
from pathlib import Path
from zenzic.core.scanner import scan_docs_references_with_links
from zenzic.models.config import ZenzicConfig

config, _ = ZenzicConfig.load(Path("."))

reports, link_errors = scan_docs_references_with_links(
    Path("."),
    validate_links=True,   # set False to skip HTTP validation
    config=config,
)

for report in reports:
    if report.security_findings:
        raise SystemExit(2)   # your code is responsible for exit-code enforcement
    for finding in report.findings:
        print(finding)

for error in link_errors:
    print(f"[LINK] {error}")
```

`scan_docs_references_with_links` deduplicates external URLs across the entire docs tree before
firing HTTP requests — 50 files linking to the same URL result in exactly one HEAD request.

### Parallel scan (large repos)

For repositories with more than ~200 Markdown files, use `scan_docs_references_parallel`:

```python
from pathlib import Path
from zenzic.core.scanner import scan_docs_references_parallel

reports = scan_docs_references_parallel(Path("."), workers=4)
```

Parallel mode uses `ProcessPoolExecutor`. External URL validation is not available in parallel
mode — use `scan_docs_references_with_links` for sequential scan with link validation.

---

## Fenced-code and frontmatter exclusion

The harvester and cross-checker both skip content that should never trigger findings:

- **YAML frontmatter** — the leading `---` block (first line only) is skipped in its entirety,
  including any reference-like syntax it might contain.
- **Fenced code blocks** — lines inside ` ``` ` or `~~~` fences are ignored. URLs in code
  examples never produce false positives.

This exclusion is applied consistently in both Pass 1 and Pass 2.

---

## Multi-language documentation

When your project uses [MkDocs i18n](https://github.com/ultrabug/mkdocs-static-i18n) or
Zensical's locale system, Zenzic adapts automatically:

- **Locale directories suppressed from orphan detection** — files under `docs/it/`, `docs/fr/`,
  etc. are not reported as orphans. The adapter detects locale directories from the engine's
  i18n configuration.
- **Cross-locale link resolution** — the MkDocs and Zensical adapters resolve links that cross
  locale boundaries (e.g. a link from `docs/it/page.md` to `docs/en/page.md`) without false
  positives.
- **Vanilla mode skips orphan check entirely** — when no build-engine config is present, every
  file would appear as an orphan. Zenzic skips the check rather than report noise.

!!! tip "Force Vanilla mode to suppress orphan check"
    ```bash
    zenzic check all --engine vanilla
    ```

[syntax]: https://spec.commonmark.org/0.31.2/#link-reference-definitions
