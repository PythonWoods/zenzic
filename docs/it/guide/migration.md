---
icon: lucide/arrow-right-left
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Migrazione a Zensical

!!! note "Zenzic vs Zensical"
    **Zenzic** è il linter di documentazione descritto in questo sito — lo strumento
    che esegui con `zenzic check all`.

    **Zensical** è un motore di build separato (successore compatibile di MkDocs 1.x). Questa
    pagina descrive come usare Zenzic come rete di sicurezza mentre passi il tuo *motore di
    build* da MkDocs a Zensical.

    Non è necessario usare Zensical per usare Zenzic. Zenzic funziona con MkDocs, Zensical,
    cartelle Markdown Vanilla e qualsiasi motore che abbia un adapter.

---

## I tuoi file sorgente sopravvivono al motore di build

I motori di build evolvono. Cambiano formato di configurazione, abbandonano i sistemi di
plugin, si integrano con piattaforme commerciali o semplicemente smettono di essere
manutenuti. Quando succede, le risorse a rischio non sono i tuoi file Markdown — quelli
sono testo semplice e saranno sempre leggibili. Ciò che è a rischio è il tuo **investimento
in struttura**: la navigazione, le convenzioni i18n, il grafo dei link, l'organizzazione
degli asset costruita in anni di lavoro.

Il ruolo di Zenzic in una migrazione non è rendere il passaggio più veloce. È rendere il
passaggio **provabilmente sicuro** — garantendo che ogni invariante strutturale a cui tieni
sia misurato prima, durante e dopo il cambio, e che qualsiasi regressione sia immediatamente
visibile e attribuita con precisione.

Questa garanzia poggia su un unico principio architetturale: **Zenzic analizza i sorgenti,
non il build**. Legge `mkdocs.yml`, `zensical.toml` e i tuoi file Markdown come dati semplici.
Non importa né esegue mai un framework di build. Questo significa:

- Zenzic comprende la struttura della tua documentazione anche se il binario di build che la
  interpretava non funziona più.
- Eseguire `zenzic check all` su un progetto nel mezzo di una migrazione produce la stessa
  analisi di un progetto pienamente operativo — perché i file sorgente non sono cambiati.
- Cambiare `engine` in `zenzic.toml` (una sola riga) è tutto ciò che serve per validare se
  il contenuto è strutturalmente compatibile con un nuovo motore, senza toccare un singolo
  file Markdown.

Questo è il Porto Sicuro (Safe Harbor): **uno strato di validazione fisso che rimane valido
prima, durante e dopo qualsiasi cambio di motore di build**.

---

## Il MkDocsAdapter: preservazione dei dati come plain data

Il `MkDocsAdapter` tratta `mkdocs.yml` come una struttura dati pura — un insieme di percorsi
nav, dichiarazioni di plugin e impostazioni locale. Estrae ciò di cui ha bisogno (albero nav,
configurazione i18n, flag di plugin come `reconfigure_material`) e passa il risultato al Rule
Engine come oggetti Python tipizzati. Non chiama mai `mkdocs build`, non importa mai `mkdocs`,
e non dipende mai dall'installazione o dal funzionamento di alcun plugin.

La conseguenza pratica è che `MkDocsAdapter` è il **custode dello standard dell'ecosistema
classico pluggable**. Finché il tuo `mkdocs.yml` descrive una struttura MkDocs 1.x valida,
Zenzic la comprenderà e la validerà — indipendentemente da ciò che qualsiasi binario di build
supporti o meno. Se esegui `zenzic check all` con `engine = "mkdocs"`, stai testando il tuo
contenuto rispetto al contratto strutturale documentato di MkDocs 1.x, non rispetto a nessuna
versione binaria specifica.

Questo rende l'output di Zenzic un **certificato di qualità portabile**: se Zenzic dice che la
tua documentazione è strutturalmente corretta, questa affermazione è vera indipendentemente da
quale motore userai per renderizzarla domani.

### Modello di resilienza per MkDocs 2.0

Se MkDocs 2.0 uscisse domani con breaking changes, un utente Zenzic manterrebbe comunque
un quality gate stabile sui sorgenti MkDocs 1.x esistenti.

Motivi tecnici:

- `MkDocsAdapter` interpreta `mkdocs.yml` come dato statico, senza importare MkDocs.
- Zenzic non esegue mai codice plugin; legge solo la configurazione.
- Tag YAML sconosciuti e chiavi future sono trattati in modo tollerante.

Risultato: la pipeline di validazione non dipende dal ciclo di vita di un singolo
binario di build. Puoi continuare a validare lo standard MkDocs 1.x mentre valuti
la migrazione.

