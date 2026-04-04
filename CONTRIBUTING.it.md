# Contribuire a Zenzic

Grazie per il tuo interesse nel contribuire a Zenzic!

Zenzic è uno strumento per la qualità della documentazione — un linter rigoroso e un wrapper di build per i siti MkDocs. I contributi che migliorano la precisione del rilevamento, aggiungono nuovi tipi di controlli o migliorano l'integrazione CI/CD sono particolarmente apprezzati.

---

## Inizio rapido

```bash
git clone git@github.com:PythonWoods/zenzic.git
cd zenzic
uv sync --group dev
nox -s dev
```

`nox -s dev` installa i pre-commit hook e scarica il set di icone Lucide in
`overrides/.icons/lucide/` (necessario per `mkdocs serve` e `mkdocs build`).
Questa directory è esclusa da git — è un asset di build generato automaticamente.

---

## Esecuzione dei task

I controlli di qualità e le attività di sviluppo sono guidati da **just** (per la velocità) e **nox** (per le sessioni CI formali):

| Sessione | Comando Just | Comando Nox | Descrizione |
|---|---|---|---|
| `dev` | - | `nox -s dev` | installa i pre-commit hook + scarica icone Lucide (da eseguire una volta dopo il clone) |
| `tests` | `just test` | `nox -s tests` | pytest + branch coverage (profilo Hypothesis **dev**) |
| `tests` (approfondito) | `just test-full` | - | pytest con profilo Hypothesis **ci** (500 esempi) |
| `mutation` | - | `nox -s mutation` | mutmut su `src/zenzic/core/rules.py` |
| `lint` | `just lint` | `nox -s lint` | linting ruff + self-check zenzic |
| `format` | - | `nox -s format` | formattazione ruff |
| `typecheck` | - | `nox -s typecheck` | mypy strict |
| `reuse` | - | `nox -s reuse` | conformità alle licenze REUSE/SPDX |
| `security` | - | `nox -s security` | scansione vulnerabilità CVE pip-audit |
| `docs` | `just dev` | `nox -s docs` | mkdocs build --strict |
| `preflight` | `just deploy` | `nox -s preflight` | tutto quanto sopra |
| `clean` | `just clean` | - | Rimuove `site/`, `dist/`, `.hypothesis/`, cache |
| `screenshot` | - | `nox -s screenshot` | rigenera `docs/assets/screenshot.svg` |
| `bump` | - | `nox -s bump -- patch` | avanza la versione + commit + tag |

Esegui il controllo pre-PR completo con:

```bash
just deploy
```

> **Suggerimento:** Prima di fare commit sugli aggiornamenti alla documentazione, esegui `uvx zenzic clean assets` (oppure `uv run zenzic clean assets`) per eliminare automaticamente i vecchi screenshot o le immagini non più referenziate. Questo mantiene pulita la cronologia Git.

---

## Convenzioni sul codice

- **Python ≥ 3.11** con annotazioni dei tipi complete (`mypy --strict` deve passare).
- **Intestazione SPDX** in ogni file sorgente — `reuse lint` è imposto dalla CI.
- Nessun testo segnaposto, `TODO`, o commenti parziali nel codice inserito tramite commit.
- I test devono superare l'80% o più di copertura dei rami.
- Tutte le PR devono puntare a `main`; i commit diretti sono bloccati dal pre-commit.

---

## Leggi Fondamentali (non negoziabili)

Queste regole proteggono le garanzie di prestazioni e determinismo di `src/zenzic/core/`.
Una PR che viola una qualsiasi di esse verrà rifiutata indipendentemente dalla copertura dei test.

### Zero I/O nel percorso critico

`src/zenzic/core/` **non deve mai** chiamare `Path.exists()`, `Path.is_file()`, `open()`,
o qualsiasi altra operazione del filesystem o di esecuzione processi all'interno di un loop iterativo sui link o sui file.

Le due uniche fasi di I/O consentite sono:

| Fase | Dove | Cosa |
| ----- | ----- | ---- |
| **Passo 1** | Preambolo `validate_links_async` | Attraversamento con `rglob` per costruire la topologia (`md_contents` e `known_assets`) |
| **Creazione `InMemoryPathResolver`** | `__init__` | Costruzione della mappa `_lookup_map` dal dizionario dei file pre-letti |

Tutto ciò che avviene dopo il Passo 1 deve utilizzare esclusivamente strutture dati in memoria:

