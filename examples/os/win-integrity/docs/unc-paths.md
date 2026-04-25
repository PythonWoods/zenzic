<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Windows Path Integrity — UNC Network Share Violations

**RED TEAM** objective: use UNC network share paths encoded as absolute Markdown links,
targeting documentation systems that render on Windows developer machines but break on
Linux CI/CD or deployed documentation hosts.

**BLUE TEAM** response: UNC paths encoded as `/UNC/server/share/` begin with `/` —
Z105 `ABSOLUTE_LINK` fires identically to drive-letter paths.

---

## Batch 1 — File Server Shares

[Project files](/UNC/fileserver/projects/source/)

[HR documents](/UNC/corpserver/hr/payroll/salaries.xlsx)

[Config store](/UNC/confserver/prod/app.config)

---

## Batch 2 — Named Pipe & Admin Shares

[IPC share](/UNC/dc01/IPC$/)

[Admin share](/UNC/workstation01/C$/)

[Print queue](/UNC/printserver/queue/pending/)

---

## Batch 3 — file:/// Constructs

[Local file via URI](/file:///C:/Windows/System32/drivers/etc/hosts)

[Network share via URI](/file:///UNC/server/share/secret.txt)

---

## Batch 4 — Mixed Slash Forms

[Forward-slash UNC](/UNC/server01/share/docs/)

[Dev share](/UNC/devbox/repos/internal-project/)

---

Expected: Z105 `ABSOLUTE_LINK` on every link above — exit **1**.

See also: [win-paths.md](win-paths.md).
