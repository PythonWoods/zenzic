<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Setup Avanzato

Questa pagina si trova a tre livelli di profondità nell'albero della documentazione:
`docs/guides/advanced/setup.it.md`. Dimostra che i link relativi agli asset condivisi
si risolvono correttamente da qualsiasi profondità di annidamento.

## Test della profondità dei link relativi

Da questa pagina (`docs/guides/advanced/`), la cartella degli asset è a due livelli sopra:

- [Scarica brand-kit.zip](../../assets/brand-kit.zip)
- [Scarica manual.pdf](../../assets/manual.pdf)

Questi percorsi vengono risolti da Zenzic relativamente alla posizione della pagina.
Non vengono mai usati percorsi assoluti (`/assets/...`) — romperebbero la portabilità.

## Navigazione tra le pagine

- [Torna alle Guide](../index.md)
- [Ottimizzazione delle prestazioni](tuning.md)
- [Riferimento API](../../reference/api.md)
- [Home](../../index.md)

## Frammento di configurazione

```yaml
# zenzic.toml — da posizionare nella root del repository
docs_dir = "docs"
fail_under = 100
excluded_build_artifacts = ["docs/assets/manual.pdf", "docs/assets/brand-kit.zip"]
```

Il campo `excluded_build_artifacts` indica a Zenzic che `manual.pdf` e `brand-kit.zip`
sono generati al momento del build. I link a essi vengono validati strutturalmente
senza richiedere che i file esistano su disco.
