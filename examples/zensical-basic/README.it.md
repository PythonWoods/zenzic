<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Esempio Base Zensical

Un progetto minimale che mostra l'integrazione di Zenzic con il motore di build
[Zensical](https://zensical.org) (v0.0.31+).

## Cosa dimostra

| Funzionalità | Dove |
| --- | --- |
| Sintassi `[project].nav` (v0.0.31+) | `zensical.toml` |
| `engine = "zensical"` | `zenzic.toml` `[build_context]` |
| Sezioni nav annidate | `zensical.toml` |
| Rilevamento orfani | qualsiasi file assente dal nav |
| Link relativi puliti | `docs/**/*.md` |

## Eseguire

```bash
cd examples/zensical-basic
zenzic check all
```

Risultato atteso: `SUCCESS` con punteggio ≥ 90.