- Risoluzione `.md` interna → `InMemoryPathResolver.resolve()`
- Risoluzione di asset non `.md` → testata con `asset_str in known_assets` (`frozenset[str]`, O(1))
- Soppressione artefatti a tempo di build → pattern match `fnmatch` contro gli array `excluded_build_artifacts`

### Determinismo i18n

Eventuali nuove regole di convalida che coinvolgono percorsi di file **devono** essere testate in tre scenari distinti:

1. **Monolingua** — nessun plugin i18n presente in `mkdocs.yml`.
2. **Modalità suffisso (Suffix Mode)** — `docs_structure: suffix`; i file tradotti si affiancano ai rispettivi originali (`page.it.md`).
3. **Modalità cartella (Folder Mode), con fallback attivo** — `docs_structure: folder`, con configurazione `fallback_to_default: true`.

Aggiungi i tuoi casi in `tests/test_tower_of_babel.py` se riguardano file di traduzione/localizzazione locale.
I test unitari che mettono alla prova solo funzioni pure appartengono a `tests/test_validator.py`.

### Errori di configurazione i18n

Quando l'impostazione `fallback_to_default: true` ma nessuna lingua dichiara esplicitamente `default: true`, Zenzic restituisce
`ConfigurationError` (non un generico `ValueError`). Qualsiasi porzione di codice sorgente predisposta a leggere le opzioni i18n deve
preservare questo contratto essenziale: bloccarsi segnalando prontamente la mancata assegnazione, un comportamento invisibile è severamente proibito rispetto ai fallback standardizzati.

### Contratto Adapter

Ogni nuova regola introdotta di convalida orientata all'analisi di percorsi localizzati **deve interfacciarsi con il proprio adapter di framework locale**. La lettura di un file come `mkdocs.yml` usando parsatori preimpostati YAML all'interno di routine come `validator.py` o analizzatori custom `scanner.py` è esplicitamente proibita normativamente: l'adapter designato è
l'unica interfaccia fonte di verità permessa relativa alla composizione dell'albero delle topologie di cartelle.

```python
# ✅ Corretto — utilizza la risorsa dell'adapter delegato
from zenzic.core.adapter import get_adapter
adapter = get_adapter(config.build_context, docs_root)
if adapter.is_locale_dir(rel.parts[0]):
    ...

# ❌ Errato — mai avviare il parser yaml sul filesystem ad uso check
import yaml
doc_config = yaml.load(open("mkdocs.yml"))
locale_dirs = {lang["locale"] for lang in doc_config["plugins"][0]["i18n"]["languages"]}
```

I tre metodi che supportano l'interfaccia dell'adapter designato sono:

| Metodo | Firma standard | Intento |
| :--- | :--- | :--- |
| `is_locale_dir` | `(part: str) -> bool` | Appura che questo segmento analizzato indichi una sub-directory lingua? |
| `resolve_asset` | `(missing_abs: Path, docs_root: Path) -> Path \| None` | Recupero nel branch default lingua in condizione di file primario asset inesistente |
| `is_shadow_of_nav_page` | `(rel: Path, nav_paths: frozenset[str]) -> bool` | Il file target interrogato ha valenza locale di mirroring origin-nav? |

Aggiungere validazioni su motore third-party richiede lo sforzo di replicare apposita adapter class secondo struttura registrata su directory `zenzic.core.adapter` integrata al suo factory helper `get_adapter()`.

### Portabilità & Integrità i18n

Zenzic offre standard compatibile e out/box di adozione i18n implementata `mkdocs-static-i18n`:

- **Modalità suffisso** (`filename.locale.md`) — La traduzione resta vicina, posizionata all'atto in pari estensione al dominio gốc/sorgente di lavoro con cui simmetricamente convive tramite risoluzioni asset e anchor match-tree paritari. Acquisizione locale prefisso si precompila esulante extra setups.
- **Modalità cartella** (`docs/it/filename.md`) — Subdirectory appositamente confinate ed isolate per i path non-default. MkDocsAdapter ricompatterà l'albero d'orfanità e asset integrando referenze da `zenzic.toml` via property config in locale fallback configuration property array su `[build_context]` in assenza YAML sorgente main configurato su `mkdocs.yml`.

