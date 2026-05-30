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

## Sicurezza & Compliance

- **Security First:** ogni nuova path resolution DEVE essere testata contro Path Traversal. Usa la logica `PathTraversal` da `core`.
- **Test di Obfuscation del Credential Scanner:** ogni nuovo pattern di credential o regola di normalizer DEVE includere test di regressione per obfuscation: caratteri Unicode format (categoria Cf), encoding HTML entity, interleaving di commenti (HTML `<!-- -->` e MDX `{/* */}`), e token spezzati cross-line. Vedi `tests/test_credentials_obfuscation.py` come reference.
- **Bilingual Parity:** la documentazione vive in [zenzic-doc](https://github.com/PythonWoods/zenzic-doc). Indirizza i contributori della documentazione lì.
- **Machine-Local Config:** i secret specifici del progetto (forbidden terms per Z204) vanno in `.zenzic.local.toml` — mai committati. Esegui `zenzic init --local` per generare una configurazione locale aggiornata alla tua versione del motore.

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

Per guide avanzate su come scrivere nuovi check, estendere adapter, l'architettura CLI, le obbligazioni del Credential Scanner e il mutation testing, consulta il [Developer Portal](https://zenzic.dev/developers/).

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

Baseline di release corrente: `v0.8.0`.

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
