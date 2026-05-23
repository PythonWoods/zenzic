<!--
SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
SPDX-License-Identifier: Apache-2.0
-->

<p align="center">
  <img src="assets/brand/svg/zenzic-wordmark.svg#gh-light-mode-only" alt="Zenzic" width="360">
  <img src="assets/brand/svg/zenzic-wordmark-dark.svg#gh-dark-mode-only" alt="Zenzic" width="360">
</p>

<p align="center">
  <a href="https://pypi.org/project/zenzic/">
    <img src="https://img.shields.io/pypi/v/zenzic?label=PyPI&color=38bdf8&style=flat-square&cacheBuster=current release" alt="PyPI Version">
  </a>
  <a href="https://pypi.org/project/zenzic/">
    <img src="https://img.shields.io/pypi/pyversions/zenzic?color=10b981&style=flat-square" alt="Python Versions">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-Apache--2.0-0d9488?style=flat-square" alt="License">
  </a>
</p>

<p align="center">
  <a href="https://zenzic.dev/it/docs/how-to/add-badges/">
    <img src="https://img.shields.io/badge/zenzic-audit:_passed-success?style=flat-square" alt="Zenzic Audit">
  </a>
  <a href="https://docusaurus.io/">
    <img src="https://img.shields.io/badge/docs_by-Docusaurus-3ECC5F?style=flat-square" alt="Built with Docusaurus">
  </a>
  <a href="https://zenzic.dev/it/developers/explanation/adr-vault">
    <img src="https://img.shields.io/badge/4--Gates-verified-10b981?style=flat-square" alt="4-Gates verified">
  </a>
  <a href="https://reuse.software/">
    <img src="https://img.shields.io/badge/REUSE-3.x%20compliant-0d9488?style=flat-square" alt="REUSE 3.x compliant">
  </a>
</p>

<p align="center">
  <em>Zenzic verifica internamente questo repository per credenziali esposte ad ogni commit.</em>
</p>

<p align="center">
  <strong>Audit deterministico di strutture documentali con tracciabilità bidirezionale.</strong><br>
  <em>Governance a tier, contratti frozen e scansione deterministica con backend RE2.</em>
</p>

---

## ⚡ Provalo subito — Zero Installazione

Hai una cartella di file Markdown? Esegui un audit istantaneo dei link e della sicurezza usando [`uv`][uv]:

```bash
uvx zenzic check all ./tua-cartella
```

Zenzic identificherà il tuo motore tramite i file di configurazione o passerà alla **Standalone Mode**
per cartelle Markdown pure — garantendo protezione immediata per link, credenziali e integrità dei file.

---

## 🚀 Quick Start

```bash
pip install zenzic
cd il-mio-repo-docs
zenzic init       # Stabilisce il perimetro del workspace (crea zenzic.toml)
zenzic check all  # Analizza la cartella corrente
```

## 🧠 Proposta di Valore

- **Motore puro e deterministico:** input identici producono finding ed exit identici.
- **Modello codici a tier:** finding Core, Structure e Governance separati per ownership, con cambi di policy espliciti e auditabili.
- **Contratti frozen per integrazioni:** `FROZEN_CODES`, `NON_SUPPRESSIBLE_CODES` e `PLUGIN_FORBIDDEN_EXITS` sono superfici stabili per CI e plugin.
- **Workflow contributori inspect-first:** usare `zenzic inspect codes` prima di aggiornare esempi documentali o note di rilascio.

📖 [Documentazione completa →][docs-it-home] · 🏅 [Badge][docs-it-badges] · 🔄 [Guida CI/CD][docs-it-cicd]

---

