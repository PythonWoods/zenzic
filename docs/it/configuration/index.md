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

Zenzic segue una catena di priorità a tre livelli (**Cittadino Agnostico**) quando cerca la
configurazione all'avvio:

| Priorità | Sorgente | Quando viene usata |
| :---: | :--- | :--- |
| 1 | `zenzic.toml` nella root del repository | Sempre preferita — la configurazione sovrana |
| 2 | `[tool.zenzic]` in `pyproject.toml` | Usata solo quando `zenzic.toml` è assente |
| 3 | Valori predefiniti interni | Usati quando nessun file è presente |

La root del repository viene individuata risalendo dalla directory di lavoro corrente fino a
trovare una directory `.git`, un file `zenzic.toml` o un `pyproject.toml`.

### zenzic.toml (Priorità 1)

Il file di configurazione dedicato. Se esiste, Zenzic lo legge e ignora completamente
`pyproject.toml` — non c'è nessuna fusione tra i due file.

### pyproject.toml (Priorità 2) — v0.5.0a1

I progetti Python che hanno già un `pyproject.toml` possono incorporare la configurazione di
Zenzic nella tabella `[tool.zenzic]`, eliminando la necessità di un file separato:

```toml
# pyproject.toml — configurazione Zenzic nel file di metadati Python standard

[tool.zenzic]
docs_dir   = "docs"
fail_under = 90

[tool.zenzic.build_context]
engine = "mkdocs"

[[tool.zenzic.custom_rules]]
id       = "ZZ-NODRAFT"
pattern  = "(?i)\\bDRAFT\\b"
message  = "Rimuovere il marker DRAFT prima della pubblicazione."
severity = "warning"
```

Tutti i campi supportati in `zenzic.toml` sono ugualmente supportati in `[tool.zenzic]`. La
sotto-tabella `[build_context]` diventa `[tool.zenzic.build_context]`, e gli array `[[custom_rules]]`
diventano `[[tool.zenzic.custom_rules]]`.

!!! note "Regola della sovranità"
    Se sia `zenzic.toml` **che** `pyproject.toml` esistono nella root del repository,
    `zenzic.toml` vince incondizionatamente. La tabella `[tool.zenzic]` in `pyproject.toml`
    viene ignorata.

### Gestione degli errori

Se il file di configurazione vincitore contiene un **errore di sintassi TOML**, Zenzic solleva un
`ConfigurationError` con un messaggio leggibile ed esce immediatamente — il fallback silenzioso
su un file di configurazione non valido nasconderebbe gli errori. I campi sconosciuti vengono
ignorati silenziosamente.
