<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Shield Extreme — Mixed-Case Obfuscation

**RED TEAM** objective: alternate uppercase and lowercase in credential prefixes and
patterns, bypassing case-sensitive scanners that match `AKIA` but not `AkIa`.

**BLUE TEAM** response: the Shield case-folds all content before pattern matching.
Mixed-case obfuscation does not evade detection.

---

## Technique 1 — Mixed-case AWS prefix

`AkIaIoSfOdNn7ExAmPlEkEy`

---

## Technique 2 — Mixed-case OpenAI key

`Sk-XxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXx`

---

## Technique 3 — Mixed-case GitHub token

`GhP_XxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXx`

---

## Technique 4 — Mixed-case Stripe live key

`Sk_LiVe_XxXxXxXxXxXxXxXxXxXxXxXxXx`

---

## Technique 5 — Mixed-case Slack bot token

`XoXb-0000000000-XxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXx`

---

Expected: Shield fires on every mixed-case pattern — exit **2**.

See also: [base64-secrets.md](base64-secrets.md), [encoded-creds.md](encoded-creds.md).
