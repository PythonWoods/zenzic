<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Windows Path Integrity — Absolute Link Violations

**RED TEAM** objective: embed Windows-style filesystem paths as Markdown link targets,
betting that the scanner only checks for `http://` or `../` patterns.

**BLUE TEAM** response: Z105 `ABSOLUTE_LINK` fires on every link whose target begins
with `/` — the initial slash makes it environment-dependent regardless of what follows.

---

## Batch 1 — System Paths

[System hosts file](/C:/Windows/System32/drivers/etc/hosts)

[Windows registry SAM](/C:/Windows/system32/config/SAM)

[System32 directory](/C:/Windows/System32/)

[Temp directory](/C:/Windows/Temp/)

---

## Batch 2 — User Profile Paths

[Administrator desktop](/C:/Users/Administrator/Desktop/)

[User credentials](/C:/Users/Administrator/AppData/Roaming/Microsoft/Credentials/)

[SSH known hosts](/C:/Users/Administrator/.ssh/known_hosts)

[Git config](/C:/Users/Administrator/.gitconfig)

---

## Batch 3 — Program Files & AppData

[Program Files](/C:/Program Files/)

[App config](/C:/ProgramData/example-app/config.json)

[IIS webroot](/C:/inetpub/wwwroot/)

[Startup folder](/C:/ProgramData/Microsoft/Windows/Start Menu/Programs/StartUp/)

---

## Batch 4 — Alternative Drive Letters

[Data drive root](/D:/data/)

[Backup archive](/E:/backup/credentials.zip)

[Network-mapped drive](/Z:/shared/secrets.env)

---

Expected: Z105 `ABSOLUTE_LINK` on every link above — exit **1**.

See also: [unc-paths.md](unc-paths.md).
