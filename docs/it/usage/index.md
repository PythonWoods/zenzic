---
icon: lucide/play
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Utilizzo

Zenzic legge direttamente dal filesystem e funziona con qualsiasi progetto, inclusi quelli che
non usano MkDocs come motore di build. Puoi usarlo in locale, come hook di pre-commit o nelle
tue pipeline CI.

!!! tip "Vuoi eseguirlo subito?"

    ```bash
    uvx zenzic check all
    ```

    Nessuna installazione richiesta. `uvx` scarica ed esegue Zenzic in un ambiente temporaneo.

---

## Workflow Init → Config → Check

Il workflow standard per adottare Zenzic in un progetto:

### 1. Init — scaffolding del file di configurazione

Crea un `zenzic.toml` con un singolo comando. Zenzic rileva automaticamente il motore di
documentazione e preimposta `[build_context]` di conseguenza:

```bash
zenzic init
```

**Esempio di output quando è presente `mkdocs.yml`:**

```text
Created zenzic.toml
  Engine pre-set to mkdocs (detected from mkdocs.yml).

Edit the file to enable rules, adjust directories, or set a quality threshold.
Run zenzic check all to validate your documentation.
```

Se non viene rilevato alcun file di configurazione engine, `zenzic init` produce uno scaffold
engine-agnostico (modalità Vanilla). In entrambi i casi, tutte le impostazioni sono commentate
per default — decommenta e modifica solo i campi di cui hai bisogno.

Eseguendo Zenzic senza un `zenzic.toml`, Zenzic utilizza i valori predefiniti e mostra un
pannello "Helpful Hint" che suggerisce `zenzic init`:

```text
╭─ 💡 Zenzic Tip ─────────────────────────────────────────────────────╮
│ Using built-in defaults — no zenzic.toml found.                      │
│ Run zenzic init to create a project configuration file.              │
│ Customise docs directory, excluded paths, engine adapter, and rules. │
╰──────────────────────────────────────────────────────────────────────╯
```

### 2. Config — personalizza per il tuo progetto

Modifica il `zenzic.toml` generato per silenziare il rumore e impostare soglie appropriate:

```toml
# zenzic.toml — nella root del repository
excluded_assets = [
    "assets/favicon.svg",
    "assets/social-preview.png",
]
placeholder_max_words = 30
fail_under = 70
```

Consulta la [Guida alla Configurazione](../configuration/index.md) per l'elenco completo dei campi.

### 3. Check — esegui in modo continuativo

Con il baseline stabilito, esegui Zenzic su ogni commit e pull request:

```bash
zenzic check all --strict
zenzic score --save           # salva baseline sul branch main
zenzic diff --threshold 5     # blocca le PR che regrediscono il baseline
```

---

## Modalità Vanilla vs Modalità Engine-aware

Zenzic opera in una di due modalità a seconda che riesca a trovare un file di configurazione
del motore di build:

### Modalità Engine-aware

Quando `mkdocs.yml` (MkDocs/Zensical) o `zensical.toml` (Zensical) è presente nella root del
repository, Zenzic carica l'**adapter** corrispondente che fornisce:

- **Consapevolezza della nav** — il controllo orfani sa esattamente quali file dovrebbero essere
  nella nav e quali no (ad esempio i file di locale i18n).
- **Fallback i18n** — i link cross-locale vengono risolti correttamente.
- **Soppressione directory locale** — i file sotto `docs/it/`, `docs/fr/`, ecc. non vengono
  segnalati come orfani.

### Modalità Vanilla

Quando non viene trovata alcuna configurazione del motore di build — o quando viene specificato un
nome di engine sconosciuto — Zenzic ricade su `VanillaAdapter`:

- **Il controllo orfani viene saltato.** Senza una dichiarazione di nav, ogni file Markdown
  sembrerebbe un orfano, rendendo il controllo inutile.
- **Tutti gli altri controlli vengono eseguiti normalmente** — link, snippet, placeholder, asset
  e riferimenti vengono tutti validati.

Modalità Vanilla è la scelta giusta per wiki Markdown semplici, repository GitHub-wiki, o
qualsiasi progetto dove la navigazione è implicita.

