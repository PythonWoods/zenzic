<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# security_lab — Fixture di Test per lo Shield di Zenzic

Questo esempio attiva intenzionalmente lo Shield di Zenzic (rilevamento credenziali)
e il controllo link (path traversal, link assoluti).

## Cosa dimostra

| File | Trigger |
| --- | --- |
| `traversal.md` | Path traversal: `../../etc/passwd` esce da `docs/` |
| `attack.md` | Path traversal + pattern di credenziali fake |
| `absolute.md` | Link assoluti (`/assets/logo.png`) |

## Eseguire

```bash
cd examples/security_lab

# Solo controllo link — esce con 1 (path traversal)
zenzic check links --strict

# Controllo riferimenti — esce con 2 (Shield: credenziali fake)
zenzic check references

# Suite completa — esce con 2 (Shield ha priorità)
zenzic check all
```

> **Nota:** Il codice di uscita `2` (evento Shield) non è sopprimibile con `--exit-zero`.

## Credenziali

Le credenziali in `attack.md` sono **completamente false** — corrispondono alla forma
regex di credenziali reali ma non sono token validi. Esistono solo per testare lo Shield.

## Motore

Usa `engine = "mkdocs"`. Nessuna configurazione i18n.
