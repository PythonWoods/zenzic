---
icon: lucide/settings
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Riferimento Configurazione

Zenzic legge un singolo file `zenzic.toml` nella root del repository. Tutti i campi sono
opzionali — Zenzic funziona senza alcun file di configurazione.

!!! tip "Configurazione zero"

    La maggior parte dei progetti non ha bisogno di alcun `zenzic.toml`. Esegui
    `uvx zenzic check all` — se passa, hai finito. Aggiungi configurazione solo quando
    devi personalizzare un comportamento specifico.

---

## Per iniziare

Per la maggior parte dei progetti non è necessario alcun file di configurazione. Esegui
`zenzic check all` e Zenzic individuerà la root del repository tramite `.git` o `zenzic.toml`
e applicherà valori predefiniti ragionevoli. Se non viene trovato alcun `zenzic.toml`, Zenzic
mostra un pannello "Helpful Hint" che suggerisce `zenzic init`.

Usa `zenzic init` per scaffoldare il file automaticamente. Rileva il motore di documentazione
dalla root del progetto (es. `mkdocs.yml`) e preimposta `engine` in `[build_context]`:

```bash
zenzic init          # crea zenzic.toml con engine rilevato
zenzic init --force  # sovrascrive un file esistente
```

Crea o modifica `zenzic.toml` nella root del repository quando hai bisogno di personalizzare il
comportamento:

```toml
# zenzic.toml — punto di partenza minimo

# docs_dir = "docs"
# excluded_dirs = ["includes", "assets", "stylesheets", "overrides", "hooks"]
# excluded_assets = []
# snippet_min_lines = 1
# placeholder_max_words = 50

# [build_context]
# engine         = "mkdocs"
# default_locale = "en"
# locales        = ["it"]
```

---

## Sezioni di riferimento

| Pagina | Contenuto |
| :--- | :--- |
| [Impostazioni di Base](core-settings.md) | `docs_dir`, liste di esclusione, soglie, punteggio |
| [Adapter e Motore](adapters-config.md) | `build_context`, auto-rilevamento adapter, override `--engine` |
| [DSL Regole Custom](custom-rules-dsl.md) | `[[custom_rules]]` — regole lint personalizzate in puro TOML |

---

## Esempio completo

```toml
docs_dir = "docs"
excluded_dirs  = ["includes", "assets", "stylesheets", "overrides", "hooks"]
excluded_assets = []
excluded_build_artifacts = []
snippet_min_lines = 1
placeholder_max_words = 50
placeholder_patterns = ["coming soon", "wip", "todo", "stub", "draft", "da completare", "bozza"]
validate_same_page_anchors = false
excluded_external_urls = []
fail_under = 80

[[custom_rules]]
id       = "ZZ-NODRAFT"
pattern  = "(?i)\\bDRAFT\\b"
message  = "Rimuovere il marker DRAFT prima della pubblicazione."
severity = "warning"

[build_context]
engine         = "mkdocs"
default_locale = "en"
locales        = ["it"]
```

---

## Caricamento della configurazione

Zenzic legge `zenzic.toml` dalla root del repository all'avvio. La root viene individuata
risalendo dalla directory di lavoro corrente fino a trovare una directory `.git` o un file
`zenzic.toml`.

Se `zenzic.toml` è assente, vengono applicati silenziosamente tutti i valori predefiniti. Se
`zenzic.toml` è presente ma contiene un **errore di sintassi TOML**, Zenzic solleva un
`ConfigurationError` con un messaggio leggibile ed esce immediatamente. I campi sconosciuti
vengono ignorati silenziosamente.
