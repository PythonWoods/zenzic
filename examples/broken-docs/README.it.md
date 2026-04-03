<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# broken-docs — Fixture con Errori Intenzionali

Questo esempio attiva intenzionalmente ogni controllo di Zenzic. Esiste per
dimostrare come appaiono gli errori nel nuovo Sentinel Report e per servire
come fixture di regressione per il motore di controllo.

## Cosa dimostra

| Controllo | Trigger |
| --- | --- |
| Link — file mancante | `non-existent.md` non esiste |
| Link — ancora morta | `#non-existent-section` assente |
| Link — path traversal | `../../../../etc/passwd` esce da `docs/` |
| Link — percorso assoluto | `/assets/logo.png` non è relativo |
| Link — UNREACHABLE_LINK | `orphan-nav.md` assente dal nav |
| Orfani | `api.md` non è nel nav |
| Snippet | `tutorial.md` contiene un `SyntaxError` Python |
| Placeholder | `api.md` ha solo 18 parole |
| Asset | `assets/unused.png` non è referenziato |
| Regole custom | `ZZ-NOFIXME` in `zenzic.toml` |

## Eseguire

```bash
cd examples/broken-docs
zenzic check all
```

Codice di uscita atteso: **1** (errori di controllo).

## Motore

Usa `engine = "mkdocs"` (via `[build_context]` in `zenzic.toml`).
