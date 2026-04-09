---
icon: lucide/blocks
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Guida alla Configurazione dei Motori

Zenzic è **agnostico** — funziona con MkDocs, Zensical o una semplice cartella di file
Markdown senza richiedere l'installazione di alcun framework di build. È anche **opinato**:
quando dichiari un motore, devi dimostrarlo. Questa guida spiega come configurare Zenzic
per ogni motore supportato e quali sono le regole.

## Portata multi-ecosistema

Zenzic è uno strumento Python, ma la sua portata non è limitata all'ecosistema Python della
documentazione. Poiché Zenzic analizza **file Markdown sorgente e configurazione come dati
semplici** — senza mai invocare un motore di build, senza mai importare codice di framework
— può validare la documentazione di qualsiasi generatore di siti statici (SSG),
indipendentemente dal linguaggio in cui è scritto.

| Livello di supporto | Motore | Linguaggio SSG | Come |
| :--- | :--- | :--- | :--- |
| **Nativo** | MkDocs | Python | `MkDocsAdapter` — legge `mkdocs.yml`, risolve i18n, impone la nav |
| **Nativo** | Zensical | Python | `ZensicalAdapter` — legge `zensical.toml`, zero YAML |
| **Agnostico** | Vanilla | qualsiasi | `VanillaAdapter` — funziona su qualsiasi cartella Markdown; controllo orphan disabilitato |
| **Estensibile** | Hugo *(esempio)* | Go | Adapter di terze parti via entry-point `zenzic.adapters` |
| **Estensibile** | Docusaurus *(esempio)* | Node.js | Adapter di terze parti via entry-point `zenzic.adapters` |
| **Estensibile** | Jekyll *(esempio)* | Ruby | Adapter di terze parti via entry-point `zenzic.adapters` |

Le voci "Estensibile" sono esempi di ciò che il sistema di adapter rende possibile — non
adapter già distribuiti. Un team che gestisce documentazione Hugo, Docusaurus o Jekyll può
scrivere un pacchetto adapter di terze parti e installarlo accanto a Zenzic senza alcuna
modifica a Zenzic stesso:

```bash
# Esempio: adapter di terze parti per un ipotetico supporto Hugo
uv pip install zenzic-hugo-adapter   # oppure: pip install zenzic-hugo-adapter
zenzic check all --engine hugo
```

Questa portata multi-linguaggio è una proprietà strutturale, non una promessa di roadmap.
Il protocollo Adapter definisce cinque metodi; qualsiasi pacchetto Python che li implementa
e si registra sotto il gruppo entry-point `zenzic.adapters` è un adapter Zenzic valido —
per qualsiasi SSG.

---

## Scegliere un motore

La sezione `[build_context]` in `zenzic.toml` indica a Zenzic quale motore utilizza il tuo
progetto:

```toml
# zenzic.toml
[build_context]
engine = "mkdocs"   # oppure "zensical"
```

Se `[build_context]` è assente, Zenzic rileva automaticamente:

- `mkdocs.yml` presente → `MkDocsAdapter`
- nessuna configurazione presente, nessun locale dichiarato → `VanillaAdapter` (controllo orphan disabilitato)

