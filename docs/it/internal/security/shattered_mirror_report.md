<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Analisi di Sicurezza: Vulnerabilità in v0.5.0a3

---

> *"Ciò che non è documentato, non esiste; ciò che è documentato male, è
> un'imboscata."*
>
> Questo documento registra le cause radice e il ragionamento architetturale
> dietro ogni vulnerabilità — per prevenire regressioni e informare i futuri contributori.

---

## 1. Sommario Esecutivo

Durante la fase alpha di v0.5.0a3, un'analisi di sicurezza interna ha identificato **quattro
vulnerabilità confermate** che attraversano
i tre pilastri del modello di sicurezza di Zenzic: lo Shield (rilevamento
segreti), la Virtual Site Map (validazione routing) e il motore di Parallelismo
Adattivo.

Tutte e quattro sono state risolte in v0.5.0a4. Questo documento registra le
cause radice, le meccaniche di attacco e il ragionamento architetturale dietro
ogni fix — sia per prevenire regressioni che per spiegare ai futuri
contributori *perché* il codice ha questa forma.

---

## 2. Il Modello di Minaccia della Sentinella

Prima di esaminare ogni finding, è utile capire cosa promette la Sentinella
e cosa non promette.

| Promessa | Meccanismo |
|----------|-----------|
| Nessun commit di segreti | Lo Shield scansiona ogni byte prima dell'elaborazione |
| Nessun link rotto | La VSM valida i link rispetto allo stato di routing, non al filesystem |
| Nessun CI in deadlock | Timeout worker + canary rigettano i pattern catastrofici |
| Nessuna navigazione falsa | La VSM risolve i link dal contesto del file sorgente |

L'analisi ha rilevato che tre di queste quattro promesse avevano lacune
strutturali — non bug logici, ma **punti ciechi architetturali** dove il
componente era progettato correttamente per il suo *input dichiarato* ma non
aveva mai considerato una classe di input tecnicamente validi.

---

## 3. Finding

### ZRT-001 — CRITICO: Shield Cieco al Frontmatter YAML

#### Cosa è Successo

`ReferenceScanner.harvest()` esegue due passate su ogni file:

1. **Passata 1 (Shield):** scansione delle righe per pattern di segreti.
2. **Passata 1b (Contenuto):** raccolta di definizioni di riferimento e alt-text.

Entrambe le passate dovevano saltare il frontmatter YAML (blocchi `---`) — ma
per ragioni *diverse e opposte*:

- La **passata Contenuto** deve saltare il frontmatter perché `author: Jane Doe`
  verrebbe altrimenti analizzato come una definizione di riferimento rotta.
- La **passata Shield** deve **non** saltare il frontmatter perché `aws_key: AKIA…`
  è un vero segreto che deve essere catturato.

L'implementazione originale condivideva un unico generatore, `_skip_frontmatter()`,
per entrambe le passate. Questo era corretto per lo stream Contenuto e
catastroficamente sbagliato per lo stream Shield.

#### Percorso di Attacco

```markdown
---
description: Guida API
aws_key: AKIA[chiave-20-char-redatta]      ← invisibile allo Shield
stripe_key: sk_live_[chiave-24-char-redatta]  ← invisibile allo Shield
---

# Guida API

Contenuto normale qui.
```

```bash
zenzic check all   # Exit 0 — PASS  ← Zero finding segnalati (pre-fix)
git commit -am "aggiunta credenziali api"  # Chiave committata, CI verde — violazione
```

#### Diagramma della Causa Radice

```text
                ┌─────────────────────────────────┐
                │  harvest()                       │
                │                                  │
File su disco ──►│  _skip_frontmatter(fh)           │──► Stream Shield
                │      ↑                           │
                │      salta righe 1–N             │   (PUNTO CIECO)
                │      del blocco ---              │
                │                                  │
                │  _iter_content_lines(file)       │──► Stream Contenuto
                └─────────────────────────────────┘
```

#### Il Fix: Architettura Dual-Stream

I due stream usano ora **generatori diversi** con **contratti di filtraggio
diversi**:

