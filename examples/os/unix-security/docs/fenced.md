<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Unix Security Probe — Fenced Block Attack

**RED TEAM** objective: hide credentials inside fenced code blocks, assuming the scanner
respects Markdown formatting boundaries and skips code examples.

**BLUE TEAM** response: the Shield treats **no line as invisible**. Fenced blocks are
scanned identically to prose. A credential in a `bash` example is a committed credential.

---

## Attempt 1 — Unlabelled fence

```text
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLEKEY
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

---

## Attempt 2 — Bash fence with OpenAI and GitHub tokens

```bash
export OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
export GITHUB_TOKEN=ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
export STRIPE_SECRET=sk_live_XXXXXXXXXXXXXXXXXXXXXXXX
```

---

## Attempt 3 — YAML configuration fence

```yaml
production:
  stripe_key: sk_live_XXXXXXXXXXXXXXXXXXXXXXXX
  slack_token: xoxb-0000000000-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
  google_api_key: AIzaSYXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

---

## Attempt 4 — PEM key fragment in a fence

```text
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0Z3VS5JJcds3xHn/ygWep4mSCiMmiGdFBT0MxRHoMXDCPbWb
-----END RSA PRIVATE KEY-----
```

---

Expected: Shield fires on all four blocks — exit **2**.

See also: [deep-traversal.md](deep-traversal.md), [obfuscated.md](obfuscated.md).
