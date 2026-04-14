<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# mkdocs-basic — Fixture di Riferimento MkDocs 1.6.1

Un progetto MkDocs 1.x minimale e pulito, usato come baseline stabile per Zenzic.
Dimostra anche il plugin `zenzic.integrations.mkdocs` — un plugin MkDocs nativo
che attiva automaticamente `zenzic check all` durante ogni esecuzione di `mkdocs build`.

## Prerequisiti

Installa Zenzic con l'extra opzionale per l'integrazione MkDocs:

```bash
pip install "zenzic[mkdocs]"
```

Questo installa sia `zenzic` che `mkdocs>=1.6.1`. Senza questo extra, il plugin
`zenzic` dichiarato in `mkdocs.yml` causerà l'errore "Unknown plugin" durante
`mkdocs build`.

## Configurazione del Plugin

Il `mkdocs.yml` in questo esempio registra il plugin senza configurazione:

```yaml
plugins:
  - search
  - zenzic          # drop-in — nessun blocco di configurazione richiesto
```

Il plugin viene scoperto automaticamente tramite l'entry point `mkdocs.plugins`
registrato nel `pyproject.toml` di Zenzic.

## Eseguire

```bash
cd examples/mkdocs-basic
zenzic check all
```

Codice di uscita atteso: **0**.

O tramite MkDocs (esegue Zenzic come parte della pipeline di build):

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
- Dimostra il plugin `zenzic.integrations.mkdocs` come gate di qualità durante la build.
- Fornisce una baseline sicura per la migrazione a Zensical.
