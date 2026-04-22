<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# standalone — Quality Gate Agnostico

Questo esempio dimostra Zenzic in **Standalone Mode**: nessun MkDocs, nessun
Zensical, nessun motore di build. Solo file Markdown e un `zenzic.toml`.

## Cosa dimostra

- `engine = "standalone"` abilita la modalità agnostica
- Link, snippet, placeholder, asset e regole custom vengono tutti controllati
- Il rilevamento orfani (`Z402`) è disattivato — non esiste un contratto di navigazione
- `fail_under = 80` impone un punteggio minimo di qualità
- Una regola `[[custom_rules]]` (`ZZ-NOHTML`) avvisa contro HTML inline

## Eseguire

```bash
cd examples/standalone
zenzic check all
```

Codice di uscita atteso: **0** — `SUCCESS: All checks passed.`

## Per chi è pensato

Qualsiasi team che scrive documentazione Markdown senza MkDocs o Zensical:
Hugo, Docusaurus, Sphinx, Astro, Jekyll, wiki GitHub o nessun build tool.
Zenzic controlla il **sorgente** — il motore di build è irrilevante.
