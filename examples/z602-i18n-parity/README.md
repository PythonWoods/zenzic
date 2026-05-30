<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z602 I18N_PARITY — Gallery Example

**Category:** Z6xx Governance
**Expected exit:** 1 (errors)

## What this demonstrates

`docs/en/` contains two files: `index.md` and `guide.md`.
`docs/it/` only contains `index.md` — `guide.md` is **missing from the IT
locale**. Zenzic's i18n parity checker flags this as **Z602 I18N_PARITY**.

## Run it

```bash
zenzic lab z602
# or directly:
zenzic check i18n
```bash

## Expected output

```bash
docs/it/  Z602  I18N_PARITY  guide.md present in EN but absent in IT
```bash

## Real-world fix

Create `docs/it/guide.md` with a translation of the English guide.
Until the translation is ready, add a stub with a note:

```markdown
# Guida — Configurazione avanzata

*Traduzione in corso. Vedi la [versione inglese](../../en/guide.md).*
```bash
