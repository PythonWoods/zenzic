<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Zenzic v0.4.0: Il Framework Agnostico per l'Integrità della Documentazione

**Data di rilascio:** 2026-03-31
**Stato:** Release Candidate 4 — routing-aware, freeze pre-release

---

## Perché questo rilascio conta, e perché conta adesso

L'ecosistema degli strumenti di documentazione è in fermento. MkDocs 2.0 si avvicina con
modifiche incompatibili alle API dei plugin e ai formati di configurazione. Zensical sta
emergendo come alternativa matura. I team migrano, sperimentano, cercano copertura. In questo
contesto, qualsiasi quality gate strettamente accoppiato a un motore di build specifico ha una
data di scadenza.

v0.4.0 risponde a questa incertezza con un impegno architetturale preciso: **Zenzic non si
romperà mai perché avete cambiato il vostro motore di documentazione.**

Non è una promessa di marketing. È una garanzia tecnica provabile, sostenuta da tre pilastri
di design e due sprint di chirurgia strutturale.

---

## Il Principio del Porto Sicuro

Immaginate di costruire un faro mentre i porti intorno cambiano nome, spostano i moli e
riscrivono le mappe nautiche. Zenzic è quel faro — un punto fisso e stabile che rimane valido
prima, durante e dopo qualsiasi migrazione tra motori di build.

Questo non è un ripiego. È la scelta di design più audace che potessimo fare.

Nella pratica, il Porto Sicuro si traduce in agnosticismo assoluto rispetto all'engine:

- Zenzic analizza file Markdown grezzi e configurazione come dati semplici. Non importa mai un
  framework di documentazione, non lo esegue, non aspetta la sua output.
- La conoscenza specifica dell'engine (struttura della nav, convenzioni i18n, regole di fallback
  locale) è incapsulata in **adapter** — componenti sottili e sostituibili che traducono la
  semantica dell'engine in un protocollo neutro. Il Core non vede mai `MkDocsAdapter` o
  `ZensicalAdapter`; vede solo un `BaseAdapter` che risponde a cinque domande.
- Gli adapter di terze parti si installano come pacchetti Python e vengono scoperti a runtime
  tramite entry-point. Aggiungere supporto per un nuovo engine (Hugo, Docusaurus) non richiede
  alcun aggiornamento di Zenzic.

La conseguenza pratica: un progetto che migra da MkDocs a Zensical può eseguire
`zenzic check all` continuamente contro entrambe le configurazioni simultaneamente. Un progetto
che non ha ancora scelto il motore di build può comunque validare la qualità della propria
documentazione oggi.

---

## I Tre Pilastri

### 1. Source-first — nessuna build richiesta

Zenzic analizza i file Markdown grezzi e la configurazione come dati semplici. Non chiama mai
`mkdocs build`, non importa mai un framework di documentazione, non dipende mai dall'HTML
generato. Un link non raggiungibile viene rilevato in 11 millisecondi su 5.000 file — prima
ancora che il vostro runner CI abbia finito il checkout del repository.

Questo rende Zenzic utilizzabile come pre-commit hook, gate pre-build, controllo PR e
validatore di migrazione simultaneamente. Lo stesso strumento. Lo stesso punteggio. Gli stessi
rilevamenti. Indipendentemente dall'engine che usate.

### 2. Nessun subprocess nel Core

L'implementazione di riferimento del "linting agnostico rispetto all'engine" prevede di
invocare l'engine e parsare il suo output. Quell'approccio eredita ogni instabilità dell'engine:
disallineamento di versione, differenze di ambiente, binari mancanti sui runner CI.

Il Core di Zenzic è Python puro. La validazione dei link usa `httpx`. Il parsing della nav usa
`yaml` e `tomllib`. Non ci sono chiamate `subprocess.run` nel percorso di linting. Il binario
dell'engine non deve essere installato perché `zenzic check all` passi.

### 3. Funzioni pure, risultati puri

