# MkDocs Basic

This fixture represents a clean MkDocs 1.6-style documentation tree.

It is intentionally small but complete enough to validate navigation parsing,
route classification, and source-only linting behavior with deterministic
results. The goal is to provide a reliable benchmark that can be executed in
CI without network assumptions or build-engine subprocess dependencies.

## Contents

- [Guide](guide/index.md)
- [API](api.md)

The navigation includes nested sections and one external link in mkdocs.yml.
Zenzic parses all of it from source configuration without running mkdocs build.
