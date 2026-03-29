<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Zenzic v0.4.0: Il Framework Agnostico per l'Integrità della Documentazione

**Data di rilascio:** 2026-03-28
**Stato:** Release Candidate 2 — pronto per la distribuzione

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
- **Guida alla migrazione** — [MkDocs → Zensical](docs/guides/migration.md) workflow in quattro
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
zenzic check all   # self-dogfood: 6/6 OK
pytest             # 433 passati, 0 falliti in 2.47s
coverage           # 98.4% line coverage
ruff check .       # 0 violazioni
mypy src/          # 0 errori
```

---

*Zenzic v0.4.0 è rilasciato sotto licenza Apache-2.0.*
*Sviluppato e mantenuto con orgoglio da [PythonWoods](https://github.com/PythonWoods).*

---

Based in Italy 🇮🇹 | Committed to the craft of Python development.
Contatto: <dev@pythonwoods.dev>