**Proibizione Link Assoluti**
Zenzic scarta rigorosamente le reference con inizializzazione `/` per non vincolarsi perentoriamente al root-doman root. Nel momento di migrazione verso public directory o hosting diramata in namespace specifici origin site (e.g. `/docs`), una reference index base come `[Home](/docs/assets/logo.png)` imploderebbe. Fai valere link interni come percorsi parent path (e.g. `../assets/logo.png`) incrementando portabilità del progetto e documentazione a lungo termine offline/online.

### Sovranità della VSM

Qualsiasi controllo di esistenza su una risorsa interna (pagina, immagine, ancora) **deve** interrogare la Virtual Site Map — mai il filesystem.

**Perché:** La VSM include le **Ghost Route** — URL canonici generati da plugin di build (es. `reconfigure_material: true`) che non hanno un file `.md` fisico su disco. Una chiamata a `Path.exists()` restituisce `False` per una Ghost Route. La VSM restituisce `REACHABLE`. La VSM è l'oracolo; il filesystem non lo è.

**Violazione di Grado 1:** Usare `os.path.exists()`, `Path.is_file()`, o qualsiasi altra probe al filesystem per validare un link interno è una violazione architetturale di Grado 1. Le PR che contengono questo pattern saranno chiuse senza revisione.

```python
# ❌ Violazione Grado 1 — interroga il filesystem, manca le Ghost Route
if (docs_root / relative_path).exists():
    ...

# ✅ Corretto — interroga la VSM
route = vsm.get(canonical_url)
if route and route.status == "REACHABLE":
    ...
```

Correlato: vedi `docs/arch/vsm_engine.md` — *Catalogo degli Anti-Pattern* per l'elenco completo delle chiamate al filesystem vietate nelle regole.

### Ghost Route Awareness

Le regole di rilevamento orfani devono rispettare le route contrassegnate come Ghost Route nella VSM. Una Ghost Route non è un orfano — è una route che il motore di build genera al momento della build da un plugin, senza un file sorgente `.md`.

**Azione:** Ogni nuova regola di scansione globale che esegue il rilevamento orfani deve accettare un parametro costruttore `include_ghosts: bool = False`. Quando `include_ghosts=False` (il default), le route con `status == "ORPHAN_BUT_EXISTING"` generate da un meccanismo Ghost Route devono essere escluse dai finding.

```python
class MiaRegolaOrfani(BaseRule):
    def __init__(self, include_ghosts: bool = False) -> None:
        self._include_ghosts = include_ghosts

    def check_vsm(self, file_path, text, vsm, anchors_cache, context=None):
        for url, route in vsm.items():
            if route.status == "ORPHAN_BUT_EXISTING":
                # Salta gli orfani derivati da Ghost Route a meno che non siano inclusi esplicitamente
                if not self._include_ghosts and _is_ghost_derived(route):
                    continue
                ...
```

## Sicurezza & Conformità

- **Sicurezza Piena:** Prevenire manipolazioni estese con `PathTraversal`. Verificare il bypass con Pathing Check su codebase in logica risolvitiva nativa `core`.
- **Parità Bilingua:** Aggiornamenti standard devono fluire nella traduzione cartelle come logica copy-mirror da `docs/*.md` in cartellatura folder-mode a `docs/it/*.md`.
- **Integrità Base Asset:** Badges documentate presso file risorsa SVG (e.g. `docs/assets/brand/`) non andranno rimosse asincronizzate ai parametri calcolo punteggi app logic score.

---

## Lo Scudo e il Canarino

Questa sezione documenta le **quattro obbligazioni di sicurezza** che si applicano a
ogni PR che tocca `src/zenzic/core/`. Una PR che risolve un bug senza soddisfare
tutte e quattro verrà rifiutata dal Responsabile Architettura.

Queste regole esistono perché l'analisi di sicurezza v0.5.0a3 (2026-04-04) ha
dimostrato che quattro scelte di design individualmente ragionevoli — ciascuna
corretta in isolamento — si sono composte in quattro distinti vettori di attacco.
Vedi `docs/internal/security/shattered_mirror_report.md` per il post-mortem completo.

---

### Obbligazione 1 — La Tassa di Sicurezza (Timeout Worker)

Ogni PR che modifica l'uso di `ProcessPoolExecutor` in `scanner.py` deve
preservare la chiamata `future.result(timeout=_WORKER_TIMEOUT_S)`. Il timeout
corrente è **30 secondi**.

**Cosa significa:**

