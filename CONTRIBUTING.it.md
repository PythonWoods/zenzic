<!--
SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
SPDX-License-Identifier: Apache-2.0
-->

# Contribuire a Zenzic

Grazie per il tuo interesse a contribuire a Zenzic!

Zenzic è uno strumento di qualità per la documentazione — un linter e
credential scanner engine-agnostic per documentazione Markdown e MDX.
Sono particolarmente benvenuti i contributi che migliorano l'accuratezza
della detection, aggiungono nuovi tipi di check, o migliorano l'integrazione
CI/CD.

## Due Repository, Due Porte

Zenzic è suddiviso in due repository indipendenti:

| Repository | Scopo | Stack |
|:-----------|:------|:------|
| **[zenzic](https://github.com/PythonWoods/zenzic)** (questo repo) | Motore di analisi core — la libreria Python e la CLI | Python 3.10+, `uv`, `pytest`, `mypy` |
| **[zenzic-doc](https://github.com/PythonWoods/zenzic-doc)** | Sito di documentazione user-facing | React, Docusaurus v3, MDX |

**Se vuoi contribuire al motore di analisi** (nuovi check, adapter, bug fix,
miglioramenti di performance) — sei nel posto giusto.

**Se vuoi contribuire alla documentazione** (guide, tutorial, traduzioni) —
vai su [zenzic-doc](https://github.com/PythonWoods/zenzic-doc).

> **Brand System** — l'identità visiva e la reference della palette colori
> vivono su <https://zenzic.dev/assets/brand/zenzic-brand-system.html>

## Missione

Zenzic non è solo un linter. È un layer di sicurezza a lungo termine per i
documentation team che dipendono da file sorgente aperti e auditabili.
Preserviamo la continuità di validazione attraverso i cambi di engine
(MkDocs, Docusaurus, Zensical e adapter futuri) così che i progetti
mantengano il controllo sui propri dati e sul processo di qualità
indipendentemente dal turnover dell'ecosistema.

## Contratto del Contributore

Prima di proporre modifiche a rule o documentazione, i contributori devono
validare l'impatto contro il registro live dei codici e il tier ownership
model.

- **Tier ownership model:** i finding sono raggruppati nei domini Core,
    Structure e Governance; mantieni i cambi nella banda corretta.
- **Frozen contract awareness:** non alterare le superfici immutabili
    (`FROZEN_CODES`, `NON_SUPPRESSIBLE_CODES`, `PLUGIN_FORBIDDEN_EXITS`) senza
    un'esplicita decisione architetturale.
- **Inspect-first workflow:** tratta `zenzic inspect codes` come fonte di
    verità prima di modificare esempi, tabelle di check o narrative del
    changelog.

---

## Prerequisiti

| Requisito | Versione | Note |
|:----------|:---------|:-----|
| **Python** | ≥ 3.10 | Motore core e CLI (Floor); validato su 3.10 & 3.14-dev in CI |
| **uv** | latest | Package manager — `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **just** | latest | Task runner — `cargo install just` o tramite il package manager del tuo OS |
| **Node.js** | ≥ 24 | Richiesto per la CI dei docs (`zenzic-doc`) e l'upload coverage (`codecov-action@v6`) |

La libreria Python core e la CLI funzionano senza Node. Node 24 serve solo se
contribuisci al sito di documentazione o esegui la suite CI completa in
locale.

---

## Quick start

```bash
git clone git@github.com:PythonWoods/zenzic.git
cd zenzic
just sync
```

`just sync` installa tutti i gruppi di dipendenze tramite `uv sync --all-groups`.

Installa gli hook pre-commit immediatamente dopo la sync (obbligatorio):

```bash
uvx pre-commit install              # commit-stage: light hooks (ruff, format, hygiene)
```

Esegui il gate di verifica completo prima del push:

```bash
just verify
```

`just verify` è l'entry point canonico: pre-commit su tutti i file →
`pytest tests/` → `zenzic check all --strict`. La stessa sequenza gira in
GitHub Actions — **locale ≡ remoto, no drift**.

---

## Il 4-Gates Standard

Zenzic applica una pipeline di qualità deterministica con un singolo
entry-point atomico. Lo stesso `just verify` gira in tre posti:

| Stage | Trigger | Cosa esegue | Velocità |
|:------|:--------|:------------|:---------|
| **TDD inner loop** | `just test` | `pytest -n auto` (no coverage, parallel) | ⚡ instant |
| **Commit** | `git commit` | Light hooks (ruff, format, file hygiene) | < 5 s |
| **Final Guard** | `just verify` (manuale o CI) | pre-commit → `pytest tests/` → `zenzic check all --strict` | < 60 s |
| **CI** | GitHub Actions | `just verify` (identico) | matches local |

### Emergency & Break-Glass Protocol

Il bypass `--no-verify` è permesso **solo** durante outage genuini (hotfix di
produzione, infra CI down, dipendenza upstream rotta) quando il gate non può
essere riparato in tempo. Ogni bypass richiede:

1. Label `gate-bypass` sulla PR.
2. Issue da `.github/ISSUE_TEMPLATE/gate-bypass-postmortem.md`
   aperta entro 24h (blameless: dati, non colpe).
3. Menzione esplicita nello sprint CHANGELOG.

I bypass silenziosi ("ghost push") violano l'integrità del progetto e vengono
escalati al retrospective di sprint. Un bypass documentato è un'occasione
per rinforzare il gate; uno nascosto è debito tecnico.

---

## Eseguire i task

I task di sviluppo usano due layer: **just** per la velocità interattiva e
**nox** per l'isolamento riproducibile della CI. Usa `just` quotidianamente;
usa `nox` direttamente quando ti serve l'environment esatto della CI.

| Task | Comando `just` | Equivalente `nox` | Descrizione |
|:-----|:---------------|:------------------|:------------|
| Bootstrap | `just sync` | — | Installa / aggiorna tutti i gruppi di dipendenze |
| **Self-lint** | **`just check`** | — | **Esegue Zenzic sui propri esempi (strict)** |
| Test (fast) | `just test` | — | pytest `-n auto`, no coverage (TDD inner loop) |
| Test (audit) | `just test-cov` | `nox -s tests` | pytest serial + branch coverage XML (matches CI) |
| Test (thorough) | `just test-full` | — | pytest con profilo Hypothesis **ci** (500 examples) |
| Mutation testing | — | `nox -s mutation` | mutmut su `rules.py`, `credentials.py`, `reporter.py` |
| **Final Guard** | **`just verify`** | — | **pre-commit → `pytest tests/` → `zenzic check all --strict`** |
| Show version | `just version` | — | Stampa la versione corrente da bump-my-version |
| Release dry-run | `just release-dry patch` | — | Simula un bump (full diff output) |
| Release dry-run (compact) | `just release-dry patch --short` | — | Simula un bump — riepilogo a 3 righe |
| Contract check | `just release-contracts` | — | Verifica i contratti architetturali del justfile (eseguito da `verify`) |
| Clean | `just clean` | — | Rimuove `dist/`, `.hypothesis/`, cache |
| Version bump | — | `nox -s bump -- patch` | bump versione + commit + tag |

Esegui il gate pre-push completo con:

```bash
just verify
```

Valida le aspettative del code registry durante lo sviluppo con:

```bash
zenzic inspect codes
```

> **Nox — Development Checklist**
>
> Zenzic usa Nox per garantire la parità tra l'environment locale e la CI. Per
> sviluppo rapido, usa `nox -s fmt` per formattare e `nox -s tests-3.12`
> (sostituendo la tua versione Python) per eseguire i test solo sul tuo
> interprete corrente.

### Compatibilità cross-platform

Zenzic è validato su Ubuntu, Windows e macOS a ogni commit. Quando lavori con
file path in qualsiasi contributo, usa `pathlib.Path` ovunque — mai
concatenazione di stringhe o `os.sep`. Regole chiave:

- `Path("a") / "b"` — sempre, mai `"a" + os.sep + "b"` o `"a/b"` come stringa letterale.
- Usa `.as_posix()` solo al punto di confronto contro URL o valori di config in stile POSIX.
- Le test fixture che costruiscono path devono usare `tmp_path / "subdir"`, non `"/tmp/subdir"`.
- Le PR che introducono concatenazione di path con `str` saranno rifiutate dalla CI matrix cross-platform.

> **Nota CI matrix:** l'upload coverage usa `codecov/codecov-action@v6`, che richiede
> il runner environment Node 24. I runner GitHub-hosted (`ubuntu-latest`) lo
> soddisfano automaticamente; i runner self-hosted devono usare Node ≥ 24.

### CI Pillar Matrix

Zenzic adotta una strategia **Pillar Matrix** — testa i limiti invece di ogni
versione intermedia:

| Slot | OS | Python | Scopo |
|------|----|--------|-------|
| **Floor** | ubuntu-latest | `3.10` | Enforce la compatibilità minima. Se passa qui, passa ovunque ≥ 3.10. |
| **Peak** | ubuntu-latest | `3.14` | Ultima CPython stabile; target di sviluppo primario. |
| **Windows Anchor** | windows-latest | `3.14` | Valida path separator, encoding binario e shell compat su un anchor stabile. |

Se `just verify` passa sulla tua Python locale (es. 3.11 o 3.13), un
fallimento in CI è altamente improbabile — la matrix copre le condizioni al
contorno del linguaggio, non ogni minor release.

---

## Convenzioni di codice

- **Python ≥ 3.10** con type annotation complete (`mypy --strict` deve passare).
- **Header SPDX** su ogni file sorgente — `reuse lint` è enforced in CI.
- Nessun testo segnaposto, `TODO` o commento stub nel codice committato.
- I test devono passare con ≥ 80% di branch coverage.
- Tutte le PR devono targettare `main`; i commit diretti sono bloccati dal pre-commit.
- Aggiorna `CHANGELOG.md` nello stesso commit del cambio di codice.

### Convenzioni UI / Rich output

- **Usa sempre `ZenzicPalette.DIM`** (da `zenzic.core.ui`) per testo dim/secondario — mai il tag Rich raw `[dim]`. `ZenzicPalette.DIM` è l'unica autorità cromatica per Slate (`#64748b`).
- **Spacing verticale: compatto (Ruff-style).** Nessuna riga vuota tra le singole righe del footer (hint, notice, audit summary). Usa i separator `Rule()` solo per dividere le sezioni principali del report (body vs. footer).
- **Spacing orizzontale:** nessuno spazio iniziale prima dei caratteri emoji/icona nelle info line. Lascia che Rich gestisca il margine tramite panel o indent dove serve.
- **Registrazione emoji:** i nuovi simboli devono essere aggiunti a `_EMOJI` in `zenzic/core/ui.py` prima dell'uso — mai literal Unicode inline nelle stringhe di output CLI.

---

## Core Laws (non negoziabili)

Queste regole proteggono le garanzie di performance e determinismo di
`src/zenzic/core/`. Una PR che ne viola una sarà rifiutata indipendentemente
dalla copertura test.

### Zero I/O nell'hot path

`src/zenzic/core/` **non deve mai chiamare** `Path.exists()`, `Path.is_file()`,
`open()`, o qualsiasi altra operazione di filesystem o subprocess dentro un
loop per-link o per-file. <!-- zenzic-ignore: Z601 - technical programming term, not brand usage -->

Le due fasi I/O permesse sono:

| Fase | Dove | Cosa |
| ---- | ---- | ---- |
| **Pass 1** | preambolo `validate_links_async` | traversal `rglob` per costruire `md_contents` e `known_assets` |
| **Costruzione `InMemoryPathResolver`** | `__init__` | Costruzione di `_lookup_map` dal dict di contenuto pre-letto |

Tutto dopo Pass 1 deve usare solo strutture dati in-memory:

- Risoluzione interna `.md` → `InMemoryPathResolver.resolve()`
- Risoluzione asset non-`.md` → `asset_str in known_assets` (`frozenset[str]`, O(1))
- Soppressione artifact di build → `fnmatch` contro pattern `excluded_build_artifacts`

### Determinismo i18n

Ogni nuova rule di validazione che tocca file path **deve** essere testata in
tre configurazioni:

1. **Monolingua** — nessun plugin i18n in `mkdocs.yml`.
2. **Suffix-mode** — `docs_structure: suffix`; i file tradotti sono sibling (`page.it.md`).
3. **Folder-mode, fallback on** — `docs_structure: folder`, `fallback_to_default: true`.

Aggiungi i tuoi scenari a `tests/test_tower_of_babel.py` se coinvolgono file
locale. Gli unit test che esercitano solo funzioni pure vanno in
`tests/test_validator.py`.

### Errori di configurazione i18n

Quando `fallback_to_default: true` ma nessuna lingua dichiara `default: true`,
Zenzic solleva `ConfigurationError` (non un generico `ValueError`). Ogni code
path che legge config i18n deve preservare questo contratto: fail loudly con
un messaggio actionable, mai cadere silenziosamente su un locale sbagliato.

### Adapter contract

Ogni nuova rule di validazione che tocca path di locale **deve passare per
l'adapter**. Il parsing diretto YAML di `mkdocs.yml` in `validator.py` o
`scanner.py` è proibito — l'adapter è l'unica fonte di verità per la topologia
del locale.

```python
# ✅ Correct — use the adapter
from zenzic.core.adapter import get_adapter
adapter = get_adapter(config.build_context, docs_root)
if adapter.is_locale_dir(rel.parts[0]):
    ...

# ❌ Wrong — never parse mkdocs.yml for locale data inside a check
import yaml
doc_config = yaml.load(open("mkdocs.yml"))
locale_dirs = {lang["locale"] for lang in doc_config["plugins"][0]["i18n"]["languages"]}
```

I tre metodi dell'adapter contract sono:

| Metodo | Signature | Scopo |
| :--- | :--- | :--- |
| `is_locale_dir` | `(part: str) -> bool` | Questo componente del path è una locale directory? |
| `resolve_asset` | `(missing_abs: Path, docs_root: Path) -> Path \| None` | Fallback default-locale per un asset mancante |
| `is_shadow_of_nav_page` | `(rel: Path, nav_paths: frozenset[str]) -> bool` | Questo file locale è un mirror di una nav page? |

Per aggiungere il supporto a un nuovo build engine, implementa una nuova
adapter class con questi tre metodi e registrala in `get_adapter()` in
`zenzic.core.adapter`.

### Portabilità & Integrità i18n

Zenzic supporta entrambe le strategie i18n usate da `mkdocs-static-i18n`:

- **Suffix Mode** (`filename.locale.md`) — i file tradotti sono sibling degli originali alla
  stessa profondità di directory. I path relativi degli asset sono simmetrici tra lingue. Zenzic
  auto-rileva i suffissi di locale dai nomi dei file senza configurazione.
- **Folder Mode** (`docs/it/filename.md`) — i locale non-default vivono in una directory top-level.
  Link agli asset e detection degli orphan sono gestiti da `MkDocsAdapter` tramite `[build_context]` in
  `zenzic.toml`. Quando `zenzic.toml` è assente, Zenzic legge la config locale da `mkdocs.yml`.

**Proibizione degli Absolute Link**
Zenzic rifiuta qualsiasi link interno che inizi con `/`. I path assoluti presuppongono che il sito
sia hostato sulla root del dominio. Se la documentazione è servita da una subdirectory (es.
`https://example.com/docs/`), un link a `/assets/logo.png` risolve a
`https://example.com/assets/logo.png` (404), non all'asset previsto. Usa path relativi
(`../assets/logo.png`) per garantire portabilità indipendentemente dall'environment di hosting.

### VSM Sovereignty

Ogni existence check su una risorsa interna (page, image, anchor) **deve**
interrogare la Virtual Site Map — mai il filesystem.

**Perché:** la VSM include **Ghost Route** — URL canonici generati dai build
plugin (es. `reconfigure_material: true`) che non hanno alcun file `.md`
fisico su disco. Una chiamata a `Path.exists()` ritorna `False` per una Ghost
Route. La VSM ritorna `REACHABLE`. La VSM è l'oracolo; il filesystem no.

**Violazione Grade-1:** usare `os.path.exists()`, `Path.is_file()`, o
qualsiasi altra probe filesystem per validare un link interno è una violazione
architetturale Grade-1. Le PR che contengono questo pattern saranno chiuse
senza review.

```python
# ❌ Grade-1 violation — asks the filesystem, misses Ghost Routes
if (docs_root / relative_path).exists():
    ...

# ✅ Correct — asks the VSM
route = vsm.get(canonical_url)
if route and route.status == "REACHABLE":
    ...
```

Correlato: vedi `docs/arch/vsm_engine.md` — *Anti-Pattern Catalogue* per la
lista completa delle chiamate filesystem bannate dentro le rule.

### Ghost Route Awareness

Le rule di detection degli orphan devono rispettare le route flaggate come
Ghost Route nella VSM. Una Ghost Route non è un orphan — è una route che il
build engine genera al build time da un plugin, senza alcun file `.md`
sorgente.

**Azione:** ogni nuova rule global-scan che esegue detection degli orphan
deve accettare un constructor parameter `include_ghosts: bool = False`.
Quando `include_ghosts=False` (il default), le route con
`status == "ORPHAN_BUT_EXISTING"` generate da un meccanismo Ghost Route
devono essere escluse dai finding.

```python
class MyOrphanRule(BaseRule):
    def __init__(self, include_ghosts: bool = False) -> None:
        self._include_ghosts = include_ghosts

    def check_vsm(self, file_path, text, vsm, anchors_cache, context=None):
        for url, route in vsm.items():
            if route.status == "ORPHAN_BUT_EXISTING":
                # Skip Ghost Route-derived orphans unless explicitly included
                if not self._include_ghosts and _is_ghost_derived(route):
                    continue
                ...
```

### Root Discovery Protocol (RDP)

`find_repo_root()` è il singolo entry point attraverso cui Zenzic stabilisce
il suo **Workspace boundary**. Tutto il resto — costruzione VSM, risoluzione
link, caricamento config — dipende dal path che ritorna. Trattalo come
infrastruttura load-bearing.

#### L'Autorità del Root

Zenzic non analizza file in isolamento. Analizza un **Workspace**: un set
delimitato di file le cui relazioni — link, anchor, nav entry, orphan status
— sono significative solo rispetto a una root condivisa. La Root è il muro
esterno inviolabile della VSM. Un check che evade questo muro non è un check
Zenzic; è una vulnerabilità.

#### Eredità Standard — Perché `.git`?

`.git` è usato come proxy per l'intento dichiarato dall'utente. La presenza
di una directory `.git` significa che l'utente ha già stabilito un confine
VCS per questo progetto. Zenzic eredita quel confine invece di inventarne
uno proprio. Questo mantiene anche Zenzic forward-compatible con future
esclusioni `.gitignore`-aware: automatizzare l'esclusione di `site/`,
`dist/`, e altri artefatti generati che già esistono nella maggior parte
dei file `.gitignore`.

`zenzic.toml` è il marker di fallback per environment senza VCS (es. un
progetto solo-documentazione, un container CI con checkout shallow). Se
`zenzic.toml` esiste, Zenzic usa la sua directory come root — senza `.git`
richiesto.

#### Opt-in Safety — Il Default Deve Essere Sicuro

Il comportamento di failure-by-default è intenzionale. Un'invocazione di
`zenzic check all` da `/home/user/` senza alcun root marker nella catena di
antenati solleva `RuntimeError` immediatamente, prima che un singolo file
venga letto. Non è un difetto di usabilità — è una **garanzia di sicurezza**.
L'alternativa (cadere silenziosamente su CWD o sulla root del filesystem)
esporrebbe Zenzic a Massive Indexing accidentale: scansionare migliaia di
file non correlati, produrre finding senza senso, e potenzialmente trapelare
informazioni attraverso i confini del progetto in environment CI.

**La mutazione di questo default richiede l'approvazione dell'Architecture
Lead.** Una PR che cambia `fallback_to_cwd=False` in `True` in qualsiasi call
site diverso da `init` è una violazione di sicurezza Grade-1 e sarà chiusa
senza review.

#### L'Eccezione Bootstrap

Solo `zenzic init` è esente dal requisito strict di root. Il suo scopo è
*creare* il root marker — richiedere che il marker pre-esista sarebbe il
Bootstrap Paradox (ZRT-005). L'esenzione è codificata come parametro
keyword-only così il call site è auto-documentante e auditable per
ispezione:

```python
# ✅ Only permitted in cli.py::init — creates a new perimeter from scratch
repo_root = find_repo_root(fallback_to_cwd=True)

# ✅ All other commands — strict perimeter enforcement, raises outside a repo
repo_root = find_repo_root()
```

Aggiungere `fallback_to_cwd=True` a qualsiasi comando diverso da `init`
richiede un Architecture Decision Record registrato che spieghi perché quel
comando ha bisogno di accesso perimeter-free.

Vedi [ADR 003](https://zenzic.dev/docs/explanation/discovery/) per il
razionale completo e la storia degli emendamenti ZRT-005.

### Il Discovery Engine

Tutta la discovery dei file in `src/zenzic/core/` passa per un singolo entry
point: `iter_markdown_sources()` in `discovery.py`. Le chiamate dirette a
`Path.rglob()`, `os.walk()`, o `Path.iterdir()` dal codice di scanner,
validator o credential scanner sono proibite by design.

Ogni funzione in `scanner.py` e `validator.py` che tocca il filesystem
prende un parametro obbligatorio `exclusion_manager: LayeredExclusionManager`.
Non ci sono wrapper `Optional` né fallback `None` — il manager deve essere
costruito prima dell'entry e passato esplicitamente.

```python
# ✅ Correct — mandatory ExclusionManager, single entry point
from zenzic.core.discovery import iter_markdown_sources

for md_file in iter_markdown_sources(docs_root, config, exclusion_manager):
    content = md_file.read_text(encoding="utf-8")

# ❌ Wrong — rglob bypasses the Layered Exclusion model
for md_file in docs_root.rglob("*.md"):
    ...
```

Il `LayeredExclusionManager` implementa una gerarchia di esclusioni a 4 livelli:

| Livello | Nome | Sorgente | Mutabile? |
| :---: | :--- | :--- | :---: |
| **L1** | System Guardrails | `SYSTEM_EXCLUDED_DIRS` (hardcoded) | No |
| **L2** | Forced Inclusions + VCS | `included_dirs`, `.gitignore` | Config |
| **L3** | Config Exclusions | `excluded_dirs`, `excluded_file_patterns` | Config |
| **L4** | CLI Overrides | `--exclude-dir`, `--include-dir` | Per-run |

**Standard di testing:** tutti i test che necessitano di un
`ExclusionManager` devono usare `make_mgr()` da `tests/_helpers.py`:

```python
from _helpers import make_mgr

def test_my_scanner_function(tmp_path: Path) -> None:
    config = ZenzicConfig()
    mgr = make_mgr(config, repo_root=tmp_path, docs_root=tmp_path / "docs")
    result = my_function(tmp_path / "docs", config, mgr)
    ...
```

Non importare `make_mgr` da `conftest.py` — non è importabile sotto
`--import-mode=importlib`. Il modulo `_helpers.py` è reso importabile
tramite `pythonpath = ["tests"]` in `pyproject.toml`.

:::note[ADR-DEBT-001 — Test Helper Complexity Threshold]
**Status:** Observed / Monitored
**Date:** 2026-04-14
**Context:** il modulo `tests/_helpers.py` è stato introdotto in v0.6.1rc1 come
workaround di un'incompatibilità tra pytest `--import-mode=importlib` e gli
helper definiti in `conftest.py`. Il workaround è corretto e funzionale.

**Concern:** man mano che la suite di test cresce, `_helpers.py` rischia di
accumulare utility non correlate da sottosistemi multipli, diventando una de
facto "utility dumping ground". Al momento della scrittura la suite ha ~953
test. Se la suite supera i **1.200 test**, l'Architecture Lead dovrebbe
valutare lo split di `_helpers.py` in moduli di helper specifici per dominio
(`_helpers_exclusion.py`, `_helpers_discovery.py`, ecc.) usando un approccio
fixture Pytest-native.

**Criterio di accettazione per il trigger del refactor:** qualsiasi sprint che
aggiunge più di 3 categorie distinte di helper function a `_helpers.py` in
una singola PR dovrebbe aprire un'issue follow-up per il refactor.

**Owner:** Architecture Lead
:::

---

## Sicurezza & Compliance

- **Security First:** ogni nuova path resolution DEVE essere testata contro Path Traversal. Usa la logica `PathTraversal` da `core`.
- **Test di Obfuscation del Credential Scanner:** ogni nuovo pattern di credential o regola di normalizer DEVE includere test di regressione per obfuscation: caratteri Unicode format (categoria Cf), encoding HTML entity, interleaving di commenti (HTML `<!-- -->` e MDX `{/* */}`), e token spezzati cross-line. Vedi `tests/test_credentials_obfuscation.py` come reference.
- **Bilingual Parity:** la documentazione vive in [zenzic-doc](https://github.com/PythonWoods/zenzic-doc). Indirizza i contributori della documentazione lì.
- **Machine-Local Config:** i secret specifici del progetto (forbidden terms per Z204) vanno in `.zenzic.local.toml` — mai committati. Copia [`.zenzic.local.toml.example`](.zenzic.local.toml.example) come template di partenza.

### Requisiti Supply-chain

Ogni GitHub Action introdotta o modificata in questo repository deve essere
pinned a una commit SHA immutabile.

Formato richiesto:

```yaml
- uses: owner/action-name@0123456789abcdef0123456789abcdef01234567 # vX
```

Regole obbligatorie:

- Mai usare ref floating (`@v4`, `@main`, `@master`, `@latest`) in file di workflow tracciati.
- Mantieni il commento di hint di versione (`# vX` o `# vX.Y.Z`) per review human-readable.
- Dependabot (`package-ecosystem: github-actions`) è l'autorità di automazione per il refresh delle SHA.
- Le PR che toccano workflow devono preservare il pinning SHA e menzionare l'impatto supply-chain nella descrizione della PR.

---

## Credential Scanner & The Canary

Questa sezione documenta le **quattro obbligazioni di sicurezza** che si
applicano a ogni PR che tocca `src/zenzic/core/`. Una PR che risolve un bug
senza soddisfare tutte e quattro sarà rifiutata dall'Architecture Lead.

Queste regole esistono perché la security review v0.5.0a3 (2026-04-04) ha
dimostrato che quattro scelte di design individualmente ragionevoli — ognuna
corretta in isolamento — si componevano in quattro vettori di attacco
distinti. Vedi `docs/internal/security/shattered_mirror_report.md` per il
post-mortem completo.

### Obbligazione 1 — La Security Tax (Worker Timeout)

Ogni PR che modifica l'uso di `ProcessPoolExecutor` in `scanner.py` deve
preservare la chiamata `future.result(timeout=_WORKER_TIMEOUT_S)`. Il timeout
corrente è **30 secondi**.

**Cosa significa:**

```python
# ✅ Required form — always use submit() + wait(FIRST_COMPLETED) + result(timeout=...)
futures_map = {executor.submit(_worker, item): item[0] for item in work_items}
raw: list[IntegrityReport] = []
_pending: set[concurrent.futures.Future[IntegrityReport]] = set(futures_map)
while _pending:
    done, _pending = concurrent.futures.wait(
        _pending,
        timeout=_WORKER_TIMEOUT_S,
        return_when=concurrent.futures.FIRST_COMPLETED,
    )
    if not done:
        # ZRT-002 deadlock guard: no worker completed within the timeout window
        for fut in _pending:
            raw.append(_make_timeout_report(futures_map[fut]))  # Z902 finding
            fut.cancel()
        break
    for fut in done:
        raw.append(fut.result())

# ❌ Forbidden — blocks indefinitely on ReDoS or deadlocked workers
raw = list(executor.map(_worker, work_items))
```

**Il finding Z902** (`WORKER_TIMEOUT`) non è un crash. È un finding
strutturato che emerge nell'UI standard del report. Un worker che va in
timeout non uccide la scansione — il coordinator continua con i worker
rimanenti.

**Se il tuo cambio richiede naturalmente un timeout più lungo** (es. una
nuova rule esegue computation costosa), incrementa `_WORKER_TIMEOUT_S` con un
commento che spiega il costo e un benchmark che dimostra l'input worst-case.

---

### Obbligazione 2 — Il Regex-Canary Protocol

Ogni entry `[[custom_rules]]` che specifica un `pattern` è soggetta al
**Regex-Canary**, uno stress test basato su POSIX `SIGALRM` che gira a
construction time di `AdaptiveRuleEngine`.

**Come funziona il canary:**

```python
# _assert_regex_canary() in rules.py — runs automatically for every CustomRule
_CANARY_STRINGS = (
    "a" * 30 + "b",   # classic (a+)+  trigger
    "A" * 25 + "!",   # uppercase variant
    "1" * 20 + "x",   # numeric variant
)
_CANARY_TIMEOUT_S = 0.1   # 100 ms
```

Il canary applica ciascuna delle tre stringhe al metodo `check()` della rule
sotto un watchdog di 100 ms. Se il pattern non completa entro 100 ms su
nessuna di queste stringhe, l'engine solleva `PluginContractError` prima che
la scansione inizi.

**Testare il tuo pattern contro il canary prima di committare:**

```python
from pathlib import Path
from zenzic.core.rules import CustomRule, _assert_regex_canary
from zenzic.core.exceptions import PluginContractError

rule = CustomRule(
    id="MY-001",
    pattern=r"your-pattern-here",
    message="Found.",
    severity="warning",
)

try:
    _assert_regex_canary(rule)
    print("✅ Canary passed — pattern is safe for production")
except PluginContractError as e:
    print(f"❌ Canary failed — ReDoS risk detected:\n{e}")
```

Oppure dalla shell:

```bash
uv run python -c "
from zenzic.core.rules import CustomRule, _assert_regex_canary
r = CustomRule(id='T', pattern=r'YOUR_PATTERN', message='.', severity='warning')
_assert_regex_canary(r)
print('safe')
"
```

**Pattern da evitare** (trigger di backtracking catastrofico):

| Pattern | Perché pericoloso |
|---------|-------------------|
| `(a+)+` | Quantificatori annidati — path esponenziali |
| `(a\|aa)+` | Alternation con overlap |
| `(a*)*` | Star annidata — infinite empty match |
| `.+foo.+bar` | Multi-wildcard greedy con suffisso |

**Pattern che sono sempre sicuri:**

| Pattern | Note |
|---------|------|
| `TODO` | Match letterale, O(n) |
| `^(DRAFT\|WIP):` | Alternation ancorata, O(1) a ogni posizione |
| `[A-Z]{3}-\d+` | Character class bounded |
| `\bfoo\b` | Ancorato a word-boundary |

**Nota di piattaforma:** `_assert_regex_canary()` usa `signal.SIGALRM`, che è
disponibile solo su sistemi POSIX (Linux, macOS). Su Windows, il canary è un
no-op. Il worker timeout (Obbligazione 1) è il backstop universale.

**Overhead del canary:** misurato a **0.12 ms** per construction di engine
con 10 rule sicure (mediana su 20 iterazioni). È un costo one-time allo
startup della scansione e ben dentro il budget accettabile della "Security
Tax".

---

### Obbligazione 3 — Il Dual-Stream Invariant del Credential Scanner

Lo stream del credential scanner e lo stream Content in
`ReferenceScanner.harvest()` non devono **mai** condividere un generator.
Questa è la lezione architetturale di ZRT-001.

```python
# ✅ CORRECT — independent generators, independent filtering contracts
with file_path.open(encoding="utf-8") as fh:
    for lineno, line in enumerate(fh, start=1):  # Credential scanner: ALL lines
        list(scan_line_for_secrets(line, file_path, lineno))

for lineno, line in _iter_content_lines(file_path):  # Content: filtered
    ...

# ❌ FORBIDDEN — sharing a generator silently drops frontmatter from credential scanner
with file_path.open(encoding="utf-8") as fh:
    shared = _skip_frontmatter(fh)
    for lineno, line in shared:
        list(scan_line_for_secrets(...))   # ← blind to frontmatter
    for lineno, line in shared:            # ← already exhausted
        ...
```

**Performance del credential scanner:** il dual-scan (raw + linea
normalizzata) gira a circa **235.000 linee/secondo** (misurato: mediana
12.74 ms per 3.000 linee su 20 iterazioni). Il normalizer aggiunge una pass
per linea ma il set `seen` previene finding duplicati, mantenendo l'output
deterministico.

Se una PR refattorizza `harvest()` e il benchmark CI scende sotto le
**100.000 linee/secondo**, rifiuta e investiga prima di mergiare.

### Obbligazione 4 — Mutation Score ≥ 90% per i Cambi Core

Ogni PR che modifica `src/zenzic/core/` deve mantenere o migliorare il
mutation score sul modulo coinvolto. Il baseline corrente per `rules.py` è
**86.7%** (242/279 mutanti uccisi).

Il target per rc1 è **≥ 90%**. Una PR che aggiunge una nuova rule o modifica
la logica di detection senza uccidere i mutanti corrispondenti sarà
rifiutata.

**Eseguire il mutation testing:**

```bash
nox -s mutation
```

**Interpretazione dei mutanti sopravvissuti:**

Non tutti i mutanti sopravvissuti sono equivalenti. Prima di marcare un
mutante come accettabile, conferma che:

1. Il mutante cambia comportamento osservabile (non è logicamente equivalente).
2. Nessun test esistente cattura il mutante (è una vera lacuna).
3. Aggiungere un test per ucciderlo sarebbe ridondante o trivialmente circolare.

Nel dubbio, aggiungi il test. La mutation suite è un documento vivo del
baseline di copertura del detection engine.

**ResolutionContext pickle validation (Eager Validation 2.0):**

`ResolutionContext` è un `@dataclass(slots=True)` con solo campi `Path`.
`Path` è pickleable dalla standard library. L'oggetto serializza a 157 byte.
Tuttavia, se `ResolutionContext` mai acquisisce un campo non pickleable (es.
un file handle, un lock, una lambda), il parallel engine fallirà
silenziosamente.

Per proteggersi da questo, ogni PR che aggiunge un campo a
`ResolutionContext` deve includere:

```python
# In tests/test_redteam_remediation.py (or a dedicated test):
def test_resolution_context_is_pickleable():
    import pickle
    ctx = ResolutionContext(docs_root=Path("/docs"), source_file=Path("/docs/a.md"))
    assert pickle.loads(pickle.dumps(ctx)) == ctx
```

Questo test esiste già nella suite di test a partire dalla v0.5.0a4.

**Credential Scanner Reporting Integrity (Il Mutation Gate per Commit 2+):**

il mutation score sul credential scanner è **più ampio** della sola
detection. Copre anche la **pipeline di reporting**:

> *Un secret che viene rilevato ma non riportato correttamente è un bug CRITICO —
> indistinguibile da un secret che non è mai stato rilevato.*

Ogni PR che tocca la funzione di conversione `_map_credentials_to_finding()`,
il path di severity `SECURITY_BREACH` in `ZenzicReporter`, o il routing degli
exit-code in `cli.py` **deve uccidere tutti e tre questi mutanti
obbligatori** prima che la PR venga accettata:

| Nome mutante | Cosa viene cambiato | Test che deve ucciderlo |
|--------------|---------------------|-------------------------|
| **The Invisible** | `severity="security_breach"` → `severity="warning"` in `_map_credentials_to_finding()` | `test_map_always_emits_security_breach_severity` |
| **The Amnesiac** | `_obfuscate_secret()` ritorna `raw` invece della forma redacted | `test_obfuscate_never_leaks_raw_secret` |
| **The Silencer** | `_map_credentials_to_finding()` ritorna `None` invece di un `Finding` | `test_pipeline_appends_breach_finding_to_list` |

**Eseguire il mutation gate:**

```bash
nox -s mutation
```

La session targetta `rules.py`, `credentials.py` e `reporter.py` come
configurato in `[tool.mutmut]` in `pyproject.toml`. Nessun posargs richiesto.

> **Nota infrastrutturale — `mutmut_pytest.ini`:**
> `mutmut` v3 genera trampoline in una working copy `mutants/`. Perché
> questi siano visibili a pytest, `mutants/src/` deve precedere le
> site-packages installate in `sys.path`. `mutmut_pytest.ini` (tracciato nel
> repo) fornisce una pytest config isolata (`import-mode=prepend`,
> `pythonpath = src`) usata esclusivamente dalla session `nox -s mutation`.
> La pytest config principale in `pyproject.toml` non è coinvolta.

**Fallback — Manual Mutation Verification (Il Mutation Gate, Manual Mode):**

Se il tool automatizzato non può riportare uno score (es. per un'issue di
editable-install mapping), applica ogni mutante a mano e conferma che il
test fallisce:

```bash
# 1. Apply mutant, run the specific test, confirm FAIL, revert.
git diff  # verify only one targeted line changed
pytest tests/test_redteam_remediation.py::TestCredentialScannerReportingIntegrity -v
git checkout -- src/  # revert
```

La verifica manuale è accettata come waiver temporaneo previa approvazione
dell'Architecture Lead. Documenta i risultati nella descrizione della PR
prima del merge.

Se lo score è sotto 90% (automated) o uno qualsiasi dei tre trial passa
quando dovrebbe fallire (manual), aggiungi test mirati prima di riaprire la
PR. Non marcare i mutanti sopravvissuti come equivalenti senza l'esplicita
approvazione dell'Architecture Lead.

---

## Aggiungere un nuovo check

I check di Zenzic vivono in `src/zenzic/core/`. Ogni check è una funzione
standalone o in `scanner.py` (filesystem traversal) o in `validator.py`
(content validation). Il wiring CLI è nel package `cli/` (`src/zenzic/cli/`).

Quando aggiungi un nuovo check:

1. Implementa la logica nel modulo core appropriato (`zenzic.core.scanner` o `zenzic.core.validator`).
2. **Ogni logica di risoluzione link o path DEVE delegare a `InMemoryPathResolver`** — non chiamare mai
   `os.path.exists()`, `Path.is_file()`, o qualsiasi altra probe filesystem dentro un loop per-link.
   Il resolver è istanziato una volta prima del loop; la ri-istanziazione per file vanifica
   il `_lookup_map` pre-computato e abbatte il throughput da 430.000+ a sotto le 30.000 resolution/s.
   Vedi [Core Laws — Zero I/O nell'hot path](#zero-io-nellhot-path) sopra.
3. Se il check coinvolge file path, testalo in tutte e tre le configurazioni i18n.
   Vedi [Core Laws — Determinismo i18n](#determinismo-i18n) sopra.
4. Aggiungi un comando corrispondente (o sub-command) nel package `cli/` — vedi [la sezione CLI Architecture](#cli-architecture) sotto.
5. Scrivi test in `tests/` che coprono casi sia passing che failing, incluso un performance
   baseline (5.000 link risolti in < 100 ms contro un corpus in-memory mock).
6. Aggiorna gli esempi in `examples/` per esercitare il nuovo check — Zenzic valida i suoi
   esempi a ogni commit.

> **Contratto di performance:** l'hot path di `zenzic.core` deve rimanere allocation-free. Nessuna
> costruzione di oggetti `Path`, nessuna syscall, e nessuna chiamata a `relative_to()` dentro il loop
> di risoluzione. Vedi `docs/architecture.md` — *IO Purity contract* e *Contributor rules* per il razionale.

---

## CLI Architecture {#cli-architecture}

La CLI è organizzata come un **package** (`src/zenzic/cli/`) invece che come
un singolo modulo. Ogni file possiede un dominio di responsabilità:

| Modulo | Responsabilità |
|:-------|:---------------|
| `_shared.py` | singleton `console`, singleton `_ui`, `configure_console()`, e tutte le utility cross-command (`_build_exclusion_manager`, `_output_json_findings`, `_render_link_error`, ecc.) |
| `_check.py` | sub-app Typer `check_app` + sette comandi `check *` e i loro helper privati |
| `_clean.py` | sub-app Typer `clean_app` + comando `clean assets` |
| `_config_explain.py` | comando `explain` + superficie di genealogia config / introspezione rule |
| `_governance.py` | sub-app Typer `config_app` + comandi di governance profile |
| `_guard.py` | sub-app Typer `guard_app` + comandi `scan` / `init` per il fast secret guard |
| `_inspect.py` | sub-app Typer `inspect_app` + comandi `capabilities`, `codes`, e `routes` |
| `_lab.py` | comando `lab` + scenario showcase interattivo |
| `_metadata.py` | Unica fonte di verità per i pannelli root help, raggruppamento comandi e short help text |
| `_standalone.py` | comandi `score`, `diff`, e `init` + i loro helper privati |
| `__init__.py` | Superficie di re-export pubblica consumata da `main.py` — **non aggiungere logica qui** |

`main.py` è la factory unificata di registrazione Typer. I nuovi comandi
top-level e sub-app devono essere registrati lì, e i metadata di root help
devono restare allineati con `_metadata.py`.

### Il Visual State Manager

`_shared.py` è il **unico owner di tutto lo stato console e UI**. Questa è
la regola architetturale più critica del layer CLI:

> **PROIBIZIONE:** nessun modulo di comando può istanziare direttamente `Console()` o una UI class custom. Tutto l'output deve passare per `get_ui()` e `get_console()` da `_shared.py`.

```python
# ✅ Correct — in any _check.py / _clean.py / _standalone.py command
from . import _shared
_shared.get_ui().print_header(__version__)
_shared.get_console().print("output")

# ❌ FORBIDDEN — never do this in a command module
from rich.console import Console
from mypackage.ui import LegacyInterfaceV1
console = Console(...)          # breaks shared state
ui = LegacyInterfaceV1(console) # creates an orphaned instance
```

Questa regola esiste perché `configure_console()` sostituisce i singleton a
livello di modulo `console` e `_ui` quando viene passato `--no-color` o
`--force-color`. Qualsiasi istanza `Console` o UI creata localmente sarà
congelata allo stato pre-flag e ignorerà la preferenza colore dell'utente.

Il parametro `force_terminal` del `Console` a livello di modulo è sempre
`None` (auto-detect tramite `sys.stdout.isatty()`), mai `False` (che
disabiliterebbe esplicitamente il colore). Impostare `force_terminal=False`
è un bug silenzioso che rimuove tutto lo styling ANSI anche nei terminali
interattivi.

### Aggiungere un comando a una sub-app esistente

```python
# src/zenzic/cli/_check.py (example: adding "check metadata")
@check_app.command(name="metadata")
def check_metadata(path: Path = ...) -> None:
    ...
```

Nessuna modifica a `__init__.py`, `main.py`, o `_metadata.py` è richiesta —
la sub-app Typer esistente possiede già questa superficie di comandi.

### Aggiungere una nuova sub-app top-level

1. Crea `src/zenzic/cli/_myfeature.py` con `myfeature_app = typer.Typer(...)` e i tuoi comandi.
2. Esporta `myfeature_app` da `src/zenzic/cli/__init__.py`.
3. Registra in `src/zenzic/main.py`: `app.add_typer(myfeature_app, name="myfeature", rich_help_panel="...")`.
4. Aggiungi un entry `CommandMeta(...)` in `src/zenzic/cli/_metadata.py` così i pannelli root help e short help restano autoritativi.
5. Se la sub-app usa `no_args_is_help=True`, aggiungi `"myfeature"` al frozenset `_SUBAPPS_WITH_MENU` in `cli_main()` così il banner Zenzic appare quando la sub-app è invocata senza argomenti.

---

## Documentazione

La documentazione user-facing di Zenzic vive in un repository separato:
**[zenzic-doc](https://github.com/PythonWoods/zenzic-doc)** (Docusaurus v3,
React, MDX).

Questo repository core contiene solo:

- `README.md` / `README.it.md` — overview di progetto e quick start.
- `CONTRIBUTING.md` / `CONTRIBUTING.it.md` — guida sviluppatore (questo file).
- `examples/` — fixture mantenute che Zenzic auto-valida.

Per contribuire miglioramenti alla documentazione, apri una PR nel
repository `zenzic-doc`.

## 🚀 Cross-Repo Validation (Branch Parity Rule)

Per garantire la coerenza tra il motore core (**zenzic**) e la documentazione (**zenzic-doc**), il nostro sistema CI applica la **Regola della Branch Parity**.

### 🔍 Come funziona

1. **Sviluppo Locale**: il linter cerca sempre il repository core nella cartella adiacente (`../zenzic`). Sei responsabile di mantenere allineati i branch locali.
2. **In CI (GitHub Actions)**: la pipeline della documentazione tenta di clonare il repository core cercando un branch con **lo stesso nome esatto** di quello in build nel repo doc.
3. **Fallback**: se il branch specchio non viene trovato nel repo core, la CI ripiega automaticamente sul branch `main`.

### 🛠️ Riepilogo Operativo per i Contributori

| Scenario | Azione Richiesta | Comportamento CI |
| :--- | :--- | :--- |
| **Fix Documentazione** | Push solo su `zenzic-doc` | Valida contro core `main`. |
| **Nuova Feature (Sincronizzata)** | Push su `zenzic` **PRIMA** di pushare su `zenzic-doc` | Valida contro il codice esatto della feature. |
| **Convenzione di Naming** | Usa nomi di branch identici in entrambi i repo | Garantisce un Dogfooding perfetto. |

> **Nota**: non pushare mai cambi di documentazione che dipendano da feature core non ancora presenti sul server remoto (anche se su branch diversi), altrimenti la build fallirà per disallineamento.

### 💻 Configurazione del Multi-Root Workspace VS Code

Poiché i repository sono strettamente accoppiati, raccomandiamo di gestirli tramite un singolo **Multi-Root Workspace** in VS Code.

1. Clona entrambi i repository nella stessa directory padre.
2. Apri VS Code e vai su **File > Save Workspace As...**, salvando come `zenzic.code-workspace` nella directory padre.
3. Modifica il file appena creato così:

```json
{
  "folders": [
    { "path": "zenzic" },
    { "path": "zenzic-doc" },
    { "path": "zenzic-action" }
  ],
  "settings": {
    "python.analysis.extraPaths": ["./zenzic/src"],
    "files.exclude": {
      "**/.venv": true,
      "**/_zenzic_core": true
    }
  }
}
```

Questo ti permette di eseguire ricerche globali su tutti i repository simultaneamente e gestire i branch dal pannello Source Control in un'unica interfaccia unificata.

---

## QA Avanzato: Mutanti & Proprietà

Zenzic usa due tecniche di test avanzate per assicurare che il core sia ben
hardenato.

### Property-Based Testing (Hypothesis)

`tests/test_properties.py` usa [Hypothesis](https://hypothesis.readthedocs.io/) per generare
migliaia di input casuali e verificare **invarianti** che devono valere per qualsiasi input:

- `extract_links()` non crasha mai, ritorna sempre `LinkInfo`, i numeri di linea restano in range.
- `slug_heading()` è lowercase, idempotente, e libero da trattini iniziali/finali.
- `CustomRule.check()` ritorna finding validi con `col_start` in range.
- `InMemoryPathResolver.resolve()` ritorna sempre un outcome type valido e cattura path traversal.

Esegui i property test:

```bash
uv run pytest tests/test_properties.py -x -q
```

### Mutation Testing (mutmut)

[mutmut](https://mutmut.readthedocs.io/) modifica il tuo codice sorgente (es. cambia `>` in `>=`)
e verifica se la test suite cattura la mutazione. Un mutante sopravvissuto significa una test gap.

Modulo target: `src/zenzic/core/rules.py` — il cuore della logica di detection.

Esegui mutation testing:

```bash
nox -s mutation
```

**Requisito di merge:** ogni nuova core rule deve raggiungere un **mutation score > 90%**. Se `mutmut`
riporta mutanti sopravvissuti in `rules.py`, aggiungi test mirati prima del merge.

---

---

## Maintainer Only: Workflow Hardening

### Immutable Pre-Commit Hooks (ADR-089)

Tutte le chiavi `rev:` in `.pre-commit-config.yaml` devono puntare a un
**commit hash di 40 caratteri**, mai a un tag semantico (`v1.2.3`). I tag git
sono mutabili: un maintainer upstream (o un attaccante che lo compromette)
può spostare un tag silenziosamente, avvelenando il Gate 2 locale senza
alcun diff in questo repository.

Questa è una **policy CI interna del progetto Zenzic**, non una regola
pubblica del linter Zenzic: vincola come *noi* sviluppiamo Zenzic, non come
gli utenti Zenzic sviluppano la loro documentazione. L'enforcement a livello
di orchestratore vive in `just check-pinning` (dipendenza di `just verify`);
le violazioni sollevano `[ADR-089] FATAL` in pre-push.

**Nota threat-model.** Il rischio locale è strettamente minore di quello
GHA perché `pre-commit` clona ogni repo di hook in `~/.cache/pre-commit/` e
lo congela finché l'utente non lancia `pre-commit autoupdate` o
`pre-commit clean`. GitHub Actions invece ri-risolve il ref a ogni
esecuzione di workflow. Il pinning è comunque obbligatorio in locale per (a)
sicurezza dei nuovi clone, (b) parità architetturale con l'enforcement
ADR-089 remoto, (c) auditabilità.

**Aggiornare gli hook pinned.** Il `pre-commit autoupdate` nudo riscrive le
SHA tornando a tag mutabili, vanificando l'hardening. Usa sempre:

```bash
uvx pre-commit autoupdate --freeze
```

`--freeze` risolve ogni tag alla sua commit SHA e preserva automaticamente
il commento di annotazione `# vX.Y.Z`. Committa il diff e verifica con
`just check-pinning`.

---

## Maintainer Only: Procedura di Release

Le release sono **semi-automatizzate**: lo sviluppatore decide il tipo di
bump, un comando fa il resto.

```bash
# 1. Ensure main is green (preflight passed)
nox -s preflight

# 2. Bump version, create commit and tag automatically
nox -s bump -- patch     # 0.1.0 → 0.1.1  (bug fix)
nox -s bump -- minor     # 0.1.0 → 0.2.0  (new feature, backward compatible)
nox -s bump -- major     # 0.1.0 → 1.0.0  (breaking change)

# 3. Push — this triggers the release workflow
git push && git push --tags
```

### Bump Verification

Baseline di release corrente: `v0.7.1`.

Prima di eseguire il bump finale, i maintainer devono eseguire un dry-run per
identificare stringhe di versione hardcoded che non sono coperte
dall'automazione:

```bash
just release-dry patch  # or minor/major
```

Rivedi l'output del diff. Se un file contenente una stringa di versione (ad
esempio un esempio del README o `SECURITY.md`) manca dal diff del dry-run,
deve essere aggiunto alla configurazione del bump prima di procedere.

Nota su `CHANGELOG.md`: il changelog è escluso dal bumping automatico. I
maintainer devono aggiornare manualmente l'header di versione e la data nel
log come atto finale di governance semantica.

Il workflow `release.yml` poi:

1. Esegue `uv build` (sdist + wheel)
2. Pubblica su PyPI tramite `uv publish` (richiede il secret `PYPI_TOKEN`)
3. Crea una GitHub Release con note auto-generate

Aggiorna `CHANGELOG.md` prima del bump: sposta gli item da `[Unreleased]`
alla nuova sezione di versione.
