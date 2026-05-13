# Asset Integrity — Reference Document

This document is correctly included in the navigation contract.
It serves as the baseline to confirm that Z405 and Z406 fire only for
the intentionally broken files in this example.

## Configuration

Asset scanning is enabled by default in `standalone` engine mode.
The `assets/` directory is scanned for files not referenced by any document.

## Navigation contract

In `standalone` mode, a navigation contract is defined by listing documents
in `[nav]` inside `zenzic.toml`. Any document present on disk but absent from
the contract is flagged as Z406 NAV_CONTRACT.

See `orphan.md` in this directory for a live Z406 demonstration.
