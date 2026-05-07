<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Shield Extreme — Percent-Encoded Credentials

**RED TEAM** objective: percent-encode credential strings so that raw text matching
misses the `sk-`, `ghp_`, and `AKIA` prefixes.

**BLUE TEAM** response: the Shield URL-decodes content before scanning. Percent-encoded
credentials are normalised to their plaintext form prior to pattern matching.

---

## Technique 1 — Percent-encoded OpenAI key prefix

`%73%6b%2d%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58`

(Decodes to `sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`)

---

## Technique 2 — Percent-encoded GitHub token prefix

Set `%67%68%70%5f%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58%58` in your CI config.

(Decodes to `ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`)

---

## Technique 3 — Double-encoded AWS key

`%2541%254B%2549%2541%2549%254F%2553%254F%2544%254E%254E%2537%2545%2558%2541%254D%2550%254C%2545%254B%2545%2559`

(Decodes via two passes to `AKIAIOSFODNN7EXAMPLEKEY`)

---

Expected: Shield fires on percent-encoded credential patterns — exit **2**.

See also: [base64-secrets.md](base64-secrets.md), [mixed-case.md](mixed-case.md).