!!! tip "Forza una modalità specifica"
    Usa `--engine` per sovrascrivere l'adapter rilevato per una singola esecuzione:

    ```bash
    zenzic check all --engine vanilla   # salta il controllo orfani
    zenzic check all --engine mkdocs    # forza l'adapter MkDocs
    ```

---

## Opzioni di installazione

### Temporanea — nessuna installazione richiesta

```bash
uvx zenzic check all
```

`uvx` risolve ed esegue Zenzic da PyPI in un ambiente temporaneo. Nulla viene installato sul sistema. È la scelta giusta per audit una-tantum, `git hooks` e job CI dove si vuole evitare di fissare una dipendenza dev.

### Strumento globale — disponibile in ogni progetto

```bash
uv tool install zenzic
zenzic check all
```

Installa una volta, usa in qualsiasi progetto. Il binario è disponibile nel `PATH` senza attivare un virtual environment.

### Dipendenza dev del progetto — versione fissata per progetto

```bash
uv add --dev zenzic
uv run zenzic check all
```

Installa Zenzic nel virtual environment del progetto e fissa la versione in `uv.lock`. Scelta giusta per progetti di team.

### Comandi

```bash
# Controlli individuali
zenzic check links        # Link interni; aggiungi --strict per la validazione HTTP esterna
zenzic check orphans      # Pagine su disco mancanti dalla nav
zenzic check snippets     # Blocchi Python che non compilano
zenzic check placeholders # Pagine stub: basso conteggio parole o pattern vietati
zenzic check assets       # File media non referenziati da nessuna pagina

# Autofix & Cleanup
zenzic clean assets       # Elimina interattivamente gli asset non utilizzati
zenzic clean assets -y    # Elimina gli asset non utilizzati immediatamente
zenzic clean assets --dry-run # Mostra cosa verrebbe eliminato senza farlo

# Pipeline di riferimento (v0.2.0)
zenzic check references              # Harvest → Cross-Check → Shield → Integrity score
zenzic check references --strict     # Tratta le Dead Definitions come errori
zenzic check references --links      # Valida anche gli URL via HTTP asincrono (1 ping/URL)

# Tutti i controlli in sequenza
zenzic check all                    # Esegue tutti e sei i controlli
zenzic check all --strict           # Tratta i warning come errori
zenzic check all --format json      # Output machine-readable
zenzic check all --exit-zero        # Segnala problemi ma esce sempre con codice 0

# Punteggio qualità
zenzic score                        # Calcola punteggio 0–100
zenzic score --save                 # Calcola e persiste snapshot in .zenzic-score.json
zenzic score --fail-under 80        # Esce con 1 se il punteggio è sotto la soglia
zenzic score --format json          # Report punteggio machine-readable

# Rilevamento regressioni
zenzic diff                         # Confronta punteggio attuale con snapshot salvato
zenzic diff --threshold 5           # Esce con 1 solo se il calo è > 5 punti
zenzic diff --format json           # Report diff machine-readable

```

### Autofix & Cleanup

Invece di limitarsi a segnalare i problemi, Zenzic può ripulire attivamente il tuo repository. `zenzic clean assets` legge la documentazione, trova tutti i file non utilizzati in `docs_dir` (rispettando rigorosamente `excluded_assets`, `excluded_dirs` e `excluded_build_artifacts`), e ti chiede conferma per eliminarli. Usa `--dry-run` per visualizzare un'anteprima in sicurezza o `-y` per automatizzare l'eliminazione nelle pipeline CI.

### Server di sviluppo

```bash
# Avvia il server con pre-flight di qualità
zenzic serve

# Forza un motore specifico
zenzic serve --engine mkdocs
zenzic serve --engine zensical

# Porta personalizzata (scansiona fino a 10 porte consecutive se occupata)
zenzic serve --port 9000
zenzic serve -p 9000

# Salta il pre-flight e avvia direttamente il server
zenzic serve --no-preflight
```

`zenzic serve` rileva automaticamente il motore di documentazione dalla root del repository:

| File di config presente | Binario disponibile | Risultato |
| :--- | :--- | :--- |
| `zensical.toml` | `zensical` o `mkdocs` | Avvia il motore disponibile |
| `zensical.toml` | nessuno | Errore — installa un motore |
| solo `mkdocs.yml` | `mkdocs` o `zensical` | Avvia il motore disponibile |
| solo `mkdocs.yml` | nessuno | Errore — installa un motore |
| nessuno | qualsiasi | Server statico su `site/` (senza hot-reload) |

