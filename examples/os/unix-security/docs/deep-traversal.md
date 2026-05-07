<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD053 -- credential reference definitions are intentional Shield triggers -->

# Unix Security Probe — Deep Traversal & Credential Exposure

**RED TEAM** objective: escape the docs root via multi-hop `../` chains while embedding
credential-shaped patterns across reference definitions.

**BLUE TEAM** response: Zenzic raises `PATH_TRAVERSAL` on every escaping link and
triggers the Shield on every credential reference — `check all` exits with code **2**.

---

## Layer 1 — Multi-Hop Path Traversal

Four-hop escape attempts targeting canonical Unix sensitive files.

[Read /etc/passwd](../../../../etc/passwd)

[Steal SSH authorized_keys](../../../root/.ssh/authorized_keys)

[Extract /etc/shadow](../../../../etc/shadow)

[Implant cron job](../../etc/cron.d/backdoor)

[Read /etc/hosts](../../etc/hosts)

---

## Layer 2 — Credential Reference Definitions

Synthetic credential-shaped patterns in Markdown reference definitions.
All values are fake — they exist solely to exercise the Shield scanner.

[prod-openai-key]: sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

[prod-github-token]: ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

[aws-iam-key]: AKIAIOSFODNN7EXAMPLEKEY

[stripe-live]: sk_live_XXXXXXXXXXXXXXXXXXXXXXXX

[slack-bot]: xoxb-0000000000-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

---

Expected exit: **2** (Shield credential detection takes priority over link errors).

See [obfuscated.md](obfuscated.md) and [fenced.md](fenced.md).
