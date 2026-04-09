<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# ADR 003: Protocollo di Scoperta della Radice (PSR) {#adr-003-root-discovery-protocol}

**Stato:** Attivo (modificato da ZRT-005, 2026-04-08)
**Decisori:** Architecture Lead
**Data:** 2026-03-01
**Modifica:** 2026-04-08

---

## Contesto

Zenzic non opera su file isolati. Ogni controllo che esegue — validazione dei
link, rilevamento degli orfani, risoluzione degli asset — è relativo a un'entità
logica chiamata **Workspace**. Il Workspace ha un confine autorizzato unico: la
**radice del progetto**.

Senza una radice nota, Zenzic non può:

- Risolvere link interni in stile assoluto (`/docs/pagina.md`) in file fisici.
- Localizzare `zenzic.toml` o la configurazione di fallback del motore
  (`mkdocs.yml`, `zensical.toml`).
- Applicare il perimetro della Virtual Site Map (VSM) — l'oracolo che determina
  cos'è una pagina valida e cosa è una Ghost Route.
- Evitare di indicizzare accidentalmente file appartenenti a un progetto padre,
  a un repository adiacente o alla radice di sistema.

Il meccanismo di scoperta della radice deve quindi essere **deterministico**,
**sicuro per impostazione predefinita** e **agnostico rispetto al motore**
(indipendente da MkDocs, Zensical o qualsiasi altro toolchain di build).

---

## Decisione

`find_repo_root()` in `src/zenzic/core/scanner.py` risale dalla directory di
lavoro corrente controllando ogni antenato per uno dei due **marcatori di
radice** (vince il primo trovato):

| Marcatore | Motivazione |
|-----------|-------------|
| `.git/` | Segnale VCS universale. La presenza di `.git` indica che l'utente ha definito esplicitamente un confine di repository. Zenzic rispetta questo confine come perimetro del progetto. |
| `zenzic.toml` | Il file di configurazione nativo di Zenzic. La sua presenza è una dichiarazione inequivocabile che quella directory è la radice dell'analisi, anche in ambienti senza VCS. |

`mkdocs.yml`, `pyproject.toml` e altri file specifici del motore sono
deliberatamente **esclusi** dai marcatori di radice. Includerli accoplerebbe
il meccanismo di scoperta a un motore specifico, violando il Pilastro 1
(*Analizza la Sorgente, non la Build*).

Se nessun marcatore viene trovato in nessun antenato, `find_repo_root()` solleva
un `RuntimeError` con un messaggio operativo — non fa mai silenziosamente
defaulting alla radice del filesystem.

---

## Motivazione

### 1. Sicurezza: Prevenire l'Indicizzazione Massiva Accidentale

Un'implementazione ingenua che defaulta alla directory corrente quando non
viene trovato alcun marcatore permetterebbe a un utente che invoca
`zenzic check all` da `/home/utente/` di indicizzare inavvertitamente l'intera
home directory. La modalità di fallimento rigorosa è un **default sicuro**:
Zenzic rifiuta di agire finché l'utente non stabilisce un perimetro.

### 2. Coerenza: Supporto Futuro di `.gitignore`

Usare `.git` come ancora della radice allinea il confine del Workspace di Zenzic
con il confine VCS. Questo è un prerequisito per qualsiasi funzionalità futura
che necessiti di interpretare `.gitignore` (es. esclusione automatica di `site/`,
`dist/` o artefatti di build generati).

### 3. Esperienza Utente: Fallimento Immediato e Chiaro

Una radice ambigua produce risultati scorretti in silenzio. Un fallimento
esplicito all'avvio — prima che qualsiasi file venga toccato — è preferibile a
una scansione che segnali violazioni fantasma o salti file perché la radice è
stata risolta nell'antenato sbagliato. Il messaggio di errore include la CWD e
un suggerimento di rimedio esplicito.

### 4. Agnosticismo rispetto al Motore

`.git` e `zenzic.toml` sono entrambi marcatori agnostici. La stessa logica di
scoperta della radice funziona identicamente indipendentemente dal fatto che il
progetto sia costruito con MkDocs, Zensical, Hugo o plain Pandoc. Questo
preserva l'invariante fondamentale per cui il comportamento di Zenzic è
indipendente dal toolchain di build.

---

## Conseguenze

- **Positivo:** Ogni percorso di codice che chiama `find_repo_root()` riceve
  garantitamente una directory valida e delimitata, o solleva un'eccezione prima
  che avvenga qualsiasi I/O.
- **Positivo:** La logica delle Ghost Route e la costruzione della VSM hanno
  un'ancora stabile.
- **Negativo (pre-modifica):** Il comando `zenzic init`, il cui scopo è
  *creare* il marcatore di radice `zenzic.toml`, non poteva essere eseguito in
  una directory priva sia di `.git` sia di `zenzic.toml`. Questo era il
  **Paradosso di Bootstrap** (ZRT-005).

---

## Modifica — ZRT-005: Il Fallback Genesis (2026-04-08)

**Problema:** `zenzic init` è il comando di bootstrap per nuovi progetti. Il
suo scopo esatto è creare il marcatore di radice `zenzic.toml`. Richiedere che
un marcatore di radice *esista già* prima che `init` possa girare è un
Catch-22.

**Risoluzione:** `find_repo_root()` acquisisce un parametro keyword-only:

```python
def find_repo_root(*, fallback_to_cwd: bool = False) -> Path:
    ...  # risale da CWD; solleva o restituisce cwd in base al flag
```

Quando `fallback_to_cwd=True` e nessun marcatore di radice viene trovato, la
funzione restituisce `Path.cwd()` invece di sollevare un'eccezione. Questo è
chiamato **Fallback Genesis**.

**Ambito di autorizzazione:** Il Fallback Genesis è un'esenzione a punto
singolo. Solo il comando `init` passa `fallback_to_cwd=True`. Ogni altro
comando (`check`, `scan`, `score`, `serve`, `clean`) mantiene il default
rigoroso (`fallback_to_cwd=False`) e continuerà a fallire esplicitamente
fuori da un perimetro di progetto.

```python
# src/zenzic/cli.py — l'unico call site autorizzato per fallback_to_cwd=True
@app.command()
def init(plugin=None, force=False):
    repo_root = find_repo_root(fallback_to_cwd=True)  # Fallback Genesis
    ...

# Tutti gli altri comandi — applicazione rigorosa del perimetro
@app.command()
def check(target=None, strict=False):
    repo_root = find_repo_root()  # solleva fuori da un repo — corretto
    ...
```

**Nota di sicurezza:** Il Fallback Genesis **non** indebolisce il perimetro
per i comandi di analisi. `zenzic check all` eseguito da `/home/utente/` senza
alcun antenato `.git` solleverà comunque `RuntimeError`. Il fallback è
ristretto all'unico comando esplicitamente progettato per stabilire un
perimetro da zero.

---

## Riferimenti

- `src/zenzic/core/scanner.py` — implementazione di `find_repo_root()`
- `src/zenzic/cli.py` — comando `init`, unico consumatore di `fallback_to_cwd=True`
- `tests/test_scanner.py` — `test_find_repo_root_genesis_fallback`,
  `test_find_repo_root_genesis_fallback_still_raises_without_flag`
- `tests/test_cli.py` — `test_init_in_fresh_directory_no_git`
- `CONTRIBUTING.md` — Leggi del Core → Protocollo di Scoperta della Radice
- [`ADR 003 (English)`](../../adr/003-discovery-logic.md)