```python
# ✅ Forma richiesta — usa sempre submit() + result(timeout=...)
futures_map = {executor.submit(_worker, item): item[0] for item in work_items}
for fut, md_file in futures_map.items():
    try:
        raw.append(fut.result(timeout=_WORKER_TIMEOUT_S))
    except concurrent.futures.TimeoutError:
        raw.append(_make_timeout_report(md_file))  # finding Z009

# ❌ Vietato — si blocca indefinitamente su ReDoS o worker in deadlock
raw = list(executor.map(_worker, work_items))
```

**Il finding Z009** (`ANALYSIS_TIMEOUT`) non è un crash. È un finding strutturato
che appare nell'interfaccia del report standard. Un worker che va in timeout non
interrompe la scansione — il coordinatore continua con i worker rimanenti.

**Se la tua modifica richiede naturalmente un timeout più lungo** (es. una nuova
regola esegue calcoli costosi), aumenta `_WORKER_TIMEOUT_S` con un commento che
spiega il costo e un benchmark che dimostra l'input peggiore.

---

### Obbligazione 2 — Il Protocollo Regex-Canary

Ogni voce `[[custom_rules]]` che specifica un `pattern` è soggetta al
**Regex-Canary**, uno stress test basato su POSIX `SIGALRM` che viene eseguito
al momento della costruzione di `AdaptiveRuleEngine`.

**Come funziona il canary:**

```python
# _assert_regex_canary() in rules.py — eseguito automaticamente per ogni CustomRule
_CANARY_STRINGS = (
    "a" * 30 + "b",   # trigger classico (a+)+
    "A" * 25 + "!",   # variante maiuscola
    "1" * 20 + "x",   # variante numerica
)
_CANARY_TIMEOUT_S = 0.1   # 100 ms
```

Il canary applica ciascuna delle tre stringhe al metodo `check()` della regola
sotto un watchdog di 100 ms. Se il pattern non si completa entro 100 ms su
qualsiasi di queste stringhe, il motore solleva `PluginContractError` prima
che la scansione inizi.

**Testare il pattern contro il canary prima di committare:**

```python
from pathlib import Path
from zenzic.core.rules import CustomRule, _assert_regex_canary
from zenzic.core.exceptions import PluginContractError

rule = CustomRule(
    id="MIA-001",
    pattern=r"il-tuo-pattern-qui",
    message="Trovato.",
    severity="warning",
)

try:
    _assert_regex_canary(rule)
    print("✅ Canary passato — il pattern è sicuro per la produzione")
except PluginContractError as e:
    print(f"❌ Canary fallito — rischio ReDoS rilevato:\n{e}")
```

Oppure dalla shell:

```bash
uv run python -c "
from zenzic.core.rules import CustomRule, _assert_regex_canary
r = CustomRule(id='T', pattern=r'IL_TUO_PATTERN', message='.', severity='warning')
_assert_regex_canary(r)
print('sicuro')
"
```

**Pattern da evitare** (trigger di backtracking catastrofico):

| Pattern | Perché pericoloso |
|---------|------------------|
| `(a+)+` | Quantificatori annidati — percorsi esponenziali |
| `(a\|aa)+` | Alternazione con sovrapposizione |
| `(a*)*` | Star annidato — match vuoti infiniti |
| `.+foo.+bar` | Multi-wildcard greedy con suffisso |

**Pattern sempre sicuri:**

| Pattern | Note |
|---------|------|
| `TODO` | Match letterale, O(n) |
| `^(BOZZA\|WIP):` | Alternazione ancorata, O(1) per posizione |
| `[A-Z]{3}-\d+` | Classi di caratteri limitate |
| `\bfoo\b` | Ancorato a word-boundary |

**Nota piattaforma:** `_assert_regex_canary()` usa `signal.SIGALRM`, disponibile
solo sui sistemi POSIX (Linux, macOS). Su Windows, il canary è un no-op. Il timeout
del worker (Obbligazione 1) è il backstop universale.

**Overhead del canary:** Misurato a **0,12 ms** per costruzione del motore con 10
regole sicure (mediana su 20 iterazioni). È un costo una-tantum all'avvio della
scansione, ben entro il budget accettabile della "Tassa di Sicurezza".

---

### Obbligazione 3 — L'Invariante Dual-Stream dello Shield

Lo stream Shield e lo stream Contenuto in `ReferenceScanner.harvest()` non devono
**mai condividere un generatore**. Questa è la lezione architetturale di ZRT-001.

