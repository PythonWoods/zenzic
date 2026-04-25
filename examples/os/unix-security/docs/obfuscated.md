<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD053 -- credential reference definitions are intentional Shield triggers -->

# Unix Security Probe — Credential Obfuscation in Markdown Structure

**RED TEAM** objective: hide credentials inside Markdown structures that naive scanners
skip — tables, blockquotes, link titles, and URL query parameters.

**BLUE TEAM** response: the Shield scans **every source line**, regardless of structure.
No Markdown element is exempt from inspection.

---

## Technique 1 — Credentials in a Config Table

| Service      | Endpoint                   | Credential                                           |
|:-------------|:---------------------------|:-----------------------------------------------------|
| AWS S3       | s3.us-east-1.amazonaws.com | AKIAIOSFODNN7EXAMPLEKEY                              |
| OpenAI       | api.openai.com             | sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  |
| Stripe       | api.stripe.com             | sk_live_XXXXXXXXXXXXXXXXXXXXXXXX                     |
| GitHub       | api.github.com             | ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX             |

---

## Technique 2 — Credentials in a Blockquote (config dump)

> Production environment — do not commit:
> OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
> GITHUB_TOKEN=ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
> AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLEKEY

---

## Technique 3 — Credentials Embedded in Link Titles

[API Documentation](https://docs.example.com "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")

[Deployment Guide](https://deploy.example.com "sk_live_XXXXXXXXXXXXXXXXXXXXXXXX")

---

## Technique 4 — Credentials in URL Query Parameters

[Export endpoint](https://api.example.com/export?key=AIzaSYXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX)

[Webhook callback](https://hooks.example.com/receive?token=xoxb-0000000000-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX)

---

Expected: Shield fires on every technique — exit **2**.

See also: [deep-traversal.md](deep-traversal.md), [fenced.md](fenced.md).