Tutta la logica di validazione in Zenzic vive in funzioni pure: nessun I/O su file, nessun
accesso alla rete, nessuno stato globale, nessun output sul terminale. L'I/O avviene solo ai
bordi — nei wrapper CLI che leggono file e stampano rilevamenti. Le funzioni pure sono
testabili in modo banale (433 test che passano con il 98,4% di coverage), componibili in
pipeline di ordine superiore, e deterministiche tra ambienti.

Il punteggio che ottenete sul laptop dello sviluppatore è il punteggio che ottiene la CI. Il
punteggio che ottiene la CI è il punteggio che tracciate nel version control. Il determinismo
non è una feature; è il fondamento su cui sono costruiti `zenzic diff` e il rilevamento delle
regressioni.

---

## Cosa è cambiato in rc3

### Fix i18n Ancore — AnchorMissing ora ha la soppressione tramite fallback i18n

`AnchorMissing` ora partecipa alla stessa logica di fallback i18n di `FileNotFound`. In
precedenza, un link come `[testo](it/pagina.md#intestazione)` generava un falso positivo quando
la pagina italiana esisteva ma la sua intestazione era tradotta — perché il ramo `AnchorMissing`
in `validate_links_async` non aveva nessun percorso di soppressione. `_should_suppress_via_i18n_fallback()`
era definita ma non veniva mai chiamata.

**Fix:** nuovo metodo `resolve_anchor()` aggiunto al protocollo `BaseAdapter` e a tutti e tre
gli adapter (`MkDocsAdapter`, `ZensicalAdapter`, `VanillaAdapter`). Quando un'ancora non è
trovata in un file locale, `resolve_anchor()` verifica se l'ancora esiste nel file equivalente
nella locale di default tramite l'`anchors_cache` già in memoria. Nessun I/O su disco
aggiuntivo.

### Utility condivisa — `remap_to_default_locale()`

La logica di rimappatura dei percorsi locale che era duplicata indipendentemente in `resolve_asset()`
e `is_shadow_of_nav_page()` è ora una singola funzione pura in
`src/zenzic/core/adapters/_utils.py`. `resolve_asset()`, `resolve_anchor()` e
`is_shadow_of_nav_page()` in entrambi `MkDocsAdapter` e `ZensicalAdapter` vi delegano.
`_should_suppress_via_i18n_fallback()`, `I18nFallbackConfig`, `_I18N_FALLBACK_DISABLED` e
`_extract_i18n_fallback_config()` — 118 righe di codice morto — sono eliminati
permanentemente da `validator.py`.

### Visual Snippets per i rilevamenti delle regole custom

Le violazioni delle regole custom (`[[custom_rules]]` da `zenzic.toml`) mostrano ora la riga
sorgente incriminata sotto l'intestazione del rilevamento:

```text
[ZZ-NODRAFT] docs/guide/install.md:14 — Remove DRAFT marker before publishing.
  │ > DRAFT: section under construction
```

L'indicatore `│` è visualizzato nel colore della severity del rilevamento. I rilevamenti
standard (link non validi, orfani, ecc.) non sono interessati.

### Schema JSON — 7 chiavi

L'output `--format json` emette ora uno schema stabile a 7 chiavi:
`links`, `orphans`, `snippets`, `placeholders`, `unused_assets`, `references`, `nav_contract`.

### `strict` e `exit_zero` come campi di `zenzic.toml`

Entrambi i flag possono ora essere dichiarati in `zenzic.toml` come default a livello di progetto:

```toml
strict    = true   # equivalente a passare sempre --strict
exit_zero = false  # exit code 0 anche con rilevamenti (soft-gate CI)
```

I flag CLI continuano a sovrascrivere i valori TOML.

### Suddivisione documentazione usage — tre pagine dedicate

`docs/usage/index.md` era una pagina monolitica di 580 righe che copriva install, comandi,
CI/CD, punteggio, funzionalità avanzate e API programmatica. Suddivisa in tre pagine dedicate:

- `usage/index.md` — Opzioni di installazione, workflow init→config→check, modalità engine
- `usage/commands.md` — Comandi CLI, flag, codici di uscita, output JSON, punteggio qualità
- `usage/advanced.md` — Pipeline tre-pass, Zenzic Shield, alt-text, API programmatica,
  documentazione multilingua

