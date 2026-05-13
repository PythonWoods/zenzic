<!-- markdownlint-disable MD052 -->
# Reference Graph Integrity — Example Document

This document intentionally contains three reference-graph violations
to demonstrate Z301, Z302, and Z303 detection.

## Z301 — Dangling Reference

The following link uses a reference ID that is never defined in this file:

See [the configuration guide][missing-id].

Without a corresponding definition `[missing-id]: …`, Zenzic emits Z301 DANGLING_REF.

## Z302 — Dead Definition

The definition below is declared but never used as a link target:

Zenzic emits Z302 DEAD_DEF for any `[id]: url` entry with no `[text][id]` reference.

## Z303 — Duplicate Definition

The following definition appears twice in this file:

Zenzic emits Z303 DUPLICATE_DEF when the same reference ID is defined more than once.

## Baseline content

This section contains valid content to ensure the document is not also flagged
for Z502 SHORT_CONTENT. Reference-graph errors fire independently of content length.
The three violations above are the only expected findings from this file.
