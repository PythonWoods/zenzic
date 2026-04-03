<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# i18n-standard — Il Gold Standard Bilingue

Questo esempio dimostra un progetto di documentazione bilingue perfettamente
strutturato che ottiene **100/100** con `zenzic check all --strict`.

## Cosa dimostra

- **Suffix-mode i18n**: le traduzioni sono file `page.it.md` nella stessa cartella
- **Simmetria dei percorsi**: un link relativo si risolve identicamente da `.md` e `.it.md`
- **Esclusione artefatti di build**: `manual.pdf` e `brand-kit.zip` in `excluded_build_artifacts`
- **`fail_under = 100`**: impone un punteggio perfetto

## Eseguire

```bash
cd examples/i18n-standard
zenzic check all --strict
```

Codice di uscita atteso: **0** — `SUCCESS: All checks passed.`

## Motore

Usa `engine = "mkdocs"` con il plugin `i18n` in modalità `docs_structure: suffix`.