```text
                ┌─────────────────────────────────┐
                │  harvest()                       │
                │                                  │
File su disco ──►│  enumerate(fh, start=1)          │──► Stream Shield
                │      ↑                           │      (TUTTE le righe)
                │      nessun filtraggio           │
                │                                  │
                │  _iter_content_lines(file)       │──► Stream Contenuto
                │      ↑                           │   (frontmatter +
                │    salta frontmatter             │    fence saltati)
                │    salta blocchi fence           │
                └─────────────────────────────────┘
```

Lo Shield vede ora ogni byte del file. Lo stream Contenuto continua a saltare
il frontmatter per evitare finding di riferimento falsi positivi.

**Perché questo è strutturalmente solido:** Lo Shield e il raccoglitore di
Contenuto hanno requisiti di filtraggio ortogonali. Non devono mai condividere
un generatore.

---

### ZRT-002 — ALTO: ReDoS + Deadlock di ProcessPoolExecutor

#### Cosa è Successo

L'`AdaptiveRuleEngine` valida le regole per la serializzabilità pickle alla
costruzione (`_assert_pickleable()`). Questo è corretto — garantisce che ogni
regola possa essere spedita a un processo worker. Tuttavia, `pickle.dumps()` è
cieco alla complessità computazionale. Un pattern come `^(a+)+$` serializza
correttamente e viene spedito con successo, poi si blocca indefinitamente
all'interno del worker quando applicato a una stringa come `"a" * 30 + "b"`.

`ProcessPoolExecutor` nella forma originale usava `executor.map()`, che non ha
timeout. Il risultato: una singola voce `[[custom_rules]]` malevola in
`zenzic.toml` poteva bloccare permanentemente ogni pipeline CI su un repository
con ≥ 50 file.

#### La Complessità del Backtracking Catastrofico

Il pattern `^(a+)+$` contiene un **quantificatore annidato** — `+` dentro `+`.
Quando applicato a `"aaa…aab"` (il trigger ReDoS), il motore regex deve
esplorare un numero esponenziale di percorsi nella stringa prima di determinare
che non corrisponde. A n=30 caratteri, questo richiede minuti. A n=50, ore.

L'intuizione chiave è che `re.compile()` **non** valida per ReDoS. La
compilazione è O(1). Il costo catastrofico si manifesta solo al momento di
`match()`/`search()` su input artigianali.

#### Percorso di Attacco

```toml
# zenzic.toml
[[custom_rules]]
id = "STILE-001"
pattern = "^(a+)+$"      # ← backtracking catastrofico
message = "Controllo stile"
severity = "error"
```

```markdown
<!-- docs/payload.md -->
aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaab    ← stringa trigger ReDoS
```

```bash
zenzic check all --workers 4   # Tutti i 4 worker si bloccano. La CI non finisce mai.
```

#### Due Difese Complementari

**Prevenzione — `_assert_regex_canary()` (tempo di costruzione):**

```text
AdaptiveRuleEngine.__init__():
    for rule in rules:
        _assert_pickleable(rule)   ← controllo esistente
        _assert_regex_canary(rule) ← NUOVO: stress test SIGALRM 100ms
```

Il canary esegue ogni pattern `CustomRule` contro tre stringhe di stress sotto
un watchdog `signal.SIGALRM` di 100 ms. Se il pattern impiega più di 100 ms su
un input di 30 caratteri, è categoricamente catastrofico e solleva
`PluginContractError` *prima che venga scansionato il primo file*.

**Contenimento — `future.result(timeout=30)` (runtime):**

```text
# Prima
raw = list(executor.map(_worker, work_items))   # si blocca per sempre

# Dopo
futures_map = {executor.submit(_worker, item): item[0] for item in work_items}
for fut, md_file in futures_map.items():
    try:
        raw.append(fut.result(timeout=30))
    except concurrent.futures.TimeoutError:
        raw.append(_make_timeout_report(md_file))  # finding Z009, mai crash
```

Un worker che supera 30 secondi produce un finding `Z009: ANALYSIS_TIMEOUT`
invece di bloccare il coordinatore.

**Perché entrambe le difese sono necessarie:** Il canary dipende dalla
piattaforma (`SIGALRM` è solo POSIX; è un no-op su Windows). Il timeout è il
backstop universale.

---

### ZRT-003 — MEDIO: Bypass Shield con Token Divisi tramite Tabella Markdown

#### Cosa è Successo

