---
icon: lucide/shield-check
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Funzionalità avanzate

Riferimento approfondito sulla Three-Pass Pipeline, Zenzic Shield, controlli di accessibilità
e utilizzo programmatico da Python.

---

## Integrità dei riferimenti (v0.2.0)

`zenzic check references` esegue la **Three-Pass Reference Pipeline** — il motore alla base di
ogni controllo di qualità e sicurezza sui riferimenti.

### Perché tre pass?

I [reference-style link][syntax] Markdown separano *dove punta un link* (la definizione) da
*dove appare* (l'utilizzo). Uno scanner single-pass non può risolvere un riferimento che
appare prima della sua definizione. Zenzic risolve questo con una struttura deliberata a tre pass:

| Pass | Nome | Cosa succede |
| :---: | :--- | :--- |
| 1 | **Harvest** | Legge il file riga per riga; registra tutte le definizioni `[id]: url` in una `ReferenceMap`; esegue lo Shield su ogni URL e riga |
| 2 | **Cross-Check** | Riscorre il file; per ogni utilizzo `[testo][id]`, cerca `id` nella `ReferenceMap` ora completa; segnala gli ID mancanti come **Dangling Reference** |
| 3 | **Integrity Report** | Calcola il punteggio di integrità; aggiunge le **Dead Definition**, i warning per ID duplicati e per alt-text mancanti |

Il Pass 2 inizia solo quando il Pass 1 termina senza security finding. Se lo Shield scatta
durante l'harvesting, Zenzic esce immediatamente con codice 2 — nessuna risoluzione di
riferimenti avviene su file che contengono credenziali esposte.

### Cosa intercetta la pipeline

| Problema | Tipo | Blocca l'uscita? |
| :--- | :---: | :---: |
| **Dangling Reference** — `[testo][id]` dove `id` non ha definizione | errore | Sì |
| **Dead Definition** — `[id]: url` definito ma mai usato da nessun link | warning | No (sì con `--strict`) |
| **Duplicate Definition** — stesso `id` definito due volte; vince il primo (CommonMark §4.7) | warning | No |
| **Alt-text mancante** — `![](url)` o `<img>` con alt vuoto/assente | warning | No |
| **Segreto rilevato** — pattern di credenziale trovato in un URL di riferimento o riga | sicurezza | **Exit 2** |

### Reference Integrity Score

Ogni file riceve un punteggio per-file:

```text
Reference Integrity = (definizioni risolte / definizioni totali) × 100
```

Un file dove ogni definizione è usata almeno una volta ottiene 100. Le definizioni non usate
(dead) abbassano il punteggio. Quando un file non ha definizioni, il punteggio è 100 per
convenzione.

Il punteggio di integrità è un **diagnostico per-file** — non confluisce nel punteggio di
qualità complessivo di `zenzic score`. Usalo per identificare file che accumulano reference
link boilerplate non usati.

---

## Zenzic Shield

Lo Shield gira **dentro il Pass 1** — ogni URL estratto da una reference definition viene
scansionato nel momento in cui l'harvester lo incontra, prima che qualsiasi altra elaborazione
continui. Lo Shield applica anche un pass di difesa in profondità alle righe non-definizione
per intercettare segreti nella prosa normale.

### Pattern di credenziali rilevati

| Nome pattern | Regex | Cosa intercetta |
| :--- | :--- | :--- |
| `openai-api-key` | `sk-[a-zA-Z0-9]{48}` | Chiavi API OpenAI |
| `github-token` | `gh[pousr]_[a-zA-Z0-9]{36}` | Token personal/OAuth GitHub |
| `aws-access-key` | `AKIA[0-9A-Z]{16}` | Access key ID AWS IAM |
| `stripe-live-key` | `sk_live_[0-9a-zA-Z]{24}` | Chiavi segrete live Stripe |
| `slack-token` | `xox[baprs]-[0-9a-zA-Z]{10,48}` | Token bot/utente/app Slack |
| `google-api-key` | `AIza[0-9A-Za-z\-_]{35}` | Chiavi API Google Cloud / Maps |
| `private-key` | `-----BEGIN [A-Z ]+ PRIVATE KEY-----` | Chiavi private PEM (RSA, EC, ecc.) |

### Comportamento dello Shield

- **Ogni riga viene scansionata** — incluse le righe dentro i blocchi di codice delimitati (con o
  senza etichetta). Una credenziale committata in un esempio `bash` è comunque una credenziale
  committata.
- Il rilevamento è **non sopprimibile** — `--exit-zero`, `exit_zero = true` in `zenzic.toml` e
  `--strict` non hanno effetto sui security finding dello Shield.
- Il codice di uscita 2 è riservato **esclusivamente** agli eventi Shield. Non viene mai usato
  per i fallimenti ordinari dei controlli.
- I file con security finding sono **esclusi dalla validazione dei link** — Zenzic non fa ping
  a URL che potrebbero contenere credenziali esposte.
- **Isolamento dei link nei blocchi di codice** — lo Shield scansiona l'interno dei blocchi
  delimitati, ma il validatore di link e riferimenti no. Gli URL di esempio nei blocchi di codice
  (es. `https://api.example.com`) non producono mai falsi positivi nei link.

!!! danger "Se ricevi il codice di uscita 2"
    Trattalo come un incidente di sicurezza bloccante. Ruota immediatamente la credenziale
    esposta, poi rimuovi o sostituisci l'URL di riferimento incriminato. Non committare il
    segreto nella history.

---

## Logica di scansione ibrida

Zenzic applica regole di scansione diverse alla prosa e ai blocchi di codice perché i due
contesti hanno profili di rischio diversi:

| Posizione del contenuto | Shield (segreti) | Sintassi snippet | Validazione link/ref |
| :--- | :---: | :---: | :---: |
| Prosa e definizioni di riferimento | ✓ | — | ✓ |
| Blocco delimitato — linguaggio supportato (`python`, `yaml`, `json`, `toml`) | ✓ | ✓ | — |
| Blocco delimitato — linguaggio non supportato (`bash`, `javascript`, …) | ✓ | — | — |
| Blocco delimitato — senza etichetta (` ``` `) | ✓ | — | — |

**Perché i link sono esclusi dai blocchi delimitati:** gli esempi di documentazione contengono
spesso URL illustrativi (`https://api.example.com/v1/users`) che non esistono come endpoint
reali. Controllarli produrrebbe centinaia di falsi positivi senza alcun valore di sicurezza.

**Perché i segreti sono inclusi ovunque:** una credenziale incorporata in un esempio `bash` è
comunque un segreto committato. Vive nella git history, viene indicizzato dagli strumenti di
ricerca nel codice e può essere estratto da scanner automatici che non rispettano la formattazione
Markdown.

**Perché la verifica sintattica è limitata ai parser noti:** validare Bash o JavaScript
richiederebbe parser di terze parti o sottoprocessi, violando il Pilastro No-Subprocess. Zenzic
valida solo ciò che può validare in puro Python.

---

## Accessibilità alt-text

`zenzic check references` segnala anche le immagini prive di alt text significativo:

- **Immagini Markdown inline** — `![](url)` o `![   ](url)` (alt string vuota)
- **Tag HTML `<img>`** — `<img src="...">` senza attributo `alt`, o `alt=""` senza contenuto

Un `alt=""` esplicitamente vuoto viene trattato come decorativo intenzionale e **non** viene
segnalato. Un attributo `alt` completamente assente, o alt text con solo spazi, viene segnalato
come warning.

I finding di alt-text sono warning — appaiono nel report ma non influenzano il codice di
uscita a meno che `--strict` non sia attivo.

---

## Utilizzo programmatico

Importa le funzioni scanner di Zenzic direttamente nei tuoi tool Python.

### Scansione di un singolo file

Usa `ReferenceScanner` per eseguire la pipeline a tre pass su un singolo file:

```python
from pathlib import Path
from zenzic.core.scanner import ReferenceScanner

scanner = ReferenceScanner(Path("docs/guide.md"))

# Pass 1 — harvest definizioni; raccoglie i security finding
security_findings = []
for lineno, event_type, data in scanner.harvest():
    if event_type == "SECRET":
        security_findings.append(data)
        # In produzione: raise SystemExit(2) o typer.Exit(2) qui

# Pass 2 — risolve i reference link (deve essere dopo harvest)
cross_check_findings = scanner.cross_check()

# Pass 3 — calcola il punteggio di integrità e consolida tutti i finding
report = scanner.get_integrity_report(cross_check_findings, security_findings)

print(f"Punteggio integrità: {report.score:.1f}")
for f in report.findings:
    level = "WARN" if f.is_warning else "ERROR"
    print(f"  [{level}] {f.file_path}:{f.line_no} — {f.detail}")
```

### Scansione multi-file

Usa `scan_docs_references_with_links` per scansionare ogni file `.md` in un repository e
facoltativamente validare gli URL esterni:

```python
from pathlib import Path
from zenzic.core.scanner import scan_docs_references_with_links
from zenzic.models.config import ZenzicConfig

config, _ = ZenzicConfig.load(Path("."))

reports, link_errors = scan_docs_references_with_links(
    Path("."),
    validate_links=True,   # imposta False per saltare la validazione HTTP
    config=config,
)

for report in reports:
    if report.security_findings:
        raise SystemExit(2)   # il tuo codice è responsabile dell'applicazione del codice di uscita
    for finding in report.findings:
        print(finding)

for error in link_errors:
    print(f"[LINK] {error}")
```

`scan_docs_references_with_links` deduplica gli URL esterni sull'intero albero della
documentazione prima di inviare richieste HTTP — 50 file che linkano allo stesso URL producono
esattamente una richiesta HEAD.

### Scansione parallela (repository grandi)

Per repository con più di ~200 file Markdown, usa `scan_docs_references_parallel`:

```python
from pathlib import Path
from zenzic.core.scanner import scan_docs_references_parallel

reports = scan_docs_references_parallel(Path("."), workers=4)
```

La modalità parallela usa `ProcessPoolExecutor`. La validazione degli URL esterni non è
disponibile in modalità parallela — usa `scan_docs_references_with_links` per la scansione
sequenziale con validazione dei link.

---

## Esclusione di code block e frontmatter

L'harvester e il cross-checker saltano entrambi il contenuto che non dovrebbe mai produrre
finding:

- **YAML frontmatter** — il blocco `---` iniziale (solo prima riga) viene saltato per intero,
  inclusa qualsiasi sintassi simile a reference che potrebbe contenere.
- **Fenced code block** — le righe dentro i fence ` ``` ` o `~~~` vengono ignorate. Gli URL
  negli esempi di codice non producono mai falsi positivi.

Questa esclusione viene applicata in modo coerente sia nel Pass 1 che nel Pass 2.

---

## Documentazione multilingue

Quando il tuo progetto usa i18n MkDocs o il sistema di locale di Zensical, Zenzic si adatta
automaticamente:

- **Directory locale soppresse dal rilevamento orfani** — i file sotto `docs/it/`, `docs/fr/`,
  ecc. non vengono segnalati come orfani. L'adapter rileva le directory locale dalla
  configurazione i18n dell'engine.
- **Risoluzione dei link cross-locale** — gli adapter MkDocs e Zensical risolvono i link che
  attraversano i confini di locale senza falsi positivi.
- **La modalità Vanilla salta completamente il controllo orfani** — quando non è presente alcuna
  config del motore di build, ogni file sembrerebbe un orfano. Zenzic salta il controllo
  piuttosto che segnalare rumore.

!!! tip "Forza la modalità Vanilla per sopprimere il controllo orfani"
    ```bash
    zenzic check all --engine vanilla
    ```

[syntax]: https://spec.commonmark.org/0.31.2/#link-reference-definitions
