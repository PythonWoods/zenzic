---
name: "🛡️ Gate Bypass Post-Mortem"
about: "Break-Glass protocol — documented bypass of the `just verify` Final Guard."
title: "[BYPASS] <short-emergency-description>"
labels: ["gate-bypass", "priority:critical"]
assignees: ""
---
<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD003 MD041 -->

> **Blameless principles**
>
> 1. **Data, not blame.** The failure log is objective evidence; narrative is secondary.
> 2. **System focus.** Root cause identifies *why the tool* (Zenzic / GHA / the action itself) failed, never who pushed.
> 3. **Always-on remediation.** Every bypass produces a task that hardens the gate so it is no longer needed next time.

## 🚨 1. Trigger

> What made the immediate bypass necessary? (hotfix to published action, total CI infra outage, broken upstream action dependency, ...)

## 📊 2. Gate Failure Log (Evidence)

> Paste the full output of `just verify` (or the failing GHA step) that blocked the push.

```bash
# paste log here
```

## 🔍 3. Root Cause Analysis

- [ ] **Self-check failure** (the action failed its own `self-check.yml` run)
- [ ] **Flakiness** (network fetch, runner ephemeral state)
- [ ] **Infrastructure** (GitHub Actions / local runner offline)
- [ ] **Upstream action break** (pinned action ref became unavailable)
- [ ] **Other** — describe:

## 🛠️ 4. Remediation

> Concrete change to the gate so this bypass becomes unnecessary in the future. Link the follow-up PR/issue here.

## ⏳ 5. Timeline & Scope

- **Bypass commit SHA / branch / PR:**
- **Bypass author:** (informational only — blameless)
- **Bypass time → post-mortem time** (max 24h):
- **Permanent fix merged at:**

---

*Bypass closed only when the permanent fix lands. Until then this issue stays open and is reviewed at every sprint retrospective.*
