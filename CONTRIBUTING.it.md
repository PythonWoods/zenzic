# Contribuire a Zenzic

Grazie per il tuo interesse nel contribuire a Zenzic!

Zenzic è uno strumento per la qualità della documentazione — un linter engine-agnostic e
uno scudo di sicurezza per documentazione Markdown e MDX. I contributi che migliorano la
precisione del rilevamento, aggiungono nuovi tipi di controlli o migliorano l'integrazione
CI/CD sono particolarmente apprezzati.

## Due Repository, Due Porte

Zenzic è diviso in due repository indipendenti:

| Repository | Scopo | Stack |
|:-----------|:------|:------|
| **[zenzic](https://github.com/PythonWoods/zenzic)** (questo repo) | Motore di analisi Core — libreria Python e CLI | Python 3.11+, `uv`, `pytest`, `mypy` |
| **[zenzic-doc](https://github.com/PythonWoods/zenzic-doc)** | Sito di documentazione utente | React, Docusaurus v3, MDX |

**Se vuoi contribuire al motore di analisi** (nuovi check, adapter, bug fix,
miglioramenti prestazionali) — sei nel posto giusto.

**Se vuoi contribuire alla documentazione** (guide, tutorial, traduzioni) —
dirigiti verso [zenzic-doc](https://github.com/PythonWoods/zenzic-doc).

---

## Missione

Zenzic non è solo un linter. È un livello di sicurezza a lungo termine per i team di
documentazione che dipendono da file sorgente aperti e verificabili. Preserviamo la
continuità della validazione attraverso i cambiamenti di motore (MkDocs, Docusaurus,
Zensical e futuri adapter) affinché i progetti mantengano il controllo sui propri dati
e processi di qualità indipendentemente dall'evoluzione dell'ecosistema.

---

## Inizio rapido

```bash
git clone git@github.com:PythonWoods/zenzic.git
cd zenzic
just sync
```

`just sync` installa tutti i gruppi di dipendenze tramite `uv sync --all-groups`.

---

## Esecuzione dei task

I controlli di qualità e le attività di sviluppo sono guidati da **just** (per la velocità) e **nox** (per le sessioni CI formali):

| Sessione | Comando Just | Comando Nox | Descrizione |
|---|---|---|---|
| Bootstrap | `just sync` | — | Installa / aggiorna tutti i gruppi di dipendenze |
| **Self-lint** | **`just check`** | — | **Esegui Zenzic sui propri esempi (strict)** |
| `tests` | `just test` | `nox -s tests` | pytest + branch coverage (profilo Hypothesis **dev**) |
| `tests` (approfondito) | `just test-full` | — | pytest con profilo Hypothesis **ci** (500 esempi) |
| `mutation` | — | `nox -s mutation` | mutmut su `rules.py`, `shield.py`, `reporter.py` |
| `preflight` | `just preflight` | `nox -s preflight` | lint, typecheck, test, reuse, security |
| **Pre-push gate** | **`just verify`** | — | **preflight + self-lint — esegui prima di ogni push** |
| `clean` | `just clean` | — | Rimuove `dist/`, `.hypothesis/`, cache |
| `bump` | — | `nox -s bump -- patch` | avanza la versione + commit + tag |

Esegui il controllo pre-PR completo con:

```bash
just verify
```

### Compatibilità cross-platform

Zenzic è validato su Ubuntu, Windows e macOS ad ogni commit. Quando si lavora con percorsi
di file in qualsiasi contributo, utilizza `pathlib.Path` — mai concatenazione di stringhe o
`os.sep`. Regole fondamentali:

- `Path("a") / "b"` — sempre, mai `"a" + os.sep + "b"` o `"a/b"` come letterale stringa.
- Usa `.as_posix()` solo nel punto di confronto con URL o valori di configurazione in stile POSIX.
- Le fixture di test che costruiscono percorsi devono usare `tmp_path / "subdir"`, non `"/tmp/subdir"`.
- Le PR che introducono concatenazione di percorsi con `str` saranno rifiutate dalla matrice CI cross-platform.

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

### Zero I/O nel percorso critico {#zero-io-in-the-hot-path}

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

### Determinismo i18n {#i18n-determinism}

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

Zenzic supporta entrambe le strategie i18n utilizzate da `mkdocs-static-i18n`:

- **Modalità suffisso** (`filename.locale.md`) — I file tradotti sono affiancati agli originali alla stessa profondità di directory. I percorsi degli asset relativi sono simmetrici tra le lingue. Zenzic rileva automaticamente i suffissi locale dai nomi dei file, senza alcuna configurazione aggiuntiva.
- **Modalità cartella** (`docs/it/filename.md`) — I locale non predefiniti risiedono in una directory di primo livello. Il rilevamento degli asset e degli orfani è gestito da `MkDocsAdapter` tramite `[build_context]` in `zenzic.toml`. In assenza di `zenzic.toml`, Zenzic legge la configurazione locale direttamente da `mkdocs.yml`.

**Divieto di Link Assoluti**
Zenzic rifiuta qualsiasi link interno che inizi con `/`. I percorsi assoluti presuppongono che il sito sia ospitato alla radice del dominio: se la documentazione viene servita da una sottodirectory (es. `https://example.com/docs/`), un link come `/assets/logo.png` si risolve in `https://example.com/assets/logo.png` (404), non nell'asset desiderato. Usa percorsi relativi (`../assets/logo.png`) per garantire la portabilità indipendentemente dall'ambiente di hosting.

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

### Protocollo di Scoperta della Radice (PSR)

`find_repo_root()` è il singolo punto di ingresso attraverso cui Zenzic stabilisce il confine del suo **Workspace**. Tutto il resto — costruzione della VSM, risoluzione dei link, caricamento della configurazione — dipende dal percorso che restituisce. Trattalo come infrastruttura portante.

#### L'Autorità della Radice

Zenzic non analizza file in isolamento. Analizza un **Workspace**: un insieme delimitato di file le cui relazioni — link, ancore, voci di nav, stato orfano — sono significative solo relativamente a una radice condivisa. La Radice è la parete esterna invalicabile della VSM. Un controllo che sfugge a questa parete non è un controllo Zenzic; è una vulnerabilità.

#### Ereditarietà dello Standard — Perché `.git`?

`.git` è usato come proxy della volontà dichiarata dall'utente. La presenza di una directory `.git` significa che l'utente ha già stabilito un confine VCS per questo progetto. Zenzic eredita quel confine invece di inventarne uno proprio. Questo mantiene Zenzic forward-compatible con future esclusioni basate su `.gitignore`: automatizza l'esclusione di `site/`, `dist/` e altri artefatti generati già presenti nella maggior parte dei file `.gitignore`.

`zenzic.toml` è il marcatore di fallback per ambienti senza VCS (es. un progetto solo di documentazione, un container CI con checkout superficiale). Se `zenzic.toml` esiste, Zenzic usa la sua directory come radice — senza bisogno di `.git`.

#### Sicurezza per Opt-in — Il Default Deve Essere Sicuro

Il comportamento di fallimento per impostazione predefinita è intenzionale. Un'invocazione di `zenzic check all` da `/home/utente/` senza alcun marcatore di radice in tutta la catena degli antenati solleva `RuntimeError` immediatamente, prima che venga letto un singolo file. Questa non è una mancanza di usabilità — è una **garanzia di sicurezza**. L'alternativa (default silenzioso alla CWD o alla radice del filesystem) esporrebbe Zenzic all'Indicizzazione Massiva Accidentale: scansione di migliaia di file non correlati, produzione di risultati privi di senso e potenziale perdita di informazioni attraverso confini di progetto in ambienti CI.

**La mutazione di questo default richiede approvazione dell'Architecture Lead.** Una PR che cambia `fallback_to_cwd=False` in `True` in qualsiasi call site diverso da `init` è una violazione di sicurezza di Grado-1 e verrà chiusa senza revisione.

#### L'Eccezione di Bootstrap

Solo `zenzic init` è esente dal requisito rigoroso della radice. Il suo scopo è *creare* il marcatore di radice — richiedere che il marcatore pre-esista sarebbe il Paradosso di Bootstrap (ZRT-005). L'esenzione è codificata come parametro keyword-only affinché il call site sia auto-documentante e verificabile per ispezione:

```python
# ✅ Consentito solo in cli.py::init — crea un nuovo perimetro da zero
repo_root = find_repo_root(fallback_to_cwd=True)

# ✅ Tutti gli altri comandi — applicazione rigorosa del perimetro, solleva fuori da un repo
repo_root = find_repo_root()
```

Aggiungere `fallback_to_cwd=True` a qualsiasi comando diverso da `init` richiede un Architecture Decision Record che spieghi perché quel comando necessita di accesso senza perimetro.

Vedi [ADR 003](https://zenzic.dev/docs/explanation/discovery/) per la motivazione completa e la storia della modifica ZRT-005.

### Il Motore di Discovery

Tutta la scoperta dei file in `src/zenzic/core/` passa attraverso un singolo punto
d'ingresso: `iter_markdown_sources()` in `discovery.py`. Le chiamate dirette a
`Path.rglob()`, `os.walk()`, o `Path.iterdir()` da scanner, validator, o Shield
sono proibite per design.

Ogni funzione in `scanner.py` e `validator.py` che accede al filesystem prende un
parametro obbligatorio `exclusion_manager: LayeredExclusionManager`. Non esistono
wrapper `Optional` e nessun fallback `None` — il manager deve essere costruito
prima dell'ingresso e passato esplicitamente.

```python
# ✅ Corretto — ExclusionManager obbligatorio, punto d'ingresso unico
from zenzic.core.discovery import iter_markdown_sources

for md_file in iter_markdown_sources(docs_root, config, exclusion_manager):
    content = md_file.read_text(encoding="utf-8")

# ❌ Errato — rglob aggira il modello di Esclusione a Livelli
for md_file in docs_root.rglob("*.md"):
    ...
```

Il `LayeredExclusionManager` implementa una gerarchia di esclusione a 4 livelli:

| Livello | Nome | Sorgente | Mutabile? |
| :---: | :--- | :--- | :---: |
| **L1** | Guardrail di Sistema | `SYSTEM_EXCLUDED_DIRS` (hardcoded) | No |
| **L2** | Inclusioni Forzate + VCS | `included_dirs`, `.gitignore` | Config |
| **L3** | Esclusioni Config | `excluded_dirs`, `excluded_file_patterns` | Config |
| **L4** | Override CLI | `--exclude-dir`, `--include-dir` | Per-run |

**Standard per i test:** Tutti i test che necessitano di un `ExclusionManager`
devono usare `make_mgr()` da `tests/_helpers.py`:

```python
from _helpers import make_mgr

def test_my_scanner_function(tmp_path: Path) -> None:
    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=tmp_path, docs_root=tmp_path / "docs")
    result = my_function(tmp_path / "docs", config, mgr)
    ...
```

Non importare `make_mgr` da `conftest.py` — non è importabile sotto
`--import-mode=importlib`. Il modulo `_helpers.py` è reso importabile tramite
`pythonpath = ["tests"]` in `pyproject.toml`.

---

## Sicurezza & Conformità

- **Sicurezza Prima di Tutto:** Qualsiasi nuova risoluzione di percorso DEVE essere testata contro il Path Traversal. Usa la logica `PathTraversal` da `core`.
- **Test di Offuscamento Shield:** Ogni nuovo pattern Shield o regola normalizzatore DEVE includere test di regressione sull'offuscamento: caratteri di formato Unicode (categoria Cf), codifica HTML entity, interleaving di commenti (HTML `<!-- -->` e MDX `{/* */}`), e token divisi su più righe. Vedi `tests/test_shield_obfuscation.py` come riferimento.
- **Parità Bilingue:** La documentazione risiede in [zenzic-doc](https://github.com/PythonWoods/zenzic-doc). Indirizza lì i contributori di documentazione.

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
cablaggio CLI si trova nel package `cli/` (`src/zenzic/cli/`).

Quando si aggiunge un nuovo check:

1. Implementa la logica nel modulo core appropriato (`zenzic.core.scanner` o `zenzic.core.validator`).
2. **Qualsiasi logica di risoluzione link o path DEVE delegare a `InMemoryPathResolver`** — non
   chiamare mai `os.path.exists()`, `Path.is_file()`, o qualsiasi altra verifica filesystem
   all'interno di un loop per-link. Il resolver viene istanziato una volta prima del loop;
   la re-istanziazione per file annulla il `_lookup_map` pre-calcolato e riduce il throughput
   da 430 000+ a meno di 30 000 risoluzioni/s.
   Vedi [Leggi Core — Zero I/O nel percorso critico](#zero-io-in-the-hot-path).
3. Se il check riguarda path di file, testalo nelle tre configurazioni i18n.
   Vedi [Leggi Core — Determinismo i18n](#i18n-determinism).
4. Aggiungi un comando corrispondente (o sotto-comando) nel package `cli/` — vedi [Architettura CLI](#cli-architecture) sotto.
5. Scrivi test in `tests/` che coprono sia i casi di successo che quelli di fallimento,
   incluso un benchmark prestazionale (5 000 link risolti in < 100 ms su corpus mock in memoria).
6. Aggiorna gli esempi in `examples/` per esercitare il nuovo check — Zenzic valida i propri
   esempi ad ogni commit.

> **Contratto prestazionale:** il percorso critico di `zenzic.core` deve rimanere privo di
> allocazioni. Nessuna costruzione di oggetti `Path`, nessuna syscall, e nessuna chiamata
> `relative_to()` all'interno del loop di risoluzione.
> Vedi `docs/architecture.md` — sezioni *IO Purity contract* e *Contributor rules*.

---

## Architettura CLI {#cli-architecture}

La CLI è organizzata come **package** (`src/zenzic/cli/`) anziché come modulo singolo. Ogni file è responsabile di un dominio specifico:

| Modulo | Responsabilità |
|:-------|:---------------|
| `_shared.py` | Singleton `console`, singleton `_ui`, `configure_console()`, e tutte le utility trasversali ai comandi (`_build_exclusion_manager`, `_output_json_findings`, `_render_link_error`, ecc.) |
| `_check.py` | Sub-app Typer `check_app` + sette comandi `check *` e i loro helper privati |
| `_clean.py` | Sub-app Typer `clean_app` + comando `clean assets` |
| `_plugins.py` | Sub-app Typer `plugins_app` + comando `plugins list` |
| `_standalone.py` | Comandi `score`, `diff`, e `init` + i loro helper privati |
| `__init__.py` | Superficie di re-export pubblica consumata da `main.py` — **non aggiungere logica qui** |

### Il Custode dello Stato Visivo

`_shared.py` è il **solo proprietario di tutto lo stato console e UI**. Questa è la regola architetturale più critica del layer CLI:

> **DIVIETO:** Nessun modulo di comando può istanziare `Console()` o `ObsidianUI()` direttamente. Tutto l'output deve passare attraverso `get_ui()` e `get_console()` di `_shared.py`.

```python
# ✅ Corretto — in qualsiasi modulo _check.py / _clean.py / _standalone.py
from . import _shared
_shared.get_ui().print_header(__version__)
_shared.get_console().print("output")

# ❌ VIETATO — non farlo mai in un modulo di comando
from rich.console import Console
from zenzic.ui import ObsidianUI
console = Console(...)      # rompe lo stato condiviso
ui = ObsidianUI(console)    # crea un'istanza orfana
```

Questa regola esiste perché `configure_console()` sostituisce i singleton `console` e `_ui` a livello di modulo quando vengono passati `--no-color` o `--force-color`. Qualsiasi istanza locale di `Console` o `ObsidianUI` rimarrà congelata allo stato pre-flag e ignorerà la preferenza colore dell'utente.

Il parametro `force_terminal` del `Console` a livello di modulo è sempre `None` (rilevamento automatico via `sys.stdout.isatty()`), mai `False` (che disabiliterebbe esplicitamente il colore). Impostare `force_terminal=False` è un bug silenzioso che rimuove tutti gli stili ANSI anche nei terminali interattivi.

### Aggiungere un comando a una sub-app esistente

```python
# src/zenzic/cli/_check.py (esempio: aggiungere "check metadata")
@check_app.command(name="metadata")
def check_metadata(path: Path = ...) -> None:
    ...
```

Non sono necessarie modifiche a `__init__.py` o `main.py` — Typer rileva automaticamente il nuovo sotto-comando.

### Aggiungere una nuova sub-app di primo livello

1. Crea `src/zenzic/cli/_miafeature.py` con `miafeature_app = typer.Typer(...)` e i tuoi comandi.
2. Esporta `miafeature_app` da `src/zenzic/cli/__init__.py`.
3. Registra in `src/zenzic/main.py`: `app.add_typer(miafeature_app, name="miafeature", rich_help_panel="...")`.
4. Se la sub-app usa `no_args_is_help=True`, aggiungi `"miafeature"` al frozenset `_SUBAPPS_WITH_MENU` in `cli_main()` affinché il banner Zenzic appaia quando la sub-app viene invocata senza argomenti.

---

## Documentazione

La documentazione utente di Zenzic risiede in un repository separato:
**[zenzic-doc](https://github.com/PythonWoods/zenzic-doc)** (Docusaurus v3, React, MDX).

Questo repository core contiene solamente:

- `README.md` / `README.it.md` — panoramica del progetto e avvio rapido.
- `CONTRIBUTING.md` / `CONTRIBUTING.it.md` — guida per sviluppatori (questo file).
- `examples/` — fixture mantenuti che Zenzic auto-valida.

Per contribuire alla documentazione, apri una PR nel repository `zenzic-doc`.

---

## QA Avanzato: Mutanti & Proprietà

Zenzic usa due tecniche di test avanzate per garantire che il cuore della Sentinella sia indurito.

### Test Basati sulle Proprietà (Hypothesis)

`tests/test_properties.py` usa [Hypothesis](https://hypothesis.readthedocs.io/) per generare
migliaia di input casuali e verificare **invarianti** che devono valere per qualsiasi input:

- `extract_links()` non va mai in crash, restituisce sempre `LinkInfo`, i numeri di riga rimangono nel range.
- `slug_heading()` è in minuscolo, idempotente e privo di trattini iniziali/finali.
- `CustomRule.check()` restituisce finding validi con `col_start` nel range.
- `InMemoryPathResolver.resolve()` restituisce sempre un tipo di esito valido e intercetta il path traversal.

Esegui i test sulle proprietà:

```bash
uv run pytest tests/test_properties.py -x -q
```

### Mutation Testing (mutmut)

[mutmut](https://mutmut.readthedocs.io/) modifica il codice sorgente (es. cambia `>` in `>=`)
e verifica se la suite di test intercetta la mutazione. Un mutante sopravvissuto indica una lacuna nei test.

Modulo target: `src/zenzic/core/rules.py` — il cuore della logica di rilevamento della Sentinella.

Esegui il mutation testing:

```bash
nox -s mutation
```

**Requisito per il merge:** qualsiasi nuova regola core deve raggiungere un **mutation score > 90%**. Se `mutmut`
riporta mutanti sopravvissuti in `rules.py`, aggiungi test mirati prima del merge.

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