`zensical.toml` ha sempre la precedenza perché Zensical è un superset di MkDocs e legge `mkdocs.yml` nativamente. Il fallback statico permette a `zenzic serve` di funzionare in qualsiasi ambiente — anche senza mkdocs o zensical installati — purché esista una directory `site/` pre-compilata.

Quando `--engine` è specificato esplicitamente, Zenzic verifica sia che il binario sia nel `$PATH` sia che il file di config richiesto esista. `--engine zensical` accetta `mkdocs.yml` come config valida per retrocompatibilità.

**Gestione della porta.** Zenzic individua una porta libera tramite socket probe *prima* di avviare il subprocess dell'engine, poi passa `--dev-addr 127.0.0.1:{porta}` a mkdocs o zensical. Questo elimina l'errore `Address already in use` dall'engine: se la porta richiesta (default `8000`) è occupata, Zenzic prova silenziosamente le porte successive fino a dieci volte e indica quale porta viene effettivamente usata.

Prima di avviare il server, Zenzic esegue un controllo pre-flight silenzioso — orfani, snippet, placeholder e asset non usati. I problemi vengono stampati come warning ma non bloccano mai l'avvio. La validazione dei link esterni (`check links --strict`) è intenzionalmente esclusa dal pre-flight: non ha senso attendere i roundtrip di rete quando stai per modificare la documentazione live.

Il processo server eredita il terminale, quindi i log di hot-reload e l'output delle richieste appaiono non filtrati. Usa `--no-preflight` per saltare il controllo qualità quando sei nel mezzo di una fix e non hai bisogno del rumore.

### Codici di uscita

| Codice | Significato |
| :---: | :--- |
| `0` | Tutti i controlli selezionati sono passati (o `--exit-zero` era impostato) |
| `1` | Uno o più controlli hanno segnalato problemi |
| **`2`** | **SECURITY CRITICAL — Zenzic Shield ha rilevato una credenziale esposta** |

!!! danger "Il codice di uscita 2 è riservato agli eventi di sicurezza"
    Il codice 2 viene emesso esclusivamente da `zenzic check references` quando lo Shield
    rileva un pattern di credenziale noto incorporato in un URL di riferimento. Non viene mai
    usato per i fallimenti ordinari dei controlli. Se ricevi il codice di uscita 2, trattalo
    come un incidente di sicurezza bloccante e **ruota immediatamente la credenziale esposta**.

### Override dell'adapter engine

Il flag `--engine` sovrascrive l'adapter del motore di build per una singola esecuzione senza
modificare `zenzic.toml`. È accettato da `check orphans` e `check all`:

```bash
# Forza l'adapter MkDocs anche se zenzic.toml dice altro
zenzic check orphans --engine mkdocs
zenzic check all --engine mkdocs

# Usa l'adapter Zensical (richiede che zensical.toml sia presente)
zenzic check orphans --engine zensical
zenzic check all --engine zensical
```

Se passi un nome di engine per cui non esiste un adapter registrato, Zenzic elenca gli adapter
disponibili ed esce con codice 1:

```text
ERROR: Unknown engine adapter 'hugo'.
Installed adapters: mkdocs, vanilla, zensical
Install a third-party adapter or choose from the list above.
```

---

### Output JSON

Passa `--format json` a `check all` per output strutturato:

```bash
zenzic check all --format json | jq '.orphans'
zenzic check all --format json > report.json
```

Il report JSON contiene cinque chiavi che corrispondono ai nomi dei controlli: `links`, `orphans`, `snippets`, `placeholders`, `unused_assets`. Una lista vuota indica che il controllo è passato.

### Punteggio qualità

I controlli individuali rispondono a una domanda binaria: passa o fallisce. `zenzic score` risponde a una diversa: *quanto è sana questa documentazione, e sta migliorando o peggiorando nel tempo?*

`zenzic score` esegue tutti e sei i controlli e aggrega i risultati in un singolo intero tra 0 e 100. Il punteggio è deterministico — a parità di stato della documentazione, produce sempre lo stesso numero — il che lo rende sicuro da tracciare nel controllo di versione e da confrontare tra branch.

### Come è calcolato il punteggio