`scan_line_for_secrets()` dello Shield applicava i pattern regex a ogni riga
grezza. Il pattern per chiavi AWS `AKIA[0-9A-Z]{16}` richiede 20 caratteri
**contigui**. Un autore (malevolo o negligente) che documenta credenziali in
una colonna di tabella usando notazione inline code e operatori di
concatenazione rompe la contiguità:

```markdown
| ID Chiave | `AKIA` + `[suffisso-16-char]` |
```

La riga grezza passata alla regex è (resa in sorgente come token divisi):

```text
| ID Chiave | `AKIA` + `[suffisso-16-char]` |
```

La sequenza alfanumerica contigua più lunga è `ABCDEF` (6 chars). Il pattern
non corrisponde mai. Lo Shield segnala zero finding.

#### Il Fix: Normalizzatore Pre-Scan

`_normalize_line_for_shield()` applica tre trasformazioni prima che vengano
eseguiti i pattern regex:

1. **Rimuovi span backtick:** `` `AKIA` `` → `AKIA`
2. **Rimuovi operatori di concatenazione:** `` ` ` + ` ` `` → niente
3. **Collassa pipe di tabella:** `|` → ``

La forma normalizzata della riga di attacco è `ID Chiave AKIA[suffisso-16-char]`,
che corrisponde a `AKIA[0-9A-Z]{16}` correttamente.

**Sia** la forma grezza che quella normalizzata vengono scansionate. Un set
`seen` previene finding duplicati quando un segreto appare non offuscato *e*
la forma normalizzata corrisponde anch'essa.

---

### ZRT-004 — MEDIO: Risoluzione URL Context-Free di VSMBrokenLinkRule

#### Cosa è Successo

`VSMBrokenLinkRule._to_canonical_url()` era un `@staticmethod`. Convertiva
gli href in URL VSM canonici usando un algoritmo root-relativo: rimuovi `.md`,
elimina `index`, prependi `/`, aggiungi `/`. Questo è corretto per i file nella
docs root ma produce il risultato sbagliato per i file in sottodirectory quando
l'href contiene segmenti `..`.

#### Esempio del Bug

```text
File sorgente: docs/a/b/pagina.md
Link:          [Vedi](../../c/target.md)

URL atteso:    /c/target/    ← dove il browser navigherebbe
URL calcolato: /c/target/    ← accidentalmente corretto in questo caso a 2 livelli

File sorgente: docs/a/b/pagina.md
Link:          [Vedi](../fratello.md)

URL atteso:    /a/fratello/  ← il file è docs/a/fratello.md
URL calcolato: /fratello/    ← SBAGLIATO: risolto dalla root, non dalla dir sorgente
```

L'`InMemoryPathResolver` (usato da `validate_links_async`) risolveva i link
correttamente perché aveva il contesto `source_file` dall'inizio. La
`VSMBrokenLinkRule` no, creando una discrepanza silenziosa tra due superfici di
validazione.

#### Il Fix: ResolutionContext

```python
@dataclass(slots=True)
class ResolutionContext:
    docs_root: Path
    source_file: Path
```

`BaseRule.check_vsm()` e `AdaptiveRuleEngine.run_vsm()` accettano ora
`context: ResolutionContext | None = None`. Quando il contesto è fornito,
`_to_canonical_url()` risolve i segmenti `..` usando `os.path.normpath`
relativo a `context.source_file.parent`, poi mappa il percorso assoluto
risolto di ritorno a un URL docs-relativo.

Il metodo applica anche il confine Shield: se il percorso risolto esce da
`docs_root`, restituisce `None` (equivalente a un outcome `PathTraversal`
in `InMemoryPathResolver`).

**La Lezione Architetturale:** Qualsiasi metodo che converte un href relativo in
URL assoluto *deve* sapere da dove proviene quell'href. Uno `@staticmethod` che
riceve solo la stringa href è strutturalmente incapace di gestire correttamente
i percorsi relativi. In Zenzic, questo si chiama ora **Anti-Pattern
Context-Free** (vedi `../../arch/vsm_engine.md` per il protocollo completo).

---

## 4. L'Architettura di Multiplexing degli Stream

Post-remediation, `ReferenceScanner.harvest()` implementa un modello pulito a
due stream. Questa sezione lo documenta per i futuri contributori.

