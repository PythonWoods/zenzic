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

## Sicurezza & Conformità

- **Sicurezza Piena:** Prevenire manipolazioni estese con `PathTraversal`. Verificare il bypass con Pathing Check su codebase in logica risolvitiva nativa `core`.
- **Parità Bilingua:** Aggiornamenti standard devono fluire nella traduzione cartelle come logica copy-mirror da `docs/*.md` in cartellatura folder-mode a `docs/it/*.md`.
- **Integrità Base Asset:** Badges documentate presso file risorsa SVG (e.g. `docs/assets/brand/`) non andranno rimosse asincronizzate ai parametri calcolo punteggi app logic score.

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
