<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Shield Extreme — Base64-Encoded Credentials

**RED TEAM** objective: encode credential strings in Base64, betting that the scanner
only performs raw string matching against known prefixes.

**BLUE TEAM** response: the Shield normalises content before pattern matching. Base64
payloads that decode to credential-shaped strings are detected.

---

## Technique 1 — Base64 AWS Access Key

The following string decodes to `AKIAIOSFODNN7EXAMPLEKEY`:

```text
QUtJQUlPU0ZPRE5ON0VYQU1QTEVLRVY=
```

---

## Technique 2 — Base64 OpenAI API Key

The following string decodes to `sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`:

```text
c2stWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhY
```

---

## Technique 3 — Inline base64 in prose

Deploy with `api_key=QUtJQUlPU0ZPRE5ON0VYQU1QTEVLRVY=` to access the endpoint.

---

Expected: Shield fires on base64-encoded credential patterns — exit **2**.

See also: [encoded-creds.md](encoded-creds.md), [mixed-case.md](mixed-case.md).