> 🚀 **CI/CD Ready:** Usa la [Official Zenzic Action](https://github.com/PythonWoods/zenzic-action) per eseguire Zenzic in GitHub Actions — i finding appaiono in Code Scanning, nelle annotazioni PR e nella tab Security.
>
> ```yaml
> - uses: PythonWoods/zenzic-action@v1
>   with:
>     format: sarif
>     upload-sarif: "true"
> ```

<p align="center">
  <img alt="GitHub Code Scanning con finding Zenzic" src="https://raw.githubusercontent.com/PythonWoods/zenzic-action/main/assets/sarif-showcase.svg" width="760">
</p>

---

## 🔌 Supporto Multi-Motore

| Motore | Adapter | Punti chiave |
| :--- | :--- | :--- |
| [Docusaurus v3][docusaurus] | `DocusaurusAdapter` | Versioned docs, alias `@site/`, Ghost Route detection |
| [MkDocs][mkdocs] | `MkDocsAdapter` | Modalità i18n suffix + folder, `fallback_to_default` |
| [Zensical][zensical] | `ZensicalAdapter` | Proxy trasparente per `mkdocs.yml` |
| Qualsiasi cartella | `StandaloneAdapter` | Controlli integrità — rilevamento orfani disabilitato senza contratto nav |

Vedi l'[Adapter API][docs-arch] per l'interfaccia plugin. I terzi adapter si installano via il gruppo entry-point `zenzic.adapters`.

---

## ⚙️ Configurazione

Zero-config per default. Vedi la [Guida alla Configurazione][docs-it-home] per lo schema completo di `zenzic.toml`.

```bash
zenzic init        # Genera zenzic.toml con valori auto-rilevati
```

---

## 🔄 Integrazione CI/CD

```yaml
- uses: PythonWoods/zenzic-action@v1
  with:
    format: sarif
    upload-sarif: "true"
```

Per integrazione `uvx` zero-install e gate di regressione, vedi la [Guida CI/CD][docs-it-cicd].

---

## 📦 Installazione

```bash
# Zero-install, audit one-shot (raccomandato per CI ed esplorazione)
uvx zenzic check all ./docs

# Tool CLI globale
uv tool install zenzic

# Dipendenza dev pinned
uv add --dev zenzic

# pip
pip install zenzic
```

---

## 📖 Documentazione

| Area | URL | Destinatario |
| :--- | :--- | :--- |
| 👤 Guida Utente | [zenzic.dev/it/docs][docs-it-home] | Installazione, configurazione, CI/CD, codici finding |
| 🔧 Developer Portal | [zenzic.dev/developers][docs-developers] | Adapter, ADR, architettura CLI, mutation testing |
| 🛡️ Sicurezza | [Engineering Ledger][docs-eng-ledger] · [SECURITY.md][security] | Reviewer di sicurezza |

---

## 🤝 Contribuire

1. Apri una [issue][issues] per discutere la modifica.
2. Leggi la [Guida ai Contributi][contributing].
3. Ogni PR deve passare `just verify` e includere header SPDX sui nuovi file.

Vedi anche: [Code of Conduct][coc] · [Security Policy][security]

## 📎 Citare Zenzic

Un file [`CITATION.cff`][citation-cff] è presente nel repository. Clicca **"Cite this repository"** su GitHub per output APA o BibTeX.

## 📄 Licenza

Apache-2.0 — vedi [LICENSE][license].

---

<div align="center">
  <a href="https://zenzic.dev">
    <img src="assets/brand/pythonwoods-logo.svg" alt="PythonWoods" height="50" />
  </a>
  <p>
    <strong>Progettato con precisione da PythonWoods in Italia 🇮🇹</strong><br/>
    <em>"Building the Standard for Technical Document Integrity."</em>
  </p>
  <p>
    <a href="https://zenzic.dev"><strong>Documentazione</strong></a> &middot;
    <a href="https://github.com/PythonWoods"><strong>GitHub</strong></a> &middot;
    <a href="https://zenzic.dev/blog"><strong>Blog</strong></a>
  </p>
</div>

<!-- ─── Definizioni link di riferimento ──────────────────────────────────────── -->

[mkdocs]:            https://www.mkdocs.org/
[docusaurus]:        https://docusaurus.io/
[zensical]:          https://zensical.org/
[uv]:                https://docs.astral.sh/uv/
[docs-it-home]:      https://zenzic.dev/it/docs/
[docs-it-badges]:    https://zenzic.dev/it/docs/how-to/add-badges/
[docs-it-cicd]:      https://zenzic.dev/it/docs/how-to/configure-ci-cd/
[docs-arch]:         https://zenzic.dev/developers/explanation/engineering-ledger
[docs-developers]:   https://zenzic.dev/developers/
[docs-eng-ledger]:   https://zenzic.dev/developers/explanation/engineering-ledger
[contributing]:      CONTRIBUTING.it.md
[license]:           LICENSE
[citation-cff]:      CITATION.cff
[coc]:               CODE_OF_CONDUCT.md
[security]:          SECURITY.md
[issues]:            https://github.com/PythonWoods/zenzic/issues