```python
# ✅ CORRETTO — generatori indipendenti, contratti di filtraggio indipendenti
with file_path.open(encoding="utf-8") as fh:
    for lineno, line in enumerate(fh, start=1):  # Shield: TUTTE le righe
        list(scan_line_for_secrets(line, file_path, lineno))

for lineno, line in _iter_content_lines(file_path):  # Contenuto: filtrato
    ...

# ❌ VIETATO — condividere un generatore fa cadere il frontmatter dallo Shield
with file_path.open(encoding="utf-8") as fh:
    shared = _skip_frontmatter(fh)
    for lineno, line in shared:
        list(scan_line_for_secrets(...))   # ← cieco al frontmatter
    for lineno, line in shared:            # ← già esaurito
        ...
```

**Performance Shield:** La doppia scansione (riga grezza + normalizzata) opera a
circa **235.000 righe/secondo** (misurato: mediana 12,74 ms per 3.000 righe su
20 iterazioni). Il normalizzatore aggiunge un passaggio per riga, ma il set `seen`
previene finding duplicati, mantenendo l'output deterministico.

Se una PR fa refactoring di `harvest()` e il benchmark CI scende sotto **100.000
righe/secondo**, rifiutare e investigare prima del merge.

---

### Obbligazione 4 — Mutation Score ≥ 90% per le Modifiche Core

Ogni PR che modifica `src/zenzic/core/` deve mantenere o migliorare il mutation
score sul modulo interessato. La baseline attuale per `rules.py` è **86,7%**
(242/279 mutanti uccisi).

L'obiettivo per rc1 è **≥ 90%**. Una PR che aggiunge una nuova regola o modifica
la logica di rilevamento senza uccidere i mutanti corrispondenti sarà rifiutata.

**Eseguire il mutation testing:**

```bash
nox -s mutation
```

**Interpretare i mutanti sopravvissuti:**

Non tutti i mutanti sopravvissuti sono equivalenti. Prima di contrassegnare un
mutante come accettabile, verifica che:

1. Il mutante cambia un comportamento osservabile (non è logicamente equivalente).
2. Nessun test esistente cattura il mutante (è una lacuna genuina).
3. Aggiungere un test per ucciderlo sarebbe ridondante o circolare.

In caso di dubbio, aggiungi il test. La suite di mutation testing è un documento
vivente del modello di minaccia della Sentinella.

**Validazione pickle di ResolutionContext (Eager Validation 2.0):**

`ResolutionContext` è un `@dataclass(slots=True)` con soli campi `Path`. `Path`
è serializzabile con pickle dalla standard library. L'oggetto si serializza in
157 byte. Tuttavia, se `ResolutionContext` acquisisce un campo non serializzabile
(es. un file handle, un lock, una lambda), il motore parallelo fallirà in modo
silenzioso.

Per proteggersi da questo, qualsiasi PR che aggiunge un campo a `ResolutionContext`
deve includere:

```python
# In tests/test_redteam_remediation.py (o in un test dedicato):
def test_resolution_context_is_pickleable():
    import pickle
    ctx = ResolutionContext(docs_root=Path("/docs"), source_file=Path("/docs/a.md"))
    assert pickle.loads(pickle.dumps(ctx)) == ctx
```

Questo test esiste già nella suite di test a partire da v0.5.0a4.

**Integrità del Reporting Shield (Il Mutation Gate per il Commit 2+):**

Il requisito di conformità per il mutation score dello Shield è **più ampio**
della sola detection. Riguarda anche la **pipeline di reporting**:

> *Un segreto che viene rilevato ma non segnalato correttamente è un bug CRITICO —
> indistinguibile da un segreto che non è mai stato rilevato.*

Qualsiasi PR che tocca la funzione `_map_shield_to_finding()`, il percorso di
severità `SECURITY_BREACH` in `SentinelReporter`, o il routing dell'exit code in
`cli.py` **deve uccidere tutti e tre questi mutanti obbligatori** prima che la PR
venga accettata:

| Nome mutante | Cosa cambierebbe mutmut | Test che deve ucciderlo |
|-------------|------------------------|------------------------|
| **L'Invisibile** | `severity="security_breach"` → `severity="warning"` | L'exit code deve essere 2, non 1 |
| **L'Amnesico** | Rimuove l'offuscamento → espone il segreto completo | L'output del log non deve contenere la stringa grezza |
| **Il Silenziatore** | `findings.append(...)` → `pass` | L'asserzione sul conteggio dei finding deve fallire |

