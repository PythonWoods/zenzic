---
icon: lucide/plug
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Adapter e Motore

Zenzic usa un **adapter** per ottenere conoscenza specifica del motore — struttura della nav,
directory i18n e pattern locale — senza importare o eseguire alcun framework di build. Gli adapter
sono scoperti a runtime tramite Python entry-points.

---

## `[build_context]`

**Tipo:** tabella — **Default:** `engine = "mkdocs"`, `default_locale = "en"`, `locales = []`,
`fallback_to_default = true`

Contesto engine e i18n per la risoluzione dei percorsi locale-aware. Richiesto solo per i
progetti che usano **Folder Mode i18n** (`docs_structure: folder`).

```toml
[build_context]
engine         = "mkdocs"   # "mkdocs" o "zensical"
default_locale = "en"       # codice ISO 639-1 del locale di default
locales        = ["it"]     # nomi delle directory locale non-default
# fallback_to_default = true
```

> **Ordine TOML:** `[build_context]` deve essere l'**ultima** sezione in `zenzic.toml`.

### `engine`

**Default:** `"mkdocs"`

Seleziona l'adapter usato per l'estrazione della nav e la risoluzione dei percorsi i18n. I valori
validi per un'installazione Zenzic standard sono `"mkdocs"` e `"zensical"`. Gli adapter di
terze parti aggiungono i propri valori.

### `locales`

**Default:** `[]`

Nomi delle directory locale non-default. Zenzic usa questa lista per:

1. **Fallback asset** — un link da `docs/it/index.md` a `assets/logo.svg` risolve letteralmente
   in `docs/it/assets/logo.svg` (che non esiste). Sapendo che `"it"` è una directory locale,
   Zenzic rimuove il prefisso e controlla `docs/assets/logo.svg`.
2. **Soppressione orfani** — i file sotto `docs/it/` non vengono segnalati come orfani.

### `fallback_to_default`

**Default:** `true`

Rispecchia il flag `fallback_to_default` del plugin `mkdocs-i18n`. Quando `true`, un link da
una pagina tradotta a una pagina che esiste solo nel locale di default viene soppresso.

---

## Auto-rilevamento adapter

| `build_context.engine` | File di configurazione presente | Adapter selezionato |
| :--- | :--- | :--- |
| `"mkdocs"` (default) | `mkdocs.yml` trovato | `MkDocsAdapter` |
| `"mkdocs"` | `mkdocs.yml` assente, nessun locale | `VanillaAdapter` |
| `"zensical"` | `zensical.toml` trovato | `ZensicalAdapter` |
| `"zensical"` | `zensical.toml` assente | **Errore** |
| qualsiasi stringa sconosciuta | — | `VanillaAdapter` |

### Modalità Vanilla

Quando `VanillaAdapter` è selezionato, Zenzic non conosce la struttura della nav del progetto:

- **Il controllo orfani viene saltato** — senza una dichiarazione di nav, ogni file Markdown
  sembrerebbe un orfano.
- **Tutti gli altri controlli vengono eseguiti normalmente.**

---

## Flag `--engine` (override per singola esecuzione)

Il flag `--engine` su `zenzic check orphans` e `zenzic check all` sovrascrive
`build_context.engine` per una singola esecuzione:

```bash
zenzic check orphans --engine zensical
zenzic check all --engine mkdocs
```

Se passi un nome di engine senza adapter registrato, Zenzic elenca quelli disponibili ed esce
con codice 1.

---

## Adapter di terze parti

Gli adapter di terze parti si scoprono automaticamente una volta installati come pacchetti Python.
Si registrano sotto il gruppo di entry-point `zenzic.adapters`:

```toml
[project.entry-points."zenzic.adapters"]
hugo = "zenzic_hugo.adapter:HugoAdapter"
```

Consulta [Scrivere un Adapter](../../developers/writing-an-adapter.md) per il protocollo completo.
