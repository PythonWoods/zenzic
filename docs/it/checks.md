---
icon: lucide/shield-check
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Riferimento Controlli

Zenzic esegue sei controlli indipendenti. Ognuno affronta una categoria distinta di degrado della documentazione — la lenta deteriorazione che avviene quando un progetto cresce e la manutenzione della documentazione rimane indietro rispetto allo sviluppo.

<div class="grid cards" markdown>

- :lucide-link-2-off: &nbsp; __Link__

    Link interni non validi, ancore mancanti e URL esterni irraggiungibili.

    [`zenzic check links`](#link)

- :lucide-file: &nbsp; __Orfani__

    File `.md` presenti su disco ma assenti dalla navigazione del sito.

    [`zenzic check orphans`](#orfani)

- :lucide-code: &nbsp; __Snippet__

    Blocchi Python che non compilano — intercettati prima che i lettori li copino.

    [`zenzic check snippets`](#snippet)

- :lucide-pencil: &nbsp; __Placeholder__

    Pagine stub sotto la soglia di parole o con pattern vietati (es. `TODO`, `WIP`).

    [`zenzic check placeholders`](#placeholder)

- :lucide-image: &nbsp; __Asset__

    File media presenti su disco ma mai referenziati. __Supporta l'autofix.__

    [`check assets`](#asset) &nbsp;&bull;&nbsp; [`clean assets`](usage/commands.md#autofix-cleanup)

- :lucide-shield-check: &nbsp; __Riferimenti__

    Riferimenti pendenti, definizioni morte e credenziali trapelate (exit code 2).

    [`zenzic check references`](usage/advanced.md#integrita-dei-riferimenti-v020)

</div>

---

## Link

__CLI:__ `zenzic check links [--strict]`

Il link rot è uno dei fallimenti della documentazione più comuni e più visibili. Uno sviluppatore rinomina una pagina, sposta una sezione o elimina un'ancora, e i link che la puntavano diventano silenziosamente vicoli ciechi.

`zenzic check links` usa un parser Python nativo — nessun sottoprocesso, nessuna dipendenza dal motore di build. Scannerizza ogni file `.md` in `docs/`, estrae tutti i link Markdown con una state machine che ignora i blocchi di codice, e li valida in due livelli.

__Livello 1 — link interni (sempre verificati):__

I percorsi relativi e site-absolute vengono risolti contro la directory `docs/` in memoria. Il file target deve esistere nell'insieme dei file scansionati. Vengono risolti anche i percorsi senza estensione (`setup`) e i percorsi directory-index (`setup/`). Se il link include un `#frammento`, Zenzic estrae le ancore dalle intestazioni del file target e verifica la corrispondenza.

- `[testo](pagina-mancante.md)` → file target non trovato
- `[testo](pagina.md#ancora-mancante)` → ancora non trovata nel target

Tutti i file `.md` vengono letti una volta; le ancore vengono pre-calcolate dalle intestazioni (`# Titolo` → `#titolo`). Nessun I/O aggiuntivo per link.

__Livello 2 — link esterni (solo `--strict`):__

Con `--strict`, ogni URL `http://` e `https://` nei docs viene validato tramite richieste HTTP HEAD concorrenti usando `httpx`. Fino a 20 connessioni simultanee. I server che rifiutano HEAD ricevono un fallback GET. Lo stesso URL referenziato in più pagine viene pingato esattamente una volta.

I server che restituiscono `401`, `403` o `429` sono trattati come raggiungibili — indicano restrizioni di accesso, non link non validi. Timeout (>10 s) ed errori di connessione vengono segnalati come fallimenti.

__Cosa NON viene mai validato:__

- Link all'interno di blocchi di codice o span inline — il parser li ignora
- Schemi `mailto:`, `data:`, `ftp:`, `tel:` e simili
- Ancore pure della stessa pagina (`#sezione`) — non validate per default; abilitare con
  `validate_same_page_anchors = true` in `zenzic.toml` (vedi nota sotto)

__Flag `--strict`:__ senza `--strict`, vengono controllati solo i link interni (veloce, nessuna rete). Con `--strict`, vengono validati anche i link HTTP/HTTPS esterni tramite richieste di rete concorrenti.

__Validazione ancore nella stessa pagina:__ per default, i link come `[testo](#sezione)` che
puntano a un'intestazione nella stessa pagina non vengono validati. Questo è intenzionale —
gli ID delle ancore possono essere generati anche da attributi HTML, plugin personalizzati o
macro a build-time non visibili durante la scansione del sorgente. Per abilitare la
validazione delle ancore same-page basata sulle intestazioni:

```toml
# zenzic.toml
validate_same_page_anchors = true
```

Quando abilitato, ogni ancora `#frammento` in un link same-page viene verificata rispetto
alle intestazioni estratte dal file sorgente. Un link a uno slug di intestazione inesistente
viene segnalato come non valido.

__Perché:__ L'analisi a livello sorgente fornisce output riproducibile indipendente dal motore di build.

__Output di esempio:__

```text
BROKEN LINKS (3):
  index.md:12: 'setup.md' not found in docs
  guide.md:47: anchor '#installation' not found in 'setup.md'
  api.md:88: external link 'https://api.example.com/v2' returned HTTP 404
```

### Codici di violazione

Il controllo link utilizza la Virtual Site Map (VSM) per distinguere due categorie di fallimento:

| Codice | Severità | Significato |
| :--- | :---: | :--- |
| `Z001` | error | __Link rotto__ — il target non esiste nella VSM. Il file manca o l'URL è errato. |
| `Z002` | warning | __Link a orfano__ — il target esiste su disco ma non è nella navigazione del sito. I lettori non possono raggiungere la pagina tramite il nav. |

`Z001` blocca sempre la pipeline (exit code 1). `Z002` è un warning — appare nel report ma non fa fallire la CI a meno che non venga passato `--strict`. Questa distinzione permette ai team di intercettare subito le rotture reali, gestendo l'igiene della navigazione come preoccupazione separata.

__Perché i link ad orfani contano:__ un link a una pagina orfana _funziona_ a livello di filesystem — il file esiste e il motore di build potrebbe servirlo. Ma la pagina è invisibile nel nav tree, creando un'esperienza utente frammentata. I lettori che seguono il link atterrano su una pagina senza contesto nella sidebar e senza modo di navigare indietro. `Z002` intercetta questo anti-pattern.

__Output di esempio con Z002:__

```text
WARNINGS (1):
  [Z002] guide/tips.md:18 — 'drafts/experiment.md' esiste su disco ma non è nella navigazione del sito (ORPHAN_LINK).
    │ See [experiment](drafts/experiment.md) for details.
```

---

## Orfani

__CLI:__ `zenzic check orphans`

Una pagina orfana esiste su disco ma non è elencata nella navigazione del sito. È invisibile ai lettori che seguono il nav — può essere raggiunta solo indovinando l'URL o trovando un link diretto. Le pagine orfane vengono tipicamente create quando una pagina viene aggiunta durante lo sviluppo ma la sua voce nav viene dimenticata, o quando una voce nav viene rimossa senza eliminare il file corrispondente.

__Comportamento CLI:__ scannerizza `docs_dir` per tutti i file `.md`, analizza la `nav` da `mkdocs.yml` o `zensical.toml`, e segnala la differenza tra insiemi. Le directory elencate in `excluded_dirs` (default: `includes`, `assets`, `stylesheets`, `overrides`, `hooks`) vengono saltate completamente. I symlink vengono ignorati.

__Cosa rileva:__

- Pagine create su disco ma mai aggiunte alla `nav`
- Pagine la cui voce `nav` è stata rimossa senza eliminare il file

__Output di esempio:__

```text
ORPHANS (2):
  api/experimental.md
  guides/draft-tutorial.md
```

---

## Snippet

__CLI:__ `zenzic check snippets`

Gli esempi di codice nella documentazione vengono testati meno rigorosamente del codice in produzione. Un snippet che funzionava quando è stato scritto potrebbe avere un errore di sintassi introdotto da un refactoring, un errore di copia-incolla o una modifica manuale mai revisionata. I lettori che copiano codice rotto perdono tempo a fare debug di errori che non c'entrano nulla con il loro problema reale.

`zenzic check snippets` valida la sintassi dei blocchi di codice delimitati usando parser puri in Python — nessun sottoprocesso viene avviato per nessun linguaggio.

__Linguaggi supportati:__

| Tag linguaggio | Parser | Cosa viene controllato |
| :--- | :--- | :--- |
| `` python ``, `` py `` | `compile()` in modalità `exec` | Sintassi Python 3.11+ |
| `` yaml ``, `` yml `` | `yaml.safe_load()` | Struttura YAML 1.1 |
| `` json `` | `json.loads()` | Sintassi JSON |
| `` toml `` | `tomllib.loads()` (stdlib 3.11+) | Sintassi TOML v1.0 |

I blocchi con qualsiasi altro tag (`` bash ``, `` javascript ``, `` mermaid ``, ecc.) vengono trattati come testo semplice e non vengono controllati sintatticamente. Tuttavia, __ogni blocco delimitato viene comunque scansionato dallo Zenzic Shield__ per i pattern di credenziali — la validazione sintattica e la scansione di sicurezza sono indipendenti.

__Comportamento CLI:__ percorre `docs_dir`, legge ogni file `.md` e chiama `check_snippet_content(text, file_path, config)` sul contenuto grezzo.

__Estrazione dei blocchi:__ Zenzic usa una macchina a stati deterministica riga per riga invece di una regex per estrarre i blocchi di codice. Questo previene falsi positivi dagli inline code span (es., `` ` ```python ` `` nel testo) ed è robusto rispetto ai documenti `pymdownx.superfences` con fence Mermaid o altri fence personalizzati intercalati. Vedi [Architettura — Parsing a macchina a stati](architecture.md#parsing-a-macchina-a-stati-e-falsi-positivi-da-superfences) per i dettagli.

__Cosa rileva:__

- Python: `SyntaxError` — due punti mancanti, parentesi non bilanciate, espressioni non valide; crash del parser (`MemoryError`, `RecursionError`)
- YAML: errori strutturali — sequenze non chiuse, mapping non validi, chiavi duplicate
- JSON: `JSONDecodeError` — virgole finali, virgolette mancanti, parentesi non bilanciate
- TOML: `TOMLDecodeError` — virgolette mancanti sui valori, sintassi chiave non valida, mismatch di tipo

__Cosa NON rileva:__

- Errori runtime (`NameError`, `TypeError`, `ImportError`, ecc.) — viene controllata solo la sintassi
- Snippet intenzionalmente incompleti — frammenti, stub con ellissi, pseudo-codice
- Bash, JavaScript o qualsiasi altro linguaggio senza un parser puro in Python

__Tuning:__ usa `snippet_min_lines` in `zenzic.toml` per saltare i blocchi brevi. Il default di `1` controlla tutto inclusi i blocchi su una singola riga. Impostalo a `3` o superiore per ignorare stub di import e one-liner che sono probabilmente illustrativi piuttosto che eseguibili.

__Output di esempio:__

```text
INVALID SNIPPETS (3):
  tutorial.md:48 - SyntaxError in Python snippet — expected ':'
  config/reference.md:22 - SyntaxError in YAML snippet — mapping values are not allowed here
  api/reference.md:112 - SyntaxError in JSON snippet — Expecting property name enclosed in double quotes
```

---

## Placeholder

__CLI:__ `zenzic check placeholders`

Le pagine placeholder sono pagine create come stub e mai completate. Appaiono nella nav e nei risultati di ricerca, ma non contengono nulla di utile.

`zenzic check placeholders` applica due segnali indipendenti per rilevare contenuto non completato.

__Segnale 1 — conteggio parole:__ le pagine con meno di `placeholder_max_words` parole (default: 50) vengono segnalate come `short-content`. Il conteggio parole è calcolato dividendo il sorgente Markdown grezzo sugli spazi bianchi e include intestazioni, testo dei link e contenuto dei blocchi di codice.

__Segnale 2 — corrispondenza pattern:__ le righe contenenti qualsiasi stringa da `placeholder_patterns` (case-insensitive, default: `coming soon`, `work in progress`, `wip`, `todo`, `to do`, `stub`, `placeholder`, `fixme`, `tbd`, `to be written`, `to be completed`, `to be added`, `under construction`, `not yet written`, `draft`, `da completare`, `in costruzione`, `in lavorazione`, `da scrivere`, `da aggiungere`, `bozza`, `prossimamente`) vengono segnalate come `placeholder-text`. La corrispondenza viene eseguita riga per riga sul sorgente Markdown grezzo.

Entrambi i segnali sono indipendenti. Una pagina può attivarne uno, entrambi, o nessuno.

__Comportamento CLI:__ legge ogni file `.md` e chiama `check_placeholder_content(text, file_path, config)`.

__Tuning:__

```text
# zenzic.toml

# Alza la soglia per progetti con pagine dense e concise
placeholder_max_words = 100

# Personalizza i pattern per le convenzioni del tuo team
placeholder_patterns = ["coming soon", "wip", "fixme", "tbd", "draft"]

# Disabilita il controllo del conteggio parole (il controllo pattern continua)
placeholder_max_words = 0

# Disabilita entrambi i controlli
placeholder_max_words = 0
placeholder_patterns = []
```

__Output di esempio:__

```text
PLACEHOLDERS/STUBS (3):
  guides/advanced.md:1 [short-content] - Page has only 12 words (minimum 50).
  api/webhooks.md:7 [placeholder-text] - Found placeholder text matching pattern: 'coming soon'
```

---

## Asset

__CLI:__

- `zenzic check assets` — Controlla la presenza di file non utilizzati.
- `zenzic clean assets` — Rimuove in modo sicuro gli asset non utilizzati.

!!! tip "Autofix disponibile"
    Usa `zenzic clean assets` per eliminare automaticamente gli asset non utilizzati trovati da questo controllo. Ti verrà chiesto di confermare l'eliminazione (`[y/N]`), oppure puoi passare `-y` per saltare il prompt. Usa `--dry-run` per visualizzare i file che verrebbero eliminati senza cancellarli realmente. Zenzic non eliminerà mai i file che corrispondono ai pattern `excluded_assets`, `excluded_dirs` o `excluded_build_artifacts`.

Gli asset non utilizzati sono file che esistono nella directory sorgente della documentazione ma non sono mai referenziati da nessuna pagina. Tipicamente sono residui dopo che una pagina viene rinominata o un'immagine viene sostituita. Non causano errori visibili, ma si accumulano nel tempo e appesantiscono il sito compilato.

__Cosa conta come "usato":__ un asset è considerato usato se appare come link immagine Markdown (`![alt](percorso)`) o tag HTML `<img src="...">` in qualsiasi file `.md`. I percorsi vengono normalizzati usando l'aritmetica dei percorsi POSIX in modo che i riferimenti relativi come `../assets/logo.png` da una sottodirectory si risolvano correttamente in `assets/logo.png` relativo alla root dei docs.

__Sempre esclusi dal controllo:__ i file `.css`, `.js`, `.yml` sono sempre considerati intenzionalmente presenti e non vengono mai segnalati come non utilizzati, anche se nessuna pagina li linka. Sono tipicamente override del tema o file di configurazione della build.

__Comportamento CLI:__

1. Raccoglie tutti i file non-`.md` e non-esclusi da `docs_dir` ricorsivamente
2. Legge ogni file `.md` ed estrae i percorsi degli asset referenziati tramite `check_asset_references(text, page_dir)`
3. Segnala `calculate_unused_assets(all_assets, used_assets)` — la differenza tra insiemi

__Cosa rileva:__

- Screenshot caricati ma mai incorporati in nessuna pagina
- Immagini rimaste dopo una riorganizzazione o rinomina di una pagina
- Allegati (PDF, file di dati) che erano linkati da una pagina che non esiste più

__Output di esempio:__

```text
UNUSED ASSETS (3):
  assets/old-screenshot.png
  assets/diagram-v1.svg
  attachments/deprecated-spec.pdf
```