I mirror italiani (`it/usage/`) aggiornati con piena parità.

### Validazione snippet multilingua

`zenzic check snippets` valida ora quattro linguaggi usando parser puri in Python — nessun
sottoprocesso per nessun linguaggio. Python usa `compile()`, YAML usa `yaml.safe_load()`, JSON
usa `json.loads()` e TOML usa `tomllib.loads()` (stdlib Python 3.11+). I blocchi con tag di
linguaggio non supportati (`bash`, `javascript`, `mermaid`, ecc.) vengono trattati come testo
semplice e non controllati sintatticamente.

### Shield deep-scan — nessun punto cieco

Lo scanner di credenziali opera ora su ogni riga del file sorgente, incluse le righe dentro i
blocchi di codice delimitati. Una credenziale committata in un esempio `bash` è comunque una
credenziale committata — Zenzic la troverà. Il validatore di link e riferimenti continua a
ignorare il contenuto dei blocchi delimitati per prevenire falsi positivi dagli URL di esempio
illustrativi.

Lo Shield copre ora sette famiglie di credenziali: chiavi API OpenAI, token GitHub, access key
AWS, chiavi live Stripe, token Slack, chiavi API Google e chiavi private PEM generiche.

---

## Packaging Professionale & PEP 735

La rc3 adotta gli ultimi standard di packaging Python end-to-end, rendendo Zenzic più leggero
per gli utenti finali e misurabilmente più veloce in CI.

### Core install snello

`pip install zenzic` installa ora solo le cinque dipendenze runtime (`typer`, `rich`,
`pyyaml`, `pydantic`, `httpx`). L'intero stack MkDocs — precedente effetto collaterale
transitivo del gruppo dev monolitico — non viene più incluso a meno di una richiesta esplicita:

```bash
pip install "zenzic[docs]"   # MkDocs Material + mkdocstrings + plugin
```

Per la grande maggioranza degli utenti (siti Hugo, progetti Zensical, wiki Markdown semplici,
pipeline CI) questo significa un'installazione ~60% più piccola e tempi di cold-start
proporzionalmente più veloci sui runner CI effimeri.

### PEP 735 — gruppi di dipendenze atomici

