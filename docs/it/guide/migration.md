---
icon: lucide/arrow-right-left
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Migrazione da MkDocs a Zensical

Zenzic funge da guardia di integrità continua durante la migrazione. Poiché analizza i **file
sorgente** e legge la configurazione come dati semplici — senza mai importare o eseguire il
framework di build — funziona correttamente con entrambi gli engine contemporaneamente e può
validare la documentazione prima, durante e dopo il passaggio.

---

## Cosa rimane invariato

Zensical è un successore compatibile di MkDocs. Legge `mkdocs.yml` nativamente, quindi molti progetti possono
cambiare il binario di build senza toccare un singolo file di documentazione. Dal punto di vista
di Zenzic:

- La struttura della directory `docs/` rimane invariata.
- `mkdocs.yml` rimane il file principale di configurazione di navigazione e plugin.
- Le convenzioni i18n in folder-mode e suffix-mode sono identiche.
- `[build_context]` in `zenzic.toml` può rimanere `engine = "mkdocs"` fino a quando non sei
  pronto a creare `zensical.toml`.

---

## Fase 1 — Valida prima di cambiare

Esegui la suite completa di controlli sul tuo progetto MkDocs e stabilisci un baseline:

```bash
# Assicurati che i docs siano puliti prima di toccare qualcosa
zenzic check all
zenzic score --save   # persisti il baseline in .zenzic-score.json
```

Un baseline pulito rende immediatamente visibile qualsiasi regressione introdotta durante la
migrazione con `zenzic diff`.

---

## Fase 2 — Cambia il binario di build

Installa Zensical insieme a (o al posto di) MkDocs:

```bash
uv add --dev zensical      # raccomandato
# oppure: pip install zensical
```

Esegui la build della documentazione per verificare che produca output identico:

```bash
zensical build
```

I controlli di Zenzic sono engine-neutral — eseguili dopo la build per confermare che nulla si
sia rotto:

```bash
zenzic check all
zenzic diff              # dovrebbe riportare zero delta rispetto al baseline pre-migrazione
```

---

## Fase 3 — Dichiara l'identità Zensical (opzionale)

Se vuoi che Zenzic imponga il contratto di identità Zensical — richiedendo la presenza di
`zensical.toml` e usando `ZensicalAdapter` per l'estrazione della nav — aggiorna `zenzic.toml`:

```toml
# zenzic.toml
[build_context]
engine = "zensical"
default_locale = "en"
locales        = ["it"]
```

E crea un `zensical.toml` minimale nella root del repository:

```toml
# zensical.toml
[site]
name = "La Mia Documentazione"

[nav]
nav = [
    {title = "Home",  file = "index.md"},
    {title = "Guida", file = "guide.md"},
]
```

!!! warning "Contratto di enforcement"

    Una volta dichiarato `engine = "zensical"` in `zenzic.toml`, `zensical.toml` **deve**
    esistere. Zenzic solleva un `ConfigurationError` immediatamente se è assente — non c'è
    fallback silenzioso a `mkdocs.yml`. Questo è intenzionale: l'identità dell'engine deve
    essere provabile.

---

## Fase 4 — Verifica l'integrità dei link

Il controllo dei link è il passo di validazione più importante. Eseguilo sulla migrazione
completata:

```bash
# Link interni + risoluzione fallback i18n
zenzic check links

# Link reference-style + Shield (rilevamento credenziali)
zenzic check references

# Suite completa
zenzic check all
zenzic diff --threshold 0   # fallisce su qualsiasi regressione, nessun margine
```

Se il punteggio corrisponde al baseline pre-migrazione, la migrazione è completa.

---

## Mantenere le regole custom durante la migrazione

Le `[[custom_rules]]` in `zenzic.toml` sono **indipendenti dall'adapter** — si attivano
identicamente indipendentemente dall'engine. Qualsiasi regola in vigore per il tuo progetto MkDocs
continua a funzionare senza modifiche dopo il passaggio a Zensical:

```toml
# Queste regole funzionano con entrambi gli engine
[[custom_rules]]
id       = "ZZ-NODRAFT"
pattern  = "(?i)\\bDRAFT\\b"
message  = "Rimuovere il marker DRAFT prima della pubblicazione."
severity = "warning"

[build_context]
engine = "zensical"
```

---

## Riferimento rapido

| Passo | Comando | Risultato atteso |
| :--- | :--- | :--- |
| Baseline | `zenzic score --save` | Score salvato in `.zenzic-score.json` |
| Dopo il cambio di build | `zenzic check all` | Stessi problemi di prima |
| Controllo regressioni | `zenzic diff` | Delta = 0 |
| Enforcement identità | `engine = "zensical"` in `zenzic.toml` | Richiede `zensical.toml` |
| Gate finale | `zenzic diff --threshold 0` | Exit 0 solo se il punteggio non è diminuito |