Ogni categoria di controllo porta un peso fisso che riflette il suo impatto sull'esperienza del lettore:

| Categoria | Peso | Rationale |
| :--- | ---: | :--- |
| links | 35 % | Un link non valido è un vicolo cieco immediato per il lettore |
| orphans | 20 % | Le pagine irraggiungibili sono invisibili |
| snippets | 20 % | Esempi di codice non validi fuorviano attivamente gli sviluppatori |
| placeholders | 15 % | Il contenuto stub segnala una pagina incompiuta o abbandonata |
| assets | 10 % | Gli asset non usati sono spreco, ma non bloccano il lettore |

All'interno di ogni categoria, il punteggio decade linearmente: il primo problema costa 20 punti su 100 per quella categoria, il secondo ne costa altri 20, e così via, con un minimo di zero. Una categoria con cinque o più problemi non contribuisce nulla al totale. I contributi ponderati vengono sommati e arrotondati a un intero.

Questo significa che un singolo link non valido fa scendere il punteggio totale di circa 7 punti (peso del 35% × decadimento del 20%), mentre un singolo asset non utilizzato costa circa 2 punti. I pesi codificano un giudizio intenzionale sulla gravità.

### Tracciare le regressioni in CI

Il punteggio diventa più utile se confrontato con un baseline noto. Il flag `--save` scrive il report corrente su `.zenzic-score.json` nella root del repository. Una volta che esiste un baseline, `zenzic diff` calcola il delta ed esce con codice non-zero se la documentazione è regredita.

Un tipico setup CI su un progetto di team:

```bash
# Stabilisce o aggiorna il baseline sul branch main
zenzic score --save

# Su ogni pull request, blocca i merge che degradano la qualità
zenzic diff --threshold 5
```

`--threshold 5` dà ai collaboratori un margine di cinque punti — piccoli cambiamenti non correlati (una nuova pagina stub, un commento TODO temporaneo) non bloccano una PR. Impostalo a `0` per un gate rigoroso dove qualsiasi regressione fa fallire la pipeline.

### Imporre un punteggio minimo

Usa `--fail-under` quando vuoi un floor assoluto piuttosto che un controllo relativo:

```bash
zenzic score --fail-under 80
```

È utile per le policy di documentation-as-a-feature dove il team si è impegnato a mantenere un livello di qualità definito, indipendentemente da quello che era il punteggio la settimana scorsa.

### Reporting soft

Per rendere visibile il punteggio senza bloccare la pipeline — utile durante uno sprint attivo di miglioramento della documentazione — combina `check all --exit-zero` con `score` in step separati:

```bash
zenzic check all --exit-zero   # report completo, esce 0 comunque
zenzic score                   # mostra il punteggio per visibilità
```

---

## Integrità dei riferimenti (v0.2.0)

`zenzic check references` è il controllo più approfondito della suite. A differenza degli altri
controlli, che operano sulle singole pagine in isolamento, la pipeline di riferimento costruisce
una **vista globale** di tutte le Reference Definitions Markdown nell'intera documentazione prima
di validare qualsiasi utilizzo.

### Perché due pass?

Uno scanner single-pass produrrebbe falsi positivi per i *forward reference* — casi in cui
`[testo][id]` appare su una pagina prima che `[id]: url` sia definito più avanti nello stesso
file. La [Two-Pass Pipeline][arch-two-pass] risolve questo in modo pulito:

- **Pass 1 — Harvesting**: legge ogni file, raccoglie tutte le definizioni `[id]: url` in una
  [ReferenceMap][arch-refmap] per-file ed esegue lo Zenzic Shield su ogni URL.
- **Pass 2 — Cross-Check**: risolve ogni utilizzo `[testo][id]` rispetto alla ReferenceMap
  completamente popolata e segnala le Dangling References.
- **Pass 3 — Integrity**: calcola il punteggio di integrità per-file dai dati di risoluzione.

!!! warning "Non unire i pass"
    Unire Harvesting e Cross-Check in un singolo ciclo produce falsi errori *Phantom Reference*
    sui forward reference — un pattern comune nei grandi progetti di documentazione. La
    separazione in due pass non è un'ottimizzazione; è un requisito di correttezza.

### Comandi