Le dipendenze di sviluppo sono dichiarate come [gruppi PEP 735](https://peps.python.org/pep-0735/)
in `pyproject.toml`, gestiti da `uv`:

| Gruppo | Scopo | Job CI |
| :----- | :---- | :----- |
| `test` | pytest + coverage | Matrix `quality` (3.11 / 3.12 / 3.13) |
| `lint` | ruff + mypy + pre-commit + reuse | Matrix `quality` |
| `docs` | Stack MkDocs | Job `docs` |
| `release` | nox + bump-my-version + pip-audit | Job `security` |
| `dev` | Tutti i precedenti (sviluppo locale) | — |

Ogni job CI sincronizza solo il gruppo di cui ha bisogno. Il job `quality` non installa mai
lo stack MkDocs. Il job `docs` non installa mai pytest. Questo elimina il tempo di installazione
sprecato per pacchetti inutilizzati e riduce la superficie di potenziali conflitti tra job.
Combinato con la cache `uv` in GitHub Actions, le run CI successive ripristinano l'intero
ambiente in meno di 3 secondi.

### `CITATION.cff`

Il file [`CITATION.cff`](CITATION.cff) (formato CFF 1.2.0) è ora presente nella root del
repository. GitHub lo visualizza automaticamente come pulsante "Cite this repository". Zenodo,
Zotero e altri gestori di riferimenti bibliografici che supportano il formato possono
importarlo direttamente.

---

## Il Firewall per la Documentazione

La rc3 completa uno spostamento strategico in ciò che Zenzic è. Ha iniziato come un link checker.
È diventato un linter engine-agnostic. Con la rc3 diventa un **Firewall per la Documentazione**
— un unico gate che applica correttezza, completezza e sicurezza simultaneamente.

Le tre dimensioni del firewall:

**1. Correttezza** — Zenzic valida la sintassi di ogni blocco di dati strutturati nella tua
documentazione. I tuoi esempi YAML per Kubernetes, i tuoi frammenti JSON OpenAPI, i tuoi snippet
di configurazione TOML — se pubblichi esempi di configurazione errati, i tuoi utenti copieranno
configurazioni errate. `check snippets` rileva questo prima che raggiunga la produzione, usando
gli stessi parser che utilizzeranno gli utenti.

**2. Completezza** — Il rilevamento degli orfani, la scansione dei placeholder e il gate
`fail_under` garantiscono che ogni pagina linkata nella nav esista, contenga contenuto reale e
ottenga un punteggio superiore alla soglia concordata dal team. Una documentazione non è "finita"
quando tutte le pagine esistono — è finita quando tutte le pagine sono complete.

**3. Sicurezza** — Lo Shield scansiona ogni riga di ogni file, inclusi i blocchi di codice, per
sette famiglie di credenziali esposte. Nessun blocco, nessuna etichetta, nessuna annotazione può
nascondere un segreto a Zenzic. Il contratto del codice di uscita 2 è non negoziabile e non
sopprimibile: un segreto nella documentazione è un incidente bloccante per il build, non un
warning.

Questo è il significato di "Firewall per la Documentazione": non uno strumento che si esegue una
volta prima di un rilascio, ma un gate che gira ad ogni commit, applica tre dimensioni di qualità
simultaneamente e esce con un codice machine-readable che la pipeline CI può interpretare senza
intervento umano.

---

## Il Grande Disaccoppiamento (v0.4.0-rc2)

La novità principale di questo rilascio è il sistema di **Scoperta Dinamica degli Adapter**. In
v0.3.x, Zenzic possedeva i propri adapter — `MkDocsAdapter` e `ZensicalAdapter` venivano
importati direttamente dalla factory. Aggiungere supporto per un nuovo engine richiedeva un
rilascio di Zenzic.

In v0.4.0, Zenzic è un **framework host**. Gli adapter sono pacchetti Python che si registrano
sotto il gruppo di entry-point `zenzic.adapters`. Una volta installati, diventano immediatamente
disponibili:

```bash
# Esempio: adapter di terze parti per un ipotetico supporto Hugo
uv pip install zenzic-hugo-adapter   # oppure: pip install zenzic-hugo-adapter
zenzic check all --engine hugo
```

Nessun aggiornamento di Zenzic. Nessuna modifica alla configurazione. Solo installa e usa.

Gli adapter built-in (`mkdocs`, `zensical`, `vanilla`) sono registrati nello stesso modo —
non esiste un percorso privilegiato per gli adapter first-party. Questa non è
una protezione per il futuro; è una garanzia strutturale che l'API degli adapter di terze
parti è esattamente altrettanto capace di quella first-party.

---

## Il DSL `[[custom_rules]]`

v0.4.0 introduce la prima versione del DSL per regole lint specifiche del progetto. I team
possono dichiarare regole regex in `zenzic.toml` senza scrivere Python:

```toml
[[custom_rules]]
id       = "ZZ-NODRAFT"
pattern  = "(?i)\\bDRAFT\\b"
message  = "Rimuovere il marker DRAFT prima della pubblicazione."
severity = "warning"

[[custom_rules]]
id       = "ZZ-NOINTERNAL"
pattern  = "internal\\.corp\\.example\\.com"
message  = "L'hostname interno non deve apparire nella documentazione pubblica."
severity = "error"
```

Le regole sono **indipendenti dall'adapter**: si attivano identicamente con MkDocs, Zensical o
una cartella Markdown semplice. Questo significa che le regole scritte per un progetto MkDocs
non richiedono modifiche dopo la migrazione a Zensical.

I pattern vengono compilati una volta al caricamento della configurazione — nessuna penalità di
performance per avere molte regole.

Questo DSL è il primo passo verso Zenzic come motore completo di policy per la documentazione,
non solo un linter strutturale.

---

## Lo Shield (Difesa in Profondità)

Lo scanner di credenziali (`Shield`) ora analizza ogni riga non-definizione durante il Pass 1,
non solo i valori degli URL di riferimento. Uno sviluppatore che incolla una chiave API in un
paragrafo Markdown — non un link di riferimento — viene rilevato prima che qualsiasi URL venga
pingato, prima che qualsiasi richiesta HTTP venga emessa, prima che qualsiasi strumento
downstream veda la credenziale.

Il codice di uscita `2` rimane riservato esclusivamente agli eventi Shield. Non può essere
soppresso da `--exit-zero`, `--strict` o qualsiasi altro flag. Un rilevamento Shield è un
incidente di sicurezza che blocca la build — senza condizioni.

---

## La Documentazione come Cittadina di Prima Classe

La documentazione di v0.4.0 è stata validata con `zenzic check all` a ogni passo — il mandato
canonico del dogfood. Il linter che vende integrità della documentazione usa se stesso come
guardian della propria documentazione.

Modifiche strutturali principali:

- **Suddivisione della configurazione** — la singola "god-page" `configuration.md` è stata
  suddivisa in quattro pagine tematiche:
  [Panoramica](docs/configuration/index.md) ·
  [Impostazioni di Base](docs/configuration/core-settings.md) ·
  [Adapter e Motore](docs/configuration/adapters-config.md) ·
  [DSL Regole Custom](docs/configuration/custom-rules-dsl.md)
- **Parità italiana** — `docs/it/` ora rispecchia la struttura inglese completa. La
  documentazione è production-ready per team internazionali.
- **Guida alla migrazione** — [MkDocs → Zensical](docs/guide/migration.md) workflow in quattro
  fasi con l'approccio baseline/diff/gate come rete di sicurezza della migrazione.
- **Guida Adapter** — [Scrivere un Adapter](docs/developers/writing-an-adapter.md) riferimento
  completo del protocollo e utility di test.

### Onboarding Senza Attrito

v0.4.0 introduce `zenzic init` — un singolo comando che scaffolda un `zenzic.toml` con
rilevamento intelligente dell'engine. Se viene trovato `mkdocs.yml`, il file generato preimposta
`engine = "mkdocs"`. Se viene trovato `zensical.toml`, preimposta `engine = "zensical"`. In
assenza di entrambi, lo scaffold è engine-agnostico (modalità Vanilla).

```bash
uvx zenzic init        # bootstrap senza installazione
# oppure: zenzic init  # se già installato globalmente
```

Per i team che usano Zenzic per la prima volta, un pannello "Helpful Hint" appare automaticamente
quando non è presente un `zenzic.toml` — puntando direttamente a `zenzic init`. Il pannello
scompare nel momento in cui il file viene creato. Zero attrito per iniziare; zero rumore una volta
configurato.

---

## Percorso di Aggiornamento

### Da v0.3.x

Nessuna modifica a `zenzic.toml` è richiesta per i progetti MkDocs. La scoperta degli adapter
è completamente retrocompatibile.

**Una sola modifica comportamentale:** una stringa `engine` sconosciuta ora ricade su
`VanillaAdapter` (salta il controllo orfani) invece di `MkDocsAdapter`. Se il vostro
`zenzic.toml` specifica un nome di engine personalizzato, aggiungete la dichiarazione esplicita
`engine = "mkdocs"`.

### Da v0.4.0-alpha.1

Il flag CLI `--format` è invariato. Il parametro interno `format` nelle API Python `check_all`,
`score` e `diff` è stato rinominato in `output_format` — aggiornate i chiamanti programmatici.

---

## Verifica e Checksum

```text
zenzic check all       # self-dogfood: 7/7 OK
pytest                 # 446 passati, 0 falliti
coverage               # ≥ 80% (gate rigido)
ruff check .           # 0 violazioni
mypy src/              # 0 errori
mkdocs build --strict  # 0 avvertimenti
```

---

*Zenzic v0.4.0 è rilasciato sotto licenza Apache-2.0.*
*Sviluppato e mantenuto con orgoglio da [PythonWoods](https://github.com/PythonWoods).*

---

Based in Italy 🇮🇹 | Committed to the craft of Python development.
Contatto: <dev@pythonwoods.dev>
