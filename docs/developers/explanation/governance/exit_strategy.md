---

description: "The Sovereignty Oath of Zenzic, declaring a zero-lock-in and zero-residue decommission policy."
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# The Sovereignty Oath: Zero Residue

> *"Zenzic is a static analyzer in your pipeline, not a chain. The ability to remove it
> is not a failure mode — it is a design requirement."*

---

## The Oath

Zenzic makes one unconditional promise: **it will never hold your codebase hostage.**

To ensure the integrity of the Privacy Gate, Zenzic's audit core is strictly read-only.
We believe that a document integrity engine should never be a source of unintended mutations. Any future
remediation features will be implemented as explicit, interactive utilities
(e.g. `zenzic fix`), keeping the analysis phase 100% mutation-free.

This document is the formal commitment of that promise.

---

## 1. Zero Residue Guarantee

When you remove Zenzic, what remains?

| Component | Residue After Removal |
| :--- | :--- |
| **Your source files** | Unchanged — Zenzic never writes or modifies content |
| **Your application code** | Unchanged — Zenzic is never imported at runtime |
| **Your Python types** | Unchanged — Zenzic uses `typing.Protocol`, not inheritance |
| **Your config format** | Standard `[tool.zenzic]` PEP convention — remove the section, done |
| **Your CI pipeline** | One workflow step — delete it |
| **Your pre-commit hooks** | One hook entry — remove it |

**Total removal time: 30 seconds.**

No migration scripts. No data format to convert. No architecture to unwind.

---

## 2. Why `typing.Protocol` Matters

Zenzic's adapter system uses [`typing.Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)
— the Python standard library's structural subtyping mechanism.

This is a deliberate architectural choice:

```python
# Zenzic adapter contract — structural subtyping only
class AdapterProtocol(Protocol):
    def get_docs_root(self) -> Path: ...
    def get_nav_paths(self) -> frozenset[str]: ...
    def get_metadata_files(self) -> frozenset[str]: ...
```

**What this means for you:**

- You do **not** need to subclass a Zenzic base class.
- Your code does **not** carry a Zenzic inheritance chain.
- If you remove Zenzic, your Python classes remain unchanged — no base class to strip

  out, no method overrides to remove, no MRO to audit.

The adapter is a structural contract. If your object has the right methods, Zenzic
accepts it. If Zenzic is removed, your object still works — it simply has no auditor.

---

## 3. PEP-Compliant Configuration

Zenzic configuration lives in the `[tool.zenzic]` section of `pyproject.toml` —
the standard [PEP 518](https://peps.python.org/pep-0518/) location for tool config:

```toml title="pyproject.toml"
[tool.zenzic]
docs_dir = "docs"
engine = "mkdocs"
```

Or in a standalone `.zenzic.toml` at the repository root.

**Removal procedure:**

```toml title="pyproject.toml (after)"
# [tool.zenzic] section deleted — no other changes needed
```

Or:

```bash
rm .zenzic.toml
```

The `[tool.zenzic]` section is an isolated namespace. Removing it does not affect
any other tool configuration. No cascading effects. No shared state.

---

## 4. The Decommissioning Process

Removing Zenzic from a project is designed to be trivial and leave no residual lock-in. For step-by-step instructions on decommissioning, see the [Install & First Run guide — Decommissioning Zenzic](../../../how-to/install.md#decommissioning-zenzic).

---

## 5. Why We Document the Exit

Trust is built on the **ability to leave**, not the requirement to stay.

A tool that makes departure difficult is not confident in its value — it is protecting
its own presence. The Zenzic trust model is Zero-Trust: including toward Zenzic itself.

The analyzer exists to protect your documentation. Not to protect itself.
