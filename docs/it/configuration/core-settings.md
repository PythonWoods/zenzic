---
icon: lucide/sliders-horizontal
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Impostazioni di Base

Tutti i campi di primo livello in `zenzic.toml` che controllano percorsi, soglie e punteggio.

---

## `docs_dir`

**Tipo:** stringa (percorso) — **Default:** `"docs"`

Percorso alla directory sorgente della documentazione, relativo alla root del repository.

```toml
docs_dir = "documentation"
```

---

## `excluded_dirs`

**Tipo:** lista di stringhe — **Default:** `["includes", "assets", "stylesheets", "overrides", "hooks"]`

Nomi di directory (non percorsi completi) all'interno di `docs_dir` escluse da tutti i controlli.

```toml
excluded_dirs = ["includes", "assets", "partials", "_templates"]
```

---

## `excluded_assets`

**Tipo:** lista di stringhe — **Default:** `[]`

Percorsi di asset (relativi a `docs_dir`) esclusi dal controllo asset non utilizzati. Per i file
referenziati da `mkdocs.yml` o dai template del tema piuttosto che da qualsiasi pagina Markdown.

```toml
excluded_assets = [
    "assets/favicon.svg",
    "assets/social-preview.png",
]
```

---

## `excluded_asset_dirs`

**Tipo:** lista di stringhe — **Default:** `["overrides"]`

Directory all'interno di `docs_dir` i cui file non-Markdown vengono esclusi dal controllo asset
non utilizzati.

```toml
excluded_asset_dirs = ["overrides", "_theme"]
```

---

## `excluded_file_patterns`

**Tipo:** lista di stringhe — **Default:** `[]`

Pattern glob sui nomi dei file esclusi dal controllo orfani. Per i progetti `mkdocs-i18n` con
`docs_structure: suffix`, non è necessaria alcuna configurazione — Zenzic rileva automaticamente
i locale non-default.

```toml
excluded_file_patterns = ["*.locale.md", "*_draft.md"]
```

---

## `excluded_build_artifacts`

**Tipo:** lista di stringhe (pattern glob) — **Default:** `[]`

Pattern glob per asset generati in fase di build. I link corrispondenti non vengono segnalati
come non raggiungibili anche quando il file non esiste al momento del lint.

```toml
excluded_build_artifacts = [
    "pdf/*.pdf",
    "assets/bundle.zip",
]
```

---

## `excluded_external_urls`

**Tipo:** lista di stringhe — **Default:** `[]`

Prefissi URL esclusi dal controllo dei link esterni non raggiungibili.

```toml
excluded_external_urls = [
    "https://github.com/MyOrg/my-library",
    "https://pypi.org/project/my-library/",
]
```

---

## `snippet_min_lines`

**Tipo:** intero — **Default:** `1`

Numero minimo di righe che un blocco di codice Python delimitato deve contenere per essere
controllato sintatticamente.

```toml
snippet_min_lines = 3
```

---

## `placeholder_max_words`

**Tipo:** intero — **Default:** `50`

Le pagine con meno parole di questa soglia vengono segnalate come `short-content`. Imposta a `0`
per disabilitare il segnale di conteggio parole.

```toml
placeholder_max_words = 100
```

---

## `placeholder_patterns`

**Tipo:** lista di stringhe — **Default:** `["coming soon", "work in progress", "wip", "todo", "to do", "stub", "placeholder", "fixme", "tbd", "to be written", "to be completed", "to be added", "under construction", "not yet written", "draft", "da completare", "in costruzione", "in lavorazione", "da scrivere", "da aggiungere", "bozza", "prossimamente"]`

Stringhe case-insensitive che segnalano la pagina come `placeholder-text` quando trovate in
una riga.

```toml
placeholder_patterns = ["coming soon", "wip", "fixme", "tbd", "draft"]
```

---

## `validate_same_page_anchors`

**Tipo:** booleano — **Default:** `false`

Quando `true`, valida i link con ancora nella stessa pagina rispetto ai titoli estratti dal file
sorgente.

```toml
validate_same_page_anchors = true
```

---

## `fail_under`

**Tipo:** intero — **Default:** `0`

Punteggio di qualità minimo (0–100). Se `zenzic score` produce un punteggio inferiore a questo
valore, il comando termina con codice di uscita 1.

```toml
fail_under = 80
```
