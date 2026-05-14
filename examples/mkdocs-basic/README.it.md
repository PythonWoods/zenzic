<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# mkdocs-basic — Fixture di Riferimento MkDocs 1.6.1

Un progetto MkDocs 1.x minimale e pulito, usato come baseline stabile per Zenzic.
Dimostra `MkDocsAdapter` su un layout reale MkDocs 1.x mantenendo il quality gate
nella CLI standalone di Zenzic.

## Prerequisiti

Installa Zenzic nel tuo ambiente:

```bash
pip install zenzic
```

Installa MkDocs separatamente solo se vuoi buildare la fixture del sito:

```bash
pip install "mkdocs>=1.6.1"
```

## Configurazione di Build

Il `mkdocs.yml` in questo esempio viene consumato staticamente da `MkDocsAdapter`:

```yaml
plugins:
  - search
```

Zenzic legge navigazione e forma i18n da `mkdocs.yml` senza importare né
eseguire MkDocs.

## Eseguire

```bash
cd examples/mkdocs-basic
zenzic check all
```

Codice di uscita atteso: **0**.

Oppure esegui la build MkDocs separatamente dopo che l'audit Zenzic è passato:

```bash
mkdocs build --strict
```

## Configurazione

Questo esempio usa `zenzic.toml`. Zenzic supporta anche la tabella `[tool.zenzic]`
all'interno di `pyproject.toml` come fallback:

```toml
# pyproject.toml — configurazione alternativa
[tool.zenzic]
docs_dir = "docs"
fail_under = 90

[tool.zenzic.build_context]
engine = "mkdocs"
```

## Perché esiste questa fixture

- Valida la compatibilità di `MkDocsAdapter` con MkDocs 1.6.x.
- Dimostra che Zenzic analizza `mkdocs.yml` staticamente senza eseguire MkDocs.
- Dimostra una baseline MkDocs sicura per la migrazione, validata dalla CLI standalone di Zenzic.
- Fornisce una baseline sicura per la migrazione a Zensical.
