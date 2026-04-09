<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Security Analysis: Vulnerabilities in v0.5.0a3 {#security-analysis-v050a3}

---

> *"Ciò che non è documentato, non esiste; ciò che è documentato male, è
> un'imboscata."*
>
> This document records the root causes and architectural reasoning behind
> each vulnerability — to prevent regression and to inform future contributors.

---

## 1. Executive Summary

During the alpha phase of v0.5.0a3, an internal security analysis identified **four
confirmed vulnerabilities** spanning the three pillars
of Zenzic's security model: the Shield (secret detection), the Virtual Site Map
(routing validation), and the Adaptive Parallelism engine.

All four were resolved in v0.5.0a4. This document records the root causes,
attack mechanics, and architectural reasoning behind each fix — both to prevent
regression and to explain to future contributors *why* the code is shaped the
way it is.

---

## 2. The Sentinel's Threat Model

Before examining each finding, it helps to understand what the Sentinel
promises and what it does not.

| Promise | Mechanism |
|---------|-----------|
| No secret commits | Shield scans every byte before processing |
| No broken links | VSM validates links against routing state, not the filesystem |
| No deadlocked CI | Worker timeout + canary reject catastrophic patterns |
| No false navigation | VSM resolves links from source-file context |

The analysis found that three of these four promises had structural gaps — not
logic bugs, but **architectural blind spots** where the component was correctly
designed for its *stated input* but had never considered a class of inputs that
was technically valid.

---

## 3. Findings

### ZRT-001 — CRITICAL: Shield Blind to YAML Frontmatter

#### What Happened

`ReferenceScanner.harvest()` runs two passes over each file:

1. **Pass 1 (Shield):** scan lines for secret patterns.
2. **Pass 1b (Content):** harvest reference definitions and alt-text.

Both passes needed to skip YAML frontmatter (`---` blocks) — but for *different
and opposite reasons*:

- The **Content pass** must skip frontmatter because `author: Jane Doe` would
  otherwise be parsed as a broken reference definition.
- The **Shield pass** must **not** skip frontmatter because `aws_key: AKIA…`
  is a real secret that must be caught.

The original implementation shared a single generator, `_skip_frontmatter()`,
for both passes. This was correct for the Content stream and catastrophically
wrong for the Shield stream.

#### Attack Path

```markdown
---
description: API Guide
aws_key: AKIA[20-char-key-redacted]      ← invisible to Shield
stripe_key: sk_live_[24-char-key-redacted]  ← invisible to Shield
---

# API Guide

Normal content here.
```

```bash
zenzic check all   # Exit 0 — PASS  ← Zero findings reported (pre-fix)
git commit -am "add api credentials"  # Key committed, CI green — breach
```

#### Root Cause Diagram

```text
                ┌─────────────────────────────────┐
                │  harvest()                       │
                │                                  │
File on disk ──►│  _skip_frontmatter(fh)           │──► Shield stream
                │      ↑                           │
                │      skips lines 1–N             │   (BLIND SPOT)
                │      of the --- block            │
                │                                  │
                │  _iter_content_lines(file)       │──► Content stream
                └─────────────────────────────────┘
```

#### The Fix: Dual-Stream Architecture

The two streams now use **different generators** with **different filtering
contracts**:

```text
                ┌─────────────────────────────────┐
                │  harvest()                       │
                │                                  │
File on disk ──►│  enumerate(fh, start=1)          │──► Shield stream
                │      ↑                           │      (ALL lines)
                │      no filtering                │
                │                                  │
                │  _iter_content_lines(file)       │──► Content stream
                │      ↑                           │   (frontmatter +
                │    skips frontmatter             │    fences skipped)
                │    skips fenced blocks           │
                └─────────────────────────────────┘
```

The Shield now sees every byte of the file. The Content stream continues to
skip frontmatter to avoid false-positive reference findings.

**Why this is structurally sound:** The Shield and the Content harvester have
orthogonal filtering requirements. They must never share a generator.

---

### ZRT-002 — HIGH: ReDoS + ProcessPoolExecutor Deadlock

#### What Happened

The `AdaptiveRuleEngine` validates rules for pickle-serializability at
construction time (`_assert_pickleable()`). This is correct — it ensures every
rule can be dispatched to a worker process. However, `pickle.dumps()` is
blind to computational complexity. A pattern like `^(a+)+$` pickles cleanly
and dispatches successfully, then hangs indefinitely inside the worker when
applied to a string like `"a" * 30 + "b"`.

`ProcessPoolExecutor` in its original form used `executor.map()`, which has no
timeout. The result: one evil `[[custom_rules]]` entry in `zenzic.toml` could
permanently block every CI pipeline that ran on a repository with ≥ 50 files.

#### The Complexity of Catastrophic Backtracking

The pattern `^(a+)+$` contains a **nested quantifier** — `+` inside `+`. When
applied to `"aaa…aab"` (the ReDoS trigger), the regex engine must explore an
exponential number of paths through the string before determining it does not
match. At n=30 characters, this takes minutes. At n=50, hours.

The key insight is that `re.compile()` does **not** validate for ReDoS.
Compilation is O(1). The catastrophic cost only materialises at `match()`/`search()`
time on crafted input.

#### Attack Path

```toml
# zenzic.toml
[[custom_rules]]
id = "STYLE-001"
pattern = "^(a+)+$"      # ← catastrophic backtracking
message = "Style check"
severity = "error"
```

```markdown
<!-- docs/payload.md -->
aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaab    ← ReDoS trigger string
```

```bash
zenzic check all --workers 4   # All 4 workers hang. CI never exits.
```

#### Two Complementary Defences

**Prevention — `_assert_regex_canary()` (construction time):**

```text
AdaptiveRuleEngine.__init__():
    for rule in rules:
        _assert_pickleable(rule)   ← existing check
        _assert_regex_canary(rule) ← NEW: 100ms SIGALRM stress test
```

The canary runs each `CustomRule` pattern against three stress strings under a
`signal.SIGALRM` watchdog of 100 ms. If the pattern takes longer than 100 ms
on a 30-character input, it is categorically catastrophic and raises
`PluginContractError` *before the first file is scanned*.

**Containment — `future.result(timeout=30)` (runtime):**

```text
# Before
raw = list(executor.map(_worker, work_items))   # hangs forever

# After
futures_map = {executor.submit(_worker, item): item[0] for item in work_items}
for fut, md_file in futures_map.items():
    try:
        raw.append(fut.result(timeout=30))
    except concurrent.futures.TimeoutError:
        raw.append(_make_timeout_report(md_file))  # Z009 finding, never crash
```

A worker that exceeds 30 seconds produces a `Z009: ANALYSIS_TIMEOUT` finding
instead of hanging the coordinator.

**Why both defences are necessary:** The canary is platform-dependent
(`SIGALRM` is POSIX-only; it is a no-op on Windows). The timeout is the
universal backstop.

---

### ZRT-003 — MEDIUM: Split-Token Shield Bypass via Table Obfuscation

#### What Happened

The Shield's `scan_line_for_secrets()` applied regex patterns to each raw line.
The AWS key pattern `AKIA[0-9A-Z]{16}` requires 20 **contiguous** characters.
An author (malicious or careless) who documents credentials in a table column
using inline code notation and concatenation operators breaks the contiguity:

```markdown
| Key ID | `AKIA` + `[16-char-suffix]` |
```

The raw line fed to the regex is (rendered in source as split tokens):

```text
| Key ID | `AKIA` + `[16-char-suffix]` |
```

The longest contiguous alphanum sequence is `ABCDEF` (6 chars). The pattern
never matches. The Shield reports zero findings.

#### The Fix: Pre-Scan Normalizer

`_normalize_line_for_shield()` applies three transformations before the regex
patterns run:

1. **Unwrap backtick spans:** `` `AKIA` `` → `AKIA`
2. **Remove concatenation operators:** `` ` ` + ` ` `` → nothing
3. **Collapse table pipes:** `|` → ``

The normalised form of the attack line is `Key ID AKIA[16-char-suffix]`,
which matches `AKIA[0-9A-Z]{16}` cleanly.

**Both** the raw and normalised forms are scanned. A `seen` set prevents
duplicate findings when a secret appears non-obfuscated *and* the normalised
form also matches.

---

### ZRT-004 — MEDIUM: VSMBrokenLinkRule Context-Free URL Resolution

#### What Happened

`VSMBrokenLinkRule._to_canonical_url()` was a `@staticmethod`. It converted
hrefs to canonical VSM URLs using a root-relative algorithm: strip `.md`,
drop `index`, prepend `/`, append `/`. This is correct for files in the docs
root but produces the wrong result for files in subdirectories when the href
contains `..` segments.

#### Example of the Bug

```text
Source file:  docs/a/b/page.md
Link:         [See this](../../c/target.md)

Expected URL: /c/target/    ← what the browser would navigate to
Computed URL: /c/target/    ← accidentally correct in this 2-level case

Source file:  docs/a/b/page.md
Link:         [See this](../sibling.md)

Expected URL: /a/sibling/   ← file is docs/a/sibling.md
Computed URL: /sibling/     ← WRONG: resolved from root, not from source dir
```

The `InMemoryPathResolver` (used by `validate_links_async`) resolved links
correctly because it had `source_file` context from the beginning. The
`VSMBrokenLinkRule` did not, creating a silent discrepancy between two
validation surfaces.

#### The Fix: ResolutionContext

```python
@dataclass(slots=True)
class ResolutionContext:
    docs_root: Path
    source_file: Path
```

`BaseRule.check_vsm()` and `AdaptiveRuleEngine.run_vsm()` now accept
`context: ResolutionContext | None = None`. When context is provided,
`_to_canonical_url()` resolves `..` segments using `os.path.normpath`
relative to `context.source_file.parent`, then maps the absolute resolved path
back to a docs-relative URL.

The method also enforces the Shield boundary: if the resolved path escapes
`docs_root`, it returns `None` (equivalent to a `PathTraversal` outcome in
`InMemoryPathResolver`).

**The Architectural Lesson:** Any method that converts a relative href to an
absolute URL *must* know where that href came from. A `@staticmethod` that
receives only the href string is structurally incapable of handling relative
paths correctly. In Zenzic, this is now called the **Context-Free Anti-Pattern**
(see `docs/arch/vsm_engine.md` for the full protocol).

---

## 4. The Stream Multiplexing Architecture

Post-remediation, `ReferenceScanner.harvest()` implements a clean two-stream
model. This section documents it for future contributors.

```text
┌─────────────────────────────────────────────────────────────────┐
│  ReferenceScanner.harvest()                                     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  SHIELD STREAM                                          │   │
│  │  Source: enumerate(file_handle, start=1)                │   │
│  │  Filter: NONE — every line including frontmatter        │   │
│  │  Transforms:                                            │   │
│  │    1. _normalize_line_for_shield(line)  [ZRT-003]       │   │
│  │    2. scan_line_for_secrets(raw)                        │   │
│  │    3. scan_line_for_secrets(normalized)                 │   │
│  │  Output: ("SECRET", SecurityFinding) events             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  CONTENT STREAM                                         │   │
│  │  Source: _iter_content_lines(file_path)                 │   │
│  │  Filter: skips YAML frontmatter, skips fenced blocks    │   │
│  │  Transforms:                                            │   │
│  │    1. Parse reference definitions (_RE_REF_DEF)         │   │
│  │    2. Scan ref-def URLs for secrets (scan_url_for_sec…) │   │
│  │    3. Parse inline images (_RE_IMAGE_INLINE)            │   │
│  │  Output: ("DEF", "IMG", "MISSING_ALT", …) events       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Final output: events merged and sorted by line number          │
└─────────────────────────────────────────────────────────────────┘
```

**Invariant:** The Shield stream and the Content stream must *never share a
generator*. Any future refactoring that merges them reintroduces ZRT-001.

---

## 5. What Made These Vulnerabilities Possible

All four findings share a common root: **implicit contracts at subsystem
boundaries**.

| Finding | Implicit contract violated |
|---------|--------------------------|
| ZRT-001 | "The Shield sees all lines" — violated by shared generator |
| ZRT-002 | "Pickle-safe means execution-safe" — violated by ReDoS blindness |
| ZRT-003 | "One line = one token" — violated by Markdown syntax fragmentation |
| ZRT-004 | "URL resolution is context-free" — violated by relative paths |

The fix in each case is the same pattern: **make the contract explicit in the
type system or function signature**, and **test it directly**.

---

## 6. Regression Prevention

The following tests in `tests/test_redteam_remediation.py` serve as permanent
regression guards. They must never be deleted or weakened:

| Test class | What it guards |
|------------|---------------|
| `TestShieldFrontmatterCoverage` | ZRT-001 — frontmatter scanning |
| `TestReDoSCanary` | ZRT-002 — canary rejection at construction |
| `TestShieldNormalizer` | ZRT-003 — split-token reconstruction |
| `TestVSMContextAwareResolution` | ZRT-004 — context-aware URL resolution |
| `TestShieldReportingIntegrity` | Z-SEC-002 — breach severity, secret masking, bridge fidelity |

If a future refactoring causes any of these tests to fail, the PR **must not
be merged** until either the test is proven incorrect (and the regression guard
is replaced with an equivalent) or the fix is reverted.

---

## 7. Lessons Learned

For v0.5.0rc1 and beyond:

1. **Every new subsystem boundary must document its filtering contract.**
   A generator that skips lines must have a JSDoc-style note explaining
   *what* it skips and *why* the caller is permitted to use it.

2. **`@staticmethod` methods that handle paths are suspect by default.**
   If a static method takes a path string, ask: does it need to know where
   that path came from? If yes, it is not a static method — it is a missing
   context argument.

3. **User-supplied regex patterns are untrusted inputs.** Always run the
   canary. The 100 ms budget is not a performance requirement — it is a
   security boundary.

4. **The parallelism layer must always have a timeout.** A coordinator that
   waits indefinitely on workers is a single point of failure for the entire
   CI pipeline.

---

*This document is current as of v0.5.0a4.*