```text
┌─────────────────────────────────────────────────────────────────┐
│  ReferenceScanner.harvest()                                     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  STREAM SHIELD                                          │   │
│  │  Sorgente: enumerate(file_handle, start=1)              │   │
│  │  Filtro: NESSUNO — ogni riga incluso frontmatter        │   │
│  │  Trasformazioni:                                        │   │
│  │    1. _normalize_line_for_shield(riga)  [ZRT-003]       │   │
│  │    2. scan_line_for_secrets(grezza)                     │   │
│  │    3. scan_line_for_secrets(normalizzata)               │   │
│  │  Output: eventi ("SECRET", SecurityFinding)             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  STREAM CONTENUTO                                       │   │
│  │  Sorgente: _iter_content_lines(file_path)               │   │
│  │  Filtro: salta frontmatter YAML, salta blocchi fence    │   │
│  │  Trasformazioni:                                        │   │
│  │    1. Analisi definizioni riferimento (_RE_REF_DEF)     │   │
│  │    2. Scansione URL ref-def per segreti                 │   │
│  │    3. Analisi immagini inline (_RE_IMAGE_INLINE)        │   │
│  │  Output: eventi ("DEF", "IMG", "MISSING_ALT", …)       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Output finale: eventi uniti e ordinati per numero di riga     │
└─────────────────────────────────────────────────────────────────┘
```

**Invariante:** Lo stream Shield e lo stream Contenuto non devono *mai condividere
un generatore*. Qualsiasi refactoring futuro che li unisca reintroduce ZRT-001.

---

## 5. Cosa Ha Reso Possibili Queste Vulnerabilità

Tutti e quattro i finding condividono una radice comune: **contratti impliciti
ai confini dei sottosistemi**.

| Finding | Contratto implicito violato |
|---------|---------------------------|
| ZRT-001 | "Lo Shield vede tutte le righe" — violato dal generatore condiviso |
| ZRT-002 | "Pickle-safe significa execution-safe" — violato dalla cecità al ReDoS |
| ZRT-003 | "Una riga = un token" — violato dalla frammentazione della sintassi Markdown |
| ZRT-004 | "La risoluzione URL è context-free" — violato dai percorsi relativi |

Il fix in ogni caso segue lo stesso schema: **rendere il contratto esplicito nel
sistema dei tipi o nella firma della funzione**, e **testarlo direttamente**.

---

## 6. Prevenzione delle Regressioni

I seguenti test in `tests/test_redteam_remediation.py` servono come guardie di
regressione permanenti. Non devono mai essere eliminati o indeboliti:

| Classe di test | Cosa protegge |
|---------------|--------------|
| `TestShieldFrontmatterCoverage` | ZRT-001 — scansione frontmatter |
| `TestReDoSCanary` | ZRT-002 — rigetto canary alla costruzione |
| `TestShieldNormalizer` | ZRT-003 — ricostruzione token divisi |
| `TestVSMContextAwareResolution` | ZRT-004 — risoluzione URL context-aware |
| `TestShieldReportingIntegrity` | Z-SEC-002 — severità breach, mascheratura segreti, fedeltà bridge |

Se un futuro refactoring causa il fallimento di uno qualsiasi di questi test,
la PR **non deve essere mergiata** finché il test non viene dimostrato errato
(e la guardia di regressione sostituita con un equivalente) o il fix non viene
ripristinato.

---

## 7. Lezioni Apprese

Per v0.5.0rc1 e oltre:

1. **Ogni nuovo confine di sottosistema deve documentare il proprio contratto
   di filtraggio.** Un generatore che salta righe deve avere una nota che
   spiega *cosa* salta e *perché* il chiamante è autorizzato a usarlo.

2. **I metodi `@staticmethod` che gestiscono percorsi sono sospetti per
   definizione.** Se un metodo statico riceve una stringa di percorso, chiedi:
   ha bisogno di sapere da dove proviene quel percorso? Se sì, non è un metodo
   statico — è un argomento di contesto mancante.

3. **I pattern regex forniti dall'utente sono input non fidati.** Esegui sempre
   il canary. Il budget di 100 ms non è un requisito di performance — è un
   confine di sicurezza.

4. **Il livello di parallelismo deve avere sempre un timeout.** Un coordinatore
   che attende indefinitamente i worker è un single point of failure per
   l'intera pipeline CI.

---

*Documento aggiornato a v0.5.0a4.*