```bash
zenzic check references              # Pipeline completa: Harvest → Cross-Check → Shield → score
zenzic check references --strict     # Tratta le Dead Definitions come errori bloccanti
zenzic check references --links      # Valida anche gli URL via HTTP asincrono (1 ping/URL)
```

`--links` attiva la [deduplicazione URL globale][arch-dedup]: ogni URL unico tra tutti i file
viene pingato esattamente una volta, indipendentemente da quante definizioni vi fanno riferimento.

### Zenzic Shield

!!! danger "Sicurezza — Exit Code 2"
    Se `zenzic check references` esce con codice **2**, è stato trovato un segreto incorporato
    in un URL di riferimento nella documentazione. **Ruota immediatamente la credenziale esposta.**

Lo Shield scansiona ogni URL di riferimento durante il Pass 1 — prima che il Pass 2 validi i
link e prima che `--links` emetta qualsiasi richiesta HTTP. Un documento contenente una
credenziale esposta non viene mai usato per fare richieste in uscita.

| Tipo di credenziale | Pattern |
| :--- | :--- |
| OpenAI API key | `sk-[a-zA-Z0-9]{48}` |
| GitHub token | `gh[pousr]_[a-zA-Z0-9]{36}` |
| AWS access key | `AKIA[0-9A-Z]{16}` |

!!! tip "Integrazione pre-commit"
    Aggiungi `zenzic check references` ai tuoi [pre-commit hook][pre-commit] per rilevare le
    credenziali esposte prima che vengano mai committate nel controllo di versione.

### Punteggio di integrità

Ogni file riceve un **punteggio di integrità** per-file (0–100): il rapporto tra Reference
Definitions *usate* e quelle *totali*. Un punteggio di 100 significa che ogni definizione è
referenziata almeno una volta; punteggi più bassi indicano Dead Definitions.

$$
Reference\ Integrity = \frac{Resolved\ References}{Total\ Reference\ Definitions}
$$

Usa `--strict` per trattare le Dead Definitions come errori bloccanti e far fallire la pipeline
quando un file scende sotto il 100%.

---

## Integrazione CI/CD

Zenzic è progettato per workflow pipeline-first. Tutti i comandi escono con codice non-zero in
caso di fallimento — nessun wrapper aggiuntivo richiesto.

### `uvx` vs `uv run` vs `zenzic` diretto

| Invocazione | Comportamento | Quando usare |
| :--- | :--- | :--- |
| `uvx zenzic ...` | Scarica ed esegue Zenzic in un ambiente **isolato ed effimero** | Job una-tantum, pre-commit hook, step CI senza fase di install del progetto |
| `uv run zenzic ...` | Esegue Zenzic dal **virtual environment del progetto** (richiede `uv sync`) | Quando Zenzic è in `pyproject.toml` e serve comportamento version-pinned |
| `zenzic ...` (diretto) | Richiede Zenzic nel `$PATH` (dopo `uv tool install` o `pip install`) | Macchine developer con install globale persistente |

!!! tip "Raccomandazione CI"
    Preferisci `uvx zenzic ...` per step CI che non installano già le dipendenze del progetto.
    Evita di aggiungere Zenzic all'insieme delle dipendenze di produzione sfruttando la cache
    di risoluzione di [uv][uv].

### GitHub Actions — quality gate documentazione

```yaml
# .github/workflows/zenzic-scan.yml
name: Qualità documentazione

on: [push, pull_request]

jobs:
  docs-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Lint documentazione
        run: uvx zenzic check all --strict

      - name: Integrità riferimenti + Shield
        run: uvx zenzic check references
        # Exit 1 su Dangling References
        # Exit 2 immediatamente se Shield rileva una credenziale esposta

      - name: Controllo regressione punteggio
        run: uvx zenzic diff --threshold 5
```

!!! danger "Non sopprimere mai l'Exit Code 2"
    Impostare `continue-on-error: true` su uno step che esegue `check references` vanifica
    completamente lo Shield. Il codice 2 deve bloccare la pipeline — significa che una
    credenziale live è stata trovata nel sorgente della documentazione.

### Gestione baseline

```yaml
# Sul branch main — stabilisce o aggiorna il baseline del punteggio
- name: Salva baseline qualità
  if: github.ref == 'refs/heads/main'
  run: uvx zenzic score --save

# Su pull request — blocca le regressioni
- name: Controllo regressione punteggio
  if: github.event_name == 'pull_request'
  run: uvx zenzic diff --threshold 5
```

