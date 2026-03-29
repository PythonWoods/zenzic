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
| `tests` | - | `nox -s tests` | pytest + branch coverage |
| `lint` | `just lint` | `nox -s lint` | linting ruff + self-check zenzic |
| `format` | - | `nox -s format` | formattazione ruff |
| `typecheck` | - | `nox -s typecheck` | mypy strict |
| `reuse` | - | `nox -s reuse` | conformità alle licenze REUSE/SPDX |
| `security` | - | `nox -s security` | scansione vulnerabilità CVE pip-audit |
| `docs` | `just dev` | `nox -s docs` | mkdocs build --strict |
| `preflight` | `just deploy` | `nox -s preflight` | tutto quanto sopra |
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

## Sicurezza & Conformità

- **Sicurezza Piena:** Prevenire manipolazioni estese con `PathTraversal`. Verificare il bypass con Pathing Check su codebase in logica risolvitiva nativa `core`.
- **Parità Bilingua:** Aggiornamenti standard devono fluire nella traduzione cartelle come logica copy-mirror da `docs/*.md` in cartellatura folder-mode a `docs/it/*.md`.
- **Integrità Base Asset:** Badges documentate presso file risorsa SVG (e.g. `docs/assets/brand/`) non andranno rimosse asincronizzate ai parametri calcolo punteggi app logic score.

---

## Creazione di un nuovo Check

Gli strumenti di analisi del sistema Zenzic vengono raccolti in `src/zenzic/core/`.
Ogni strumento di valutazione si affianca ad apposite specifiche moduli per funzioni su directory d'ispezione locale: elaborati fs resource loop da `scanner.py` e testo di contenuto validato via test ruleset standard `validator.py`. CLI controller risiede invece su parametrizzazioni subshell comandi in modulo base `cli.py`.

Quando si inserisce una nuova validazione o check test code è preferibile seguire:

1. Modula logic target base a destinazione tool apposito file (`zenzic.core.scanner` o nativo text-match `zenzic.core.validator`).
2. **Path check resolving dovrà SEMPRE dipendere da proxy interface internal resolver** — Mai chiamate API OS (`os.path.exists()`, `Path.is_file()`). `InMemoryPathResolver`. Nessun loop su sys call allocazione su memoria e istanza per-file singola disposta a buffer allocation da tree `_lookup_map` nativa da pass zero pre-read content build. Performance drops andrebbero intese su calo vertiginoso da ~430.000 resolutions-loop per-seconds a rovinose <30.000 risoluzioni/sec violando premesse "Zero I/O in the hot path". Più dettagli consultabili su: [Legge Core Zero I/O nel percorso critico](#zero-io-nel-percorso-critico).
3. Esemplifica test configurati a determinismo validato cross locale per app properties testuale estensione IT locale compatibili se toccati link local files: testarlo via monolingua monolingual test-mode, folder i18n mode fallback test. Trovi i dettagli consultando la rule base: [Determinismo i18n](#determinismo-i18n).
4. Fornisce e correla una specifica direttiva sub-command test runner test per avvio app tramite test in runtime subcli via core app framework wrapper arg parser integrato all'interfaccia sorgente root `cli.py`.
5. Prepara unit testing check base test validation con test fail over su repo in locale `tests/` verificato memory corpus e timing memory block limit risolvendo test benchmark su mock in memory link res loop <= 100 ms limit runtime budget over limit quota 5000 link iterazione in loop res check testing buffer size alloc res block tests limite buffer quota pass tests rules max target runtime budget limit test 100 millisecond array array array.
6. Assicura ed esplicita build manual validation su integrazione build tools doc files build update: la suite documenterà autonomo check locale pre pass pr `docs/` in CI zenzic linter run self pass via check target limit quota in action pipeline su file su branch.

> **Contratto prestazionale operazionale rule target pass fail strict buffer array limit pass benchmark limit limit max performance requirement rule:** L'applicativo kernel app system engine app in `zenzic.core` in "hot path run res check memory pass resolver resolve check execution validator check rule" **deve rimanere** e operare con allocazione RAM target quota nulla senza costrutto inneschi system app path instanze oggetti costrutti allocazioni IO e `Path` o relative sys path in loop sys call memory app OS call per cicli runtime. Maggior chiarezza e specifica operativa applicativa kernel Zenzic architecture target requirements documentata app su: `docs/architecture.md` sub target heading index `IO Purity contract` res app kernel spec docs e `Contributor rules`.

---

## Documentazione

Zenzic integra `docs/` e implementa lo standard target applicativo front-end user experience in framework front generator template documentale base con stack tool via estensione Material via plugin arch applicativo framework nativa estesa plugin **MkDocs Material** framework web generator docs in framework app standard build locale app docs generator docs tool per il deployment app web standard per estensione base app e la produzione doc test in docs tool.
Mutazioni, miglioramenti in comportamento target UX user app manual o variazioni feature doc standard applicative framework system require manual in target documentazione test manual zenzic standard docs `zenzic check all --strict` imposta rigoroso strict rule engine build local e remoto in pipeline validation per validare branch PR pull test PR PR PR update docs PR review validation failure arresta pull check rule limit.

Standard docs app docs framework frontend installato impiega assets design vector test per icon sets asset bundle vector UX in base pack app vector UX icon pack vector vector bundle asset design asset UI applicativo UX design framework **Lucide** vector vector set pre asset download in bundle asset tool pre fetch download nox vector bundle icon fetch pre app run nox dev dev dev asset asset pre install. Estraendolo e non pushandolo nel git log app test repository `overrides/.icons/lucide/`. Fetching pre rendering command `nox -s dev` pre app deploy in init local locale run. Esecuzioni a venire `mkdocs serve` non test richiedono bundle refresh init o ricalcoli asset update.

Modalità in visione server manual mode rapida per visione anteprima su browser app tool web locale web localhost server rendering:

```bash
mkdocs serve
```

Per l'approvazione e la compilazione d'integrità nativa finale formale build mode locale pre release action system local app terminal build test zenzic nox:

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
