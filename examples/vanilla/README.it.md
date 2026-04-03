<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# vanilla — Quality Gate Agnostico

Questo esempio dimostra Zenzic in **modalità Vanilla**: nessun MkDocs, nessun
Zensical, nessun motore di build. Solo file Markdown e un `zenzic.toml`.

## Cosa dimostra

- `engine = "vanilla"` abilita la modalità agnostica
- Link, snippet, placeholder, asset e regole custom vengono tutti controllati
- Il controllo orfani è disattivato — senza nav, ogni file è raggiungibile
- `fail_under = 80` impone un punteggio minimo di qualità
- Una regola `[[custom_rules]]` (`ZZ-NOHTML`) avvisa contro HTML inline

## Eseguire

```bash
cd examples/vanilla
zenzic check all
```

Codice di uscita atteso: **0** — `SUCCESS: All checks passed.`

## Per chi è pensato

Qualsiasi team che scrive documentazione Markdown senza MkDocs o Zensical:
Hugo, Docusaurus, Sphinx, Astro, Jekyll, wiki GitHub o nessun build tool.
Zenzic controlla il **sorgente** — il motore di build è irrilevante.