---

## Scegliere tra le modalità

Le due modalità non sono mutuamente esclusive. Molti progetti lo usano per i pre-commit hook e gli audit locali rapidi, e come gate definitivo in CI.

| Scenario | Approccio consigliato |
| --- | --- |
| Audit una-tantum, nessuna installazione | `uvx zenzic check all` |
| Sviluppo locale, feedback rapido | `zenzic check all` (installazione globale o di progetto) |
| Pre-commit hook | `uvx zenzic check all` o `uv run zenzic check all` |
| CI: nessuno step di build MkDocs | CLI — `uv run zenzic check all` |
| Tracciare la qualità nel tempo | `zenzic score --save` su main + `zenzic diff` su PR |
| Imporre un punteggio minimo | `zenzic score --fail-under 80` |
| Report senza bloccare (sprint di cleanup) | `zenzic check all --exit-zero` o `fail_on_error: false` |
| Sviluppo locale con anteprima live | `zenzic serve` |
| Validazione link (sempre solo CLI) | `zenzic check links [--strict]` |
| Integrità riferimenti + scansione segreti | `zenzic check references [--strict] [--links]` |
| Rilevare credenziali esposte pre-commit | `zenzic check references` in pre-commit hook |

Il controllo dei link e il controllo dei riferimenti sono sempre solo CLI. Il parser nativo opera

---

## Utilizzo programmatico

Il core di Zenzic è prima di tutto una libreria. Importa `ReferenceScanner` e `ReferenceMap`
direttamente nei tuoi tool di build, o test suite.

### Scansione di un singolo file

```python
from pathlib import Path

from zenzic.core.scanner import ReferenceScanner
from zenzic.models.references import ReferenceMap

# Ogni scanner opera su un singolo file Markdown
scanner = ReferenceScanner(Path("docs/api.md"))

# Pass 1: harvest delle definizioni + esecuzione dello Shield
# Ogni evento è una tupla (lineno, event_type, data)
# event_type in {"DEF", "DUPLICATE_DEF", "IMG", "MISSING_ALT", "SECRET"}
security_findings = []
for lineno, event, data in scanner.harvest():
    if event == "SECRET":
        # Shield attivato — credenziale rilevata prima di qualsiasi richiesta HTTP
        security_findings.append(data)
    elif event == "DUPLICATE_DEF":
        print(f"  WARN [{lineno}]: definizione duplicata '{data}' (first wins per CommonMark §4.7)")

# Pass 2: risolvi gli utilizzi rispetto alla ReferenceMap completamente popolata
# Deve essere chiamato dopo che harvest() è completamente consumato
cross_check_findings = scanner.cross_check()
for finding in cross_check_findings:
    print(f"  {finding.level}: {finding.message}")

# Pass 3: report di integrità
report = scanner.get_integrity_report(
    cross_check_findings=cross_check_findings,
    security_findings=security_findings,
)
print(f"Integrità: {report.integrity_score:.1f}%")
```

### Orchestrazione multi-file

Per scansionare un intero albero di documentazione con deduplicazione URL globale:

```python
from pathlib import Path

from zenzic.core.scanner import scan_docs_references_with_links

reports, link_errors = scan_docs_references_with_links(
    repo_root=Path("."),
    validate_links=False,  # imposta True per pingare ogni URL unico (1 richiesta/URL)
)

for report in reports:
    print(f"{report.file_path}: {report.integrity_score:.1f}%")

for err in link_errors:
    print(f"  LINK ERROR: {err}")
```

`scan_docs_references_with_links` applica automaticamente il contratto Shield-as-firewall:
se il Pass 1 trova segreti in qualsiasi file, solleva `SystemExit(2)` prima che il Pass 2
venga eseguito su qualsiasi file.

<!-- ─── Reference link definitions ──────────────────────────────────────────── -->

[arch-two-pass]:  ../architecture.md#two-pass-reference-pipeline-v020
[arch-refmap]:    ../architecture.md#gestione-dello-stato-referencemap-tra-i-pass
[arch-dedup]:     ../architecture.md#deduplicazione-url-globale-via-linkvalidator
[pre-commit]:     https://pre-commit.com/
[uv]:             https://docs.astral.sh/uv/
