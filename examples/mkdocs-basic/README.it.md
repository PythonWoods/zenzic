<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# mkdocs-basic — Fixture di Riferimento MkDocs 1.6.1

Un progetto MkDocs 1.x minimale e pulito, usato come baseline stabile per Zenzic.

## Configurazione

Questo esempio usa `zenzic.toml`. Zenzic supporta anche la tabella `[tool.zenzic]`
all'interno di `pyproject.toml` (Issue #5) come fallback:

```toml
# pyproject.toml — configurazione alternativa
[tool.zenzic]
docs_dir = "docs"
fail_under = 90

[tool.zenzic.build_context]
engine = "mkdocs"
```

## Eseguire

```bash
cd examples/mkdocs-basic
zenzic check all
```

Codice di uscita atteso: **0**.

## Perché esiste questa fixture

- Valida la compatibilità di MkDocsAdapter con MkDocs 1.6.x.
- Dimostra che Zenzic analizza `mkdocs.yml` staticamente senza eseguire MkDocs.
- Fornisce una baseline sicura per la migrazione a Zensical.