!!! abstract "Ponte CLI — Controlli signal-to-noise"
  Selezione engine e verbosità Sentinel sono concern separati. Usa
  [Comandi CLI: Flag globali](../usage/commands.md#flag-globali) per calibrare la policy per run:

  1. `--strict` per elevare warning e imporre validazione URL esterni.
  2. `--exit-zero` per run osservativi non bloccanti.
  3. `--show-info` per ispezionare finding informativi di topologia.
  4. `--quiet` per output CI/pre-commit a riga singola.

---

## MkDocs

`MkDocsAdapter` viene selezionato quando `engine = "mkdocs"` (o qualsiasi stringa motore
non riconosciuta). Legge `mkdocs.yml` usando un loader YAML permissivo che ignora
silenziosamente i tag sconosciuti (come l'interpolazione `!ENV` di MkDocs), quindi le
configurazioni con molte variabili d'ambiente funzionano senza alcuna pre-elaborazione.

### Limiti dell'analisi statica

`MkDocsAdapter` analizza `mkdocs.yml` come **dati statici**. Non esegue la pipeline di
build di MkDocs. Questo significa:

- **Tag `!ENV`** — trattati silenziosamente come `null`. Se la nav dipende da
  interpolazione di variabili d'ambiente a runtime, le voci nav che dipendono da quei
  valori saranno assenti dalla visione di Zenzic.
- **Nav generata dai plugin** — plugin che mutano la nav a runtime (es.
  `mkdocs-awesome-pages`, `mkdocs-literate-nav`) producono un albero di navigazione
  che Zenzic non vede mai. Le pagine incluse solo da questi plugin vengono segnalate
  come orfane.
- **Macro** — `mkdocs-macros-plugin` (template Jinja2 in Markdown) non viene
  valutato. I link all'interno di espressioni macro non vengono validati.

Per progetti che dipendono fortemente dalla generazione dinamica della nav, aggiungi i
percorsi generati dai plugin a `excluded_dirs` in `zenzic.toml` per sopprimere i falsi
positivi sugli orfani finché non sarà disponibile un adapter nativo.

### Configurazione minima

```toml
# zenzic.toml
docs_dir = "docs"

[build_context]
engine         = "mkdocs"
default_locale = "en"
locales        = ["it", "fr"]   # nomi delle directory locale non predefinite (folder mode)
```

Quando `locales` è vuoto, Zenzic si ricade a leggere le informazioni sui locale direttamente
dal blocco del plugin `mkdocs-static-i18n` in `mkdocs.yml` — zero configurazione richiesta
per la maggior parte dei progetti.

### i18n: Folder Mode

In Folder Mode (`docs_structure: folder`), ogni locale non predefinito vive in una directory
di primo livello sotto `docs/`:

```text
docs/
  index.md          ← locale predefinito
  assets/
    logo.png        ← asset condiviso
  it/
    index.md        ← traduzione italiana
```

Zenzic legge la lista `languages` da `mkdocs.yml` per identificare le directory locale. I
file il cui primo componente del percorso è una directory locale vengono esclusi dal controllo
orphan — ereditano la loro appartenenza alla nav dall'originale nel locale predefinito.

Quando `fallback_to_default: true` è impostato, i link agli asset da `docs/it/index.md` che
si risolvono a `docs/it/assets/logo.png` (assente) vengono automaticamente ricontrollati
rispetto a `docs/assets/logo.png`, specchiando il comportamento di fallback effettivo del
motore di build.

```yaml
# mkdocs.yml
plugins:
  - i18n:
      docs_structure: folder
      fallback_to_default: true
      languages:
        - locale: en
          default: true
          build: true
        - locale: it
          build: true
```

> **Regola:** Se `fallback_to_default: true` è impostato, almeno una voce lingua deve avere
> `default: true`. Se nessuna lo ha, Zenzic lancia `ConfigurationError` immediatamente — non
> può determinare il locale di destinazione del fallback.

### i18n: Suffix Mode

In Suffix Mode (`docs_structure: suffix`), i file tradotti sono fratelli degli originali:

```text
docs/
  guide.md        ← locale predefinito
  guide.it.md     ← traduzione italiana (stessa profondità di directory)
  assets/
    logo.png      ← stesso percorso relativo da entrambi i file
```

Zenzic legge i codici locale non predefiniti da `mkdocs.yml` e genera pattern di esclusione
`*.{locale}.md` (es. `*.it.md`, `*.fr.md`). Questi file vengono esclusi dal controllo orphan.

Solo i codici ISO 639-1 validi di due lettere minuscole producono pattern di esclusione. I
tag di versione (`v1`, `v2`), tag di build (`beta`, `rc1`), codici a tre lettere e codici
BCP 47 con regione vengono rifiutati silenziosamente — non producono esclusioni false.

---

## Zensical

`ZensicalAdapter` viene selezionato quando `engine = "zensical"`. Legge `zensical.toml`
nativamente usando `tomllib` di Python — **zero YAML**. Nessun `mkdocs.yml` viene letto
né richiesto.

### Native Enforcement

```toml
# zenzic.toml
[build_context]
engine = "zensical"
```

Se `zensical.toml` è **assente** quando `engine = "zensical"` è dichiarato, Zenzic lancia
`ConfigurationError` immediatamente:

```text
ConfigurationError: engine 'zensical' declared in zenzic.toml but zensical.toml is missing
hint: create zensical.toml or set engine = 'mkdocs' for MkDocs projects
```

Non esiste fallback. Non esiste degradazione silenziosa. L'identità del motore deve essere
dimostrabile dai file presenti su disco.

### Formato nav di zensical.toml

Zenzic legge la sezione `[nav]` per determinare quali pagine sono dichiarate:

```toml
# zensical.toml
[project]
site_name = "La Mia Documentazione"

[nav]
nav = [
  {title = "Home",      file = "index.md"},
  {title = "Tutorial",  file = "tutorial.md"},
  {title = "API",       file = "reference/api.md"},
]
```

I file elencati sotto `file` (relativi a `docs/`) costituiscono il set della nav. Qualsiasi
file `.md` sotto `docs/` che non è in questo set e non è un mirror locale viene segnalato
come orphan.

### Perché Zensical elimina la complessità dell'i18n

L'i18n di MkDocs si basa su un plugin (`mkdocs-static-i18n`) con la propria configurazione
YAML, switch `docs_structure`, logica `fallback_to_default` e liste `languages`. Zensical
definisce la semantica i18n nativamente in `zensical.toml` senza indirezione di plugin.
Il risultato:

- Nessun YAML da analizzare per il rilevamento dei locale
- Nessuna ambiguità `fallback_to_default`
- Nessuna euristica "quale blocco plugin si applica?"
- `ConfigurationError` è impossibile per i18n mal configurato — lo schema TOML è esplicito

---

## Divieto di Link Assoluti

**Questa regola si applica a ogni motore, incondizionatamente.**

I link che iniziano con `/` sono un errore bloccante in tutte le modalità motore:

```markdown
<!-- Rifiutato — il percorso assoluto rompe la portabilità -->
[Scarica](/assets/guide.pdf)

<!-- Corretto — il percorso relativo sopravvive a qualsiasi prefisso di hosting -->
[Scarica](../assets/guide.pdf)
```

Un link a `/assets/guide.pdf` presuppone che il sito sia servito dalla root del dominio.
Quando la documentazione è ospitata su `https://example.com/docs/`, il browser risolve
`/assets/guide.pdf` in `https://example.com/assets/guide.pdf` — un 404. La correzione è
sempre un percorso relativo.

Il controllo viene eseguito prima di qualsiasi logica dell'adapter — prima del parsing della
nav, prima del rilevamento dei locale, prima della risoluzione dei percorsi. Non può essere
soppresso dalla configurazione del motore.

Gli URL esterni (`https://...`, `http://...`) non sono interessati.

---

## Vanilla (nessun motore)

`VanillaAdapter` viene restituito quando non è presente alcun file di configurazione del
motore e non sono dichiarati locale. Tutti i metodi dell'adapter sono no-op:

- `is_locale_dir` → sempre `False`
- `resolve_asset` → sempre `None`
- `is_shadow_of_nav_page` → sempre `False`
- `get_nav_paths` → `frozenset()`
- `get_ignored_patterns` → `set()`

`find_orphans` restituisce `[]` immediatamente — senza una nav, non c'è un insieme di
riferimento con cui confrontarsi. I controlli snippet, placeholder, link e asset vengono
comunque eseguiti normalmente.

Questo significa che Zenzic funziona out-of-the-box con qualsiasi altro sistema basato su
Markdown senza produrre falsi positivi.