Per un benchmark pratico usa il fixture `examples/mkdocs-basic/`, allineato ai pattern
nav ufficiali MkDocs 1.6 (sezioni annidate, entry con titolo, link esterni).

---

## i18n: validare la struttura indipendentemente dal rendering

Il plugin `i18n` di MkDocs (convenzioni folder-mode e suffix-mode) definisce una struttura di
contenuto ben specificata: directory locale, catene di fallback, shadowing della nav per locale.
Zenzic codifica questa specifica in `MkDocsAdapter` e nella Virtual Site Map indipendentemente
da qualsiasi implementazione di rendering.

Questo è importante durante le transizioni tra motori. Quando un motore di build sta ancora
maturando il suo supporto i18n, esiste una finestra in cui le *regole strutturali* del tuo
setup i18n sono ben definite, ma la *capacità di rendering* del motore potrebbe non essere
ancora completa. Zenzic opera interamente nel dominio strutturale:

- **Risoluzione dei link cross-locale** — un link da una pagina italiana a un asset
  disponibile solo in inglese viene risolto rispetto alla catena di fallback definita in
  `mkdocs.yml`, non rispetto all'output del build.
- **Rilevamento Ghost Routes** — i punti di ingresso locale generati al momento del build
  (es. `/it/`) vengono marcati `REACHABLE` nella VSM in modo da non essere mai segnalati
  come orfani, anche se non sono mai stati renderizzati.
- **Soppressione delle directory locale** — i file in `docs/it/`, `docs/fr/`, ecc. vengono
  classificati come shadow locale, non come orfani.

Puoi quindi validare una struttura i18n complessa con Zenzic e avere la certezza della sua
coerenza interna — il grafo dei link è corretto, le catene di fallback sono intatte, la nav
è completa — prima di impegnarti con qualsiasi motore di rendering.

---

## Cosa rimane invariato passando a Zensical

Zensical legge `mkdocs.yml` nativamente. Molti progetti possono cambiare il binario di build
senza toccare un singolo file di documentazione. Dal punto di vista di Zenzic:

- La struttura della directory `docs/` rimane invariata.
- `mkdocs.yml` rimane valido come sorgente principale di navigazione e configurazione;
  Zensical lo legge direttamente.
- Le convenzioni i18n in folder-mode e suffix-mode sono strutturalmente identiche.
- `[build_context]` in `zenzic.toml` può rimanere `engine = "mkdocs"` fino a quando non sei
  pronto a creare `zensical.toml`.

---

## Best practice per MkDocs Material

### Configurazione dello switcher di lingua

Quando si usa `mkdocs-material` con il plugin `i18n` e più lingue, lo switcher di lingua
può essere controllato da due meccanismi distinti. Mescolarli produce conflitti di routing
che Zenzic — in quanto linter dei sorgenti — non può rilevare automaticamente, ma che
rompono silenziosamente l'esperienza utente in fase di build.

**Configurazione raccomandata:**

```yaml
# mkdocs.yml
plugins:
  - i18n:
      docs_structure: folder
      fallback_to_default: true
      reconfigure_material: true   # ← delega lo switcher al plugin i18n
      reconfigure_search: true
      languages:
        - locale: en
          default: true
          build: true
          link: /
        - locale: it
          build: true
          link: /it/
```

**Non aggiungere** un blocco `extra.alternate` insieme a `reconfigure_material: true`.
Quando entrambi sono presenti, il tema Material riceve due definizioni di switcher in
conflitto; a seconda della versione del plugin il risultato è uno switcher duplicato oppure
nessuno switcher:

```yaml
# ✗ — rimuovere questo blocco quando reconfigure_material: true è impostato
extra:
  alternate:
    - name: English
      link: /
      lang: en
    - name: Italiano
      link: /it/
      lang: it
```

**Perché Zenzic gestisce questo correttamente:**
Quando `reconfigure_material: true` è presente in `mkdocs.yml`, Zenzic riconosce che il
tema Material genererà automaticamente i punti di ingresso per le lingue (es. `/it/`) in
fase di build. Queste pagine non sono mai elencate in `nav:` — sono rotte sintetiche
prodotte dal plugin. Zenzic le marca come **REACHABLE auto-generate** nella Virtual Site
Map in modo che non vengano mai segnalate come orfane.

---

## Piano di migrazione

### Fase 1 — Stabilisci un baseline

Esegui la suite completa di controlli e registra un baseline (punto di riferimento) di
qualità prima di cambiare qualsiasi cosa:

```bash
# Conferma che la documentazione sia strutturalmente corretta prima di toccare il layer di build
zenzic check all
zenzic score --save   # persisti il baseline in .zenzic-score.json
```

Un baseline salvato significa che qualsiasi regressione introdotta durante la migrazione è
immediatamente misurabile con `zenzic diff`. Il baseline è uno snapshot dello stato dei
sorgenti — non dipende dal funzionamento di alcun motore di build.

