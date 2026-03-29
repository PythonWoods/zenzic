<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD053 -- unused reference definitions are intentional: they are the Shield trigger -->

# Security Lab — Zenzic Shield Test

This file intentionally contains patterns that trigger both layers of the **Zenzic Shield**.
It exists to verify Shield behaviour before releases. Run from this directory:

```bash
zenzic check links --strict          # triggers PathTraversal (exit 1)
zenzic check references              # triggers credential detection (exit 2)
```

---

## Layer 1 — Path Traversal

The link below attempts to escape the `docs/` root. Zenzic Shield classifies it as
`PathTraversal` — not a generic `FileNotFound` — and blocks it before any filesystem
access occurs.

[Exploit](../../../etc/passwd)

Expected output:

```text
[ERROR] attack.md — PathTraversal: ../../../etc/passwd escapes docs root
```

---

## Layer 2 — Credential Detection

The reference definitions below embed intentionally fake, credential-shaped patterns.
They exist **solely to exercise the Shield scanner** during pre-release testing.
All values are synthetic — they match the regex shape but are not valid credentials
for any service.

[openai-key]: sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
[github-token]: ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
[aws-key]: https://s3.example.com/AKIAIOSFODNN7EXAMPLEKEY/bucket
[stripe-key]: sk_live_XXXXXXXXXXXXXXXXXXXXXXXX
[slack-token]: xoxb-0000000000-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
[google-key]: https://maps.example.com/api?key=AIzaSYXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
[private-key]: -----BEGIN RSA PRIVATE KEY-----

Expected output:

```text
╔══════════════════════════════════════╗
║        SECURITY CRITICAL             ║
║  Secret(s) detected in documentation ║
╚══════════════════════════════════════╝

  [SHIELD] attack.md:35 — openai-api-key detected in reference
  [SHIELD] attack.md:36 — github-token detected in reference
  [SHIELD] attack.md:37 — aws-access-key detected in URL
  [SHIELD] attack.md:38 — stripe-live-key detected in reference
  [SHIELD] attack.md:39 — slack-token detected in reference
  [SHIELD] attack.md:40 — google-api-key detected in URL
  [SHIELD] attack.md:41 — private-key detected in reference

Build aborted. Rotate the exposed credential immediately.
```

Exit code: **2**

---

## Patterns covered

| Pattern | Example shape | What it catches |
| --- | --- | --- |
| `openai-api-key` | `sk-` + 48 alphanum | OpenAI API keys |
| `github-token` | `gh[pousr]_` + 36 alphanum | GitHub personal/OAuth tokens |
| `aws-access-key` | `AKIA` + 16 `[0-9A-Z]` | AWS IAM access key IDs |
| `stripe-live-key` | `sk_live_` + 24 alphanum | Stripe live secret keys |
| `slack-token` | `xox[baprs]-` + 10–48 alphanum | Slack bot/user/app tokens |
| `google-api-key` | `AIza` + 35 alphanum/`-_` | Google Cloud / Maps API keys |
| `private-key` | `-----BEGIN * PRIVATE KEY-----` | PEM private keys (RSA, EC, etc.) |

---

## Why exit code 2 is non-suppressible

Shield events use exit code `2` — distinct from `1` (check failures) — so CI pipelines can
treat credential exposure as a hard blocker independently of `--exit-zero`.

```bash
zenzic check references || true   # --exit-zero does NOT suppress code 2
```

See [traversal.md](traversal.md) for the path traversal demo and
[absolute.md](absolute.md) for the portability enforcement demo.