**Eseguire il mutation gate con scope sullo Shield:**

```bash
nox -s mutation -- src/zenzic/core/scanner.py
```

Risultato atteso prima del merge di qualsiasi PR Commit 2+:

```text
Killed: XXX, Survived: Y
Mutation score: ≥ 90.0%
```

Se il punteggio è sotto il 90%, aggiungi test mirati prima di riaprire la PR. Non
contrassegnare mutanti sopravvissuti come equivalenti senza l'esplicita approvazione
del responsabile architettura.

---

## Aggiungere un nuovo check

I check di Zenzic si trovano in `src/zenzic/core/`. Ogni check è una funzione autonoma in
`scanner.py` (traversal del filesystem) o `validator.py` (validazione del contenuto). Il
cablaggio CLI si trova in `cli.py`.

Quando si aggiunge un nuovo check:

1. Implementa la logica nel modulo core appropriato (`zenzic.core.scanner` o `zenzic.core.validator`).
2. **Qualsiasi logica di risoluzione link o path DEVE delegare a `InMemoryPathResolver`** — non
   chiamare mai `os.path.exists()`, `Path.is_file()`, o qualsiasi altra verifica filesystem
   all'interno di un loop per-link. Il resolver viene istanziato una volta prima del loop;
   la re-istanziazione per file annulla il `_lookup_map` pre-calcolato e riduce il throughput
   da 430 000+ a meno di 30 000 risoluzioni/s.
   Vedi [Leggi Core — Zero I/O nel percorso critico](#zero-io-nel-percorso-critico).
3. Se il check riguarda path di file, testalo nelle tre configurazioni i18n.
   Vedi [Leggi Core — Determinismo i18n](#determinismo-i18n).
4. Aggiungi un comando corrispondente (o sotto-comando) in `cli.py`.
5. Scrivi test in `tests/` che coprono sia i casi di successo che quelli di fallimento,
   incluso un benchmark prestazionale (5 000 link risolti in < 100 ms su corpus mock in memoria).
6. Aggiorna `docs/` — Zenzic valida la propria documentazione ad ogni commit.

> **Contratto prestazionale:** il percorso critico di `zenzic.core` deve rimanere privo di
> allocazioni. Nessuna costruzione di oggetti `Path`, nessuna syscall, e nessuna chiamata
> `relative_to()` all'interno del loop di risoluzione.
> Vedi `docs/architecture.md` — sezioni *IO Purity contract* e *Contributor rules*.

---

## Documentazione

Zenzic usa **MkDocs Material** per la propria documentazione (`docs/`). Qualsiasi modifica
al comportamento o nuova funzionalità deve essere documentata. `zenzic check all --strict`
viene eseguito su questo repository in CI — un check che fallisce blocca la PR.

La documentazione usa il set di icone **Lucide**, scaricato al momento della build in
`overrides/.icons/lucide/` (escluso da git). Esegui `nox -s dev` una volta dopo il clone
per scaricare le icone — dopo di ciò, `mkdocs serve` funziona senza ulteriori passaggi.

Per visualizzare la documentazione in locale:

```bash
mkdocs serve
```

Per verificare la build di produzione:

```bash
nox -s docs
```

---

## Procedure del Release (Riservato Maintainer)

I rilasci sono **semi-automatizzati**: lo sviluppatore decide il livello del bump semver, e un singolo comando fa il resto.

```bash
# 1. Assicurati che il ramo main sia pulito (preflight superato)
nox -s preflight

# 2. Fai il bump della versione, crea commit e tag automaticamente
nox -s bump -- patch     # 0.1.0 → 0.1.1  (bug fix)
nox -s bump -- minor     # 0.1.0 → 0.2.0  (nuova feature, retrocompatibile)
nox -s bump -- major     # 0.1.0 → 1.0.0  (breaking change)

# 3. Effettua il push — questo avvia il workflow di rilascio
git push && git push --tags
```

Il workflow `release.yml` a questo punto:

1. Esegue `uv build` (sdist + wheel)
2. Pubblica su PyPI tramite `uv publish` (richiede il secret `PYPI_TOKEN`)
3. Crea una GitHub Release con note generate automaticamente

Aggiorna `CHANGELOG.md` prima di effettuare il bump: sposta gli elementi da `[Unreleased]` alla nuova sezione della versione.
