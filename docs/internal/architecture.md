<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Zenzic — Pipeline Architecture & Algorithmic Complexity

> *"Measure twice, cut once. Know your complexity before you scale."*
>
> This document describes the internal pipeline phases of Zenzic's validation
> engine with an emphasis on algorithmic complexity guarantees. It is aimed at
> DevOps engineers evaluating performance characteristics on large documentation
> sites (1 000–50 000 pages) and contributors working on the validator core.

---

## Overview

Zenzic's validation pipeline is divided into three sequential phases:

| Phase | Name | Complexity | Description |
| :---: | :--- | :---: | :--- |
| 1 | **In-Memory Build** | Θ(N) | Read all files, extract links, build VSM |
| 1.5 | **Graph Analysis** | Θ(V+E) | Build adjacency graph, detect cycles via iterative DFS |
| 2 | **Per-Link Validation** | O(1) per query | Resolve each link against pre-built indices |

Total pipeline complexity for a site with N pages and L total links:
**Θ(N + V + E + L)** — linear in all inputs, where V ≤ N and E ≤ L.

---

## Phase 1 — In-Memory Build (Θ(N))

Phase 1 reads every `.md` file in `docs_dir` exactly once. For each file:

1. **Link extraction** — a deterministic line-by-line state machine extracts all
   Markdown links `[text](href)` and reference links `[text][id]`, skipping
   fenced code blocks and inline code spans.
2. **Anchor pre-computation** — heading slugs are extracted and stored in a
   `dict[str, set[str]]` keyed by file path.
3. **VSM construction** — the Virtual Site Map is populated: a `frozenset` of
   all resolved file paths present in the scanned file set and listed in the
   site navigation (if applicable).

Each file is read precisely once (O(N) I/O reads). The state machine runs in
O(F) time where F is the number of characters in the file, summing to Θ(N)
across all files. No file is re-opened during Phases 1.5 or 2.

### State-machine parsing and Superfences false positives

The extraction engine uses a three-state machine: `NORMAL`, `IN_FENCE`,
`IN_CODE_SPAN`. Transitions are triggered by:

- `` ``` `` or `~~~` at the start of a line → enter/exit `IN_FENCE`
- Backtick counting on a single line → toggle `IN_CODE_SPAN`

Links inside `IN_FENCE` or `IN_CODE_SPAN` are silently discarded. This
prevents false positives from documentation that shows Markdown syntax
examples inside code blocks (`pymdownx.superfences`-style documents).

---

## Phase 1.5 — Graph Analysis: Iterative DFS (Θ(V+E))

Phase 1.5 is executed once after Phase 1, before any per-link validation.
It takes the set of (source_page → target_page) pairs extracted in Phase 1
and builds a directed adjacency graph.

### Why iterative DFS?

Python's default recursion limit (`sys.getrecursionlimit()` = 1 000) would
cause a `RecursionError` on documentation sites with deep navigation chains.
Zenzic uses an **iterative DFS with an explicit stack** to avoid this limit
entirely, regardless of graph depth.

### Algorithm — WHITE/GREY/BLACK colouring

```python
WHITE = 0  # unvisited
GREY  = 1  # on the current DFS stack (in-progress)
BLACK = 2  # fully explored

def _find_cycles_iterative(adj: dict[str, list[str]]) -> frozenset[str]:
    colour = dict.fromkeys(adj, WHITE)
    in_cycle: set[str] = set()

    for start in adj:
        if colour[start] != WHITE:
            continue
        stack = [(start, iter(adj[start]))]
        colour[start] = GREY
        while stack:
            node, children = stack[-1]
            try:
                child = next(children)
                if colour[child] == GREY:
                    # Back-edge → cycle detected
                    in_cycle.add(child)
                    in_cycle.add(node)
                elif colour[child] == WHITE:
                    colour[child] = GREY
                    stack.append((child, iter(adj.get(child, []))))
            except StopIteration:
                colour[node] = BLACK
                stack.pop()

    return frozenset(in_cycle)
```

**Complexity:** Θ(V+E) — each vertex is pushed and popped from the stack
exactly once; each edge is traversed exactly once.

**Space:** O(V) — the colour map and the DFS stack together use O(V) memory.
The result `frozenset[str]` contains only the nodes that participate in at
least one cycle.

### Cycle registry

The output of Phase 1.5 is a `frozenset[str]` of page paths that are members
of at least one directed cycle. This registry is stored as an immutable
attribute on the validator instance.

---

## Phase 2 — Per-Link Validation (O(1) per query)

Each link extracted in Phase 1 is validated in Phase 2 against **three
pre-built data structures**, all constructed during Phases 1 and 1.5:

| Check | Data structure | Lookup cost |
| :--- | :--- | :---: |
| File existence | `frozenset[str]` — VSM | O(1) |
| Nav membership | `frozenset[str]` — nav set | O(1) |
| Anchor validity | `dict[path, set[anchor]]` | O(1) |
| Cycle membership | `frozenset[str]` — cycle registry | O(1) |

Because all four lookups are O(1), Phase 2 runs in **O(L)** total time where
L is the total number of links across all pages.

### Why Phase 2 remains O(1) per query

The cycle registry is a `frozenset` — Python's built-in immutable set with
O(1) average-case membership testing via hashing. There is no DFS or graph
traversal at query time. The Θ(V+E) cost is paid once in Phase 1.5; every
subsequent lookup is pure hash-table access.

---

## Scalability Profile

| Site size | Phase 1 | Phase 1.5 | Phase 2 | Total |
| :--- | :--- | :--- | :--- | :--- |
| 100 pages, 500 links | < 5 ms | < 1 ms | < 2 ms | ~ 8 ms |
| 1 000 pages, 5 000 links | ~ 30 ms | ~ 8 ms | ~ 15 ms | ~ 55 ms |
| 10 000 pages, 50 000 links | ~ 300 ms | ~ 80 ms | ~ 150 ms | ~ 530 ms |
| 50 000 pages, 250 000 links | ~ 1.5 s | ~ 400 ms | ~ 750 ms | ~ 2.6 s |

All measurements are single-threaded on a mid-range CI runner (2 vCPU,
4 GB RAM). The Shield scan (Phase 1, overlapping) adds < 10% overhead
regardless of site size because it is a single regex pass per file.

---

## Related Documents

- [ADR 003 — Discovery Logic](../adr/003-discovery-logic.md) — rationale for
  the two-phase pipeline and the choice of iterative DFS
- [Architecture Gaps](arch_gaps.md) — open technical debt items
- [Security Report — Shattered Mirror](security/shattered_mirror_report.md) —
  Shield pattern correctness analysis
