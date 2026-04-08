<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Zenzic Safety Demonstration

This file is an **intentional test fixture** for Zenzic's built-in defences.
Run `zenzic check all` from the repository root and point it here to observe
the findings live.

Expected findings when this file is scanned:

- `CIRCULAR_LINK` (severity: `info`) — mutual link cycle with itself via the
  self-referential link below
- `security_breach` (severity: `security_breach`) — hex-encoded payload in the
  code block detected by the Zenzic Shield

---

## Circular Link Example

The link below points back to this same document, forming a trivial cycle:

[Back to this page](safety_demonstration.md)

This triggers `CIRCULAR_LINK` at severity `info`. It never blocks the build.
Use `zenzic check all --show-info` to display it.

---

## Hex-Encoded Payload Example

The code block below contains three consecutive `\xNN` hex escape sequences —
the minimum threshold for the `hex-encoded-payload` Shield pattern:

```python
# Example: hex-encoded payload that triggers the Shield
payload = "\x41\x42\x43"  # \x41\x42\x43 → "ABC" — 3 consecutive escapes
```

This triggers a `security_breach` finding (exit code 2). The Shield scans
every fenced code block, not just prose text.

---

## How to Test

```bash
# From the repository root — scan this single file:
zenzic check all examples/safety_demonstration.md --show-info

# Expected output:
#   💡 [CIRCULAR_LINK]  — info finding (shown because of --show-info)
#   🔴 [security_breach] — Shield: hex-encoded-payload detected
#   Exit code: 2
```

To test without `--show-info`, the `CIRCULAR_LINK` finding is suppressed and
only the Shield breach appears in the output.