### Fase 2 — Cambia il binario di build

Installa Zensical insieme a (o al posto di) MkDocs:

```bash
uv add --dev zensical      # raccomandato
# oppure: pip install zensical
```

Esegui la build della documentazione per verificare che produca output corretto:

```bash
zensical build
```

I controlli di Zenzic sono engine-neutral (indipendenti dal motore di build) — eseguili
dopo la build per confermare che la struttura dei sorgenti sia intatta:

```bash
zenzic check all
zenzic diff              # dovrebbe riportare zero delta rispetto al baseline pre-migrazione
```

### Fase 3 — Dichiara l'identità Zensical (opzionale)

Se vuoi che Zenzic imponga il contratto strutturale di Zensical — richiedendo la presenza
di `zensical.toml` e usando `ZensicalAdapter` per l'estrazione della nav — aggiorna
`zenzic.toml`:

```toml
# zenzic.toml
[build_context]
engine = "zensical"
default_locale = "en"
locales        = ["it"]
```

E crea un `zensical.toml` minimale nella root del repository:

```toml
# zensical.toml  (Zensical v0.0.31+)
[project]
site_name = "La Mia Documentazione"
docs_dir  = "docs"
nav = [
    "index.md",
    {"Guida" = "guide.md"},
]
```

!!! warning "Contratto di enforcement"
    Una volta dichiarato `engine = "zensical"` in `zenzic.toml`, `zensical.toml` **deve**
    esistere. Zenzic solleva un `ConfigurationError` immediatamente se è assente — non c'è
    fallback silenzioso a `mkdocs.yml`. Questo è intenzionale: l'identità dell'engine deve
    essere provabile.

### Fase 4 — Verifica l'integrità dei link

Il controllo dei link è il passo di validazione più importante. Eseguilo sulla migrazione
completata:

```bash
# Link interni + risoluzione fallback i18n
zenzic check links

# Link reference-style + Shield (rilevamento credenziali)
zenzic check references

# Suite completa
zenzic check all
zenzic diff --threshold 0   # fallisce su qualsiasi regressione, nessun margine
```

Se il punteggio corrisponde al baseline pre-migrazione, la migrazione è completa.

---

## Le tue opzioni di migrazione

Passare a Zensical è una delle diverse strade disponibili a un progetto su MkDocs. Zenzic
le supporta tutte con la stessa garanzia di qualità:

| Percorso | `engine` in `zenzic.toml` | Cosa valida Zenzic |
| :--- | :--- | :--- |
| Rimane su MkDocs 1.x | `"mkdocs"` | Contratto strutturale completo MkDocs 1.x |
| Passa a Zensical | `"zensical"` | Nav Zensical + contratto identità TOML |
| Migra a un altro motore | `"mkdocs"` durante transizione, poi adapter | Integrità sorgenti durante il cambio |
| Valuta senza impegnarsi | flag CLI `--engine mkdocs` o `--engine zensical` | Controllo compatibilità dry-run |

Il flag CLI `--engine` permette di eseguire un singolo controllo contro un adapter diverso
senza toccare `zenzic.toml`:

```bash
# Testa se i tuoi sorgenti attuali sono strutturalmente compatibili con Zensical
# senza dichiarare il passaggio in zenzic.toml
zenzic check all --engine zensical
```

---

## Mantenere le regole custom durante la migrazione

Le `[[custom_rules]]` in `zenzic.toml` sono **indipendenti dall'adapter** — si attivano
identicamente indipendentemente dall'engine. Qualsiasi regola in vigore per il tuo progetto
MkDocs continua a funzionare senza modifiche dopo il passaggio a Zensical:

```toml
# Queste regole funzionano con entrambi gli engine
[[custom_rules]]
id       = "ZZ-NODRAFT"
pattern  = "(?i)\\bDRAFT\\b"
message  = "Rimuovere il marker DRAFT prima della pubblicazione."
severity = "warning"

[build_context]
engine = "zensical"
```

---

## Riferimento rapido

| Passo | Comando | Risultato atteso |
| :--- | :--- | :--- |
| Baseline | `zenzic score --save` | Score salvato in `.zenzic-score.json` |
| Dry-run compatibilità | `zenzic check all --engine zensical` | Problemi strutturali con adapter Zensical |
| Dopo il cambio di build | `zenzic check all` | Stessi problemi di prima |
| Controllo regressioni | `zenzic diff` | Delta = 0 |
| Enforcement identità | `engine = "zensical"` in `zenzic.toml` | Richiede `zensical.toml` |
| Gate finale | `zenzic diff --threshold 0` | Exit 0 solo se il punteggio non è diminuito |
