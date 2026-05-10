# Privacy Gate Demo — Enterprise Z204

This document is part of the **Z204 Privacy Gate** showcase example.

## What is Z204?

`Z204 FORBIDDEN_TERM` is a Zenzic Enterprise gate that blocks confidential
terms from leaking into public documentation.  It is the documentation
equivalent of a secret scanner: instead of credentials (Z201 Shield), it
targets contractual terms, internal project codenames, and PII markers.

## How it works

1. Declare `forbidden_patterns` in `.zenzic.local.toml` (git-ignored in production).
2. Zenzic merges the local overlay with `zenzic.toml` at runtime.
3. Every documentation file is scanned.  Any match triggers **exit code 2** —
   the same severity as a credential leak.

## Trigger line (intentional violation)

The product was previously developed under the internal codename **CODENAME-PHOENIX**
before its public launch.  This line intentionally triggers Z204 to demonstrate
the gate in action.

The staging environment at `internal-staging.example.corp` must never appear in
customer-facing documentation.

## Expected output

```text
docs/index.md:14  Z204  FORBIDDEN_TERM  'CODENAME-PHOENIX' — confidential term detected
docs/index.md:17  Z204  FORBIDDEN_TERM  'internal-staging.example.corp' — confidential term detected

Exit code: 2 (security_breach)
```

## Fix

Remove the forbidden terms from the documentation source, or add a project-specific
exception with `[suppressions]` in `zenzic.toml` if the term is intentionally
referenced for historical purposes (e.g., a changelog entry).
