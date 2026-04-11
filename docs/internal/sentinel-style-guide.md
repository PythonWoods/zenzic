<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Sentinel Style Guide {#sentinel-style-guide}

> *"The Sentinel's rigour in code must extend to every pixel the user sees."*

This document codifies the **Sentinel Visual Language** — the binding rules
for all Zenzic documentation pages. Every contributor must follow these
rules. Reviewers must reject PRs that violate them.

**Directive:** ZRT-DOC-002

---

## 1. Card Rule (High-Density UX) {#card-rule}

Navigation cards orient. They do **not** replace the sidebar.

### Structure

Every card in a `<div class="grid cards" markdown>` block must have exactly:

1. An **icon** (Lucide or Octicons — see §3).
2. A **bold title**.
3. A **description** of at most two lines.
4. A **single action link** using the arrow prefix.

### Canonical example

```markdown
- :lucide-play: &nbsp; **User Guide**

    Everything you need to install, configure, and integrate Zenzic into
    your CI/CD workflow.

    [:octicons-arrow-right-24: Explore the Guide](../usage/index.md)
```

### Forbidden patterns

| Pattern | Why |
| :--- | :--- |
| Horizontal link chains (`·`-separated) | Creates a wall of text; impossible to scan |
| Nested `<li>` lists inside a card | Breaks card height uniformity |
| `---` separators inside a card | Adds visual noise without information gain |
| Cards with zero action links | Dead-end; the user has nowhere to go |

### Exception

**Presentation cards** (e.g., homepage "Sentinel in Action" demos) may omit
the action link because their purpose is visual demonstration, not navigation.
They must still receive the card CSS (border, hover, transition).

---

## 2. Admonition Taxonomy {#admonition-taxonomy}

Each admonition type has one — and only one — semantic role.

| Type | Role | When to use |
| :--- | :--- | :--- |
| `!!! tip` | **Quick Win** | One-liner commands the reader can run immediately |
| `!!! example` | **Sentinel Output** | CLI output blocks and Sentinel report samples |
| `!!! danger` | **Security Gate** | Exit Code 2 (credentials) and Exit Code 3 (path traversal) only |
| `!!! warning` | **Design Constraint** | Architectural rules, contributor policies, "use sparingly" caveats |
| `!!! note` | **Clarification** | Engine-specific facts, contributor onboarding, multi-step guidance |
| `!!! abstract` | **Cross-Reference Bridge** | Links from the current section to the next actionable step |
| `!!! info` | **Community CTA** | Engagement calls ("Help us grow", "Join the discussion") |
| `!!! quote` | **Philosophy** | Project vision, design manifesto, Sentinel creed |

### Enforcement

If a block does not fit any category above, rewrite it as prose. Admonitions
are not decoration.

---

## 3. Iconography Law (ZRT-DOC-003) {#iconography}

### Hierarchy

| Priority | Set | Scope | Example |
| :---: | :--- | :--- | :--- |
| 1 | **Lucide** (`:lucide-*:`) | All UI and navigation icons | `:lucide-play:`, `:lucide-book:` |
| 2 | **Octicons** (`:octicons-*:`) | GitHub / developer workflow concepts | `:octicons-arrow-right-24:`, `:octicons-mark-github-24:` |
| 3 | **Simple Icons** (`:simple-*:`) | Third-party brand logos **only** | `:simple-pypi:`, `:simple-astral:` |
| — | ~~Material~~ (`:material-*:`) | **BANNED** | — |

### Rules

- **Semantic consistency:** if an icon represents "Contribute" on one page, it
  must be the same icon on every page.
- **No mixing:** a single card grid must not combine icons from different sets
  (exception: Octicons arrow in action links alongside Lucide title icons).

---

## 4. Anchor ID Protocol (ZRT-DOC-004) {#anchor-ids}

### When to add explicit IDs

Add `{#id}` to a heading when it satisfies **any** of:

1. It is an **H1 page title**.
2. It is referenced by a cross-page link (`[text](page.md#anchor)`).
3. It appears in `mkdocs.yml` nav entries pointing to a specific section.

### i18n Invariant

The canonical ID is always the **English slug**. Italian (and any future
language) pages must use the same `{#id}` value:

```markdown
<!-- EN -->
## Getting Started {#getting-started}

<!-- IT -->
## Inizia Ora {#getting-started}
```

This ensures the VSM resolver and cross-language links never break due to
translation-dependent slug generation.

### Heading format

```markdown
## Section Title {#section-title}
```

Do not add IDs to headings that are never linked to externally. Every
explicit ID is a maintenance contract.

---

## 5. Code Block Rule {#code-blocks}

Every opening fence **must** carry a language tag:

| Fence | Verdict |
| :--- | :---: |
| ` ```python ` | ✓ |
| ` ```bash ` | ✓ |
| ` ```toml ` | ✓ |
| ` ```text ` | ✓ (plain output) |
| ` ``` ` | ✗ **FORBIDDEN** |

Use `text` for output that has no syntax highlighting. Naked fences hurt
accessibility tools and syntax highlighters.

**Gutter specificity:** for CLI output shown inside `!!! example` blocks,
always use the `text` tag to prevent the syntax highlighter from generating
random colours on log strings or file paths.

---

## 6. SPDX Header {#spdx-header}

Every `.md` file must begin with:

```html
<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
```

Files with YAML frontmatter place the SPDX block immediately after the
closing `---`.

---

## 7. Visual Consistency Checklist {#checklist}

Before submitting a PR, verify:

- [ ] Every card grid follows §1 (single action link).
- [ ] Every admonition matches its §2 role.
- [ ] No `:material-*:` icons remain (§3).
- [ ] Cross-referenced headings have explicit `{#id}` (§4).
- [ ] No naked code fences exist (§5).
- [ ] SPDX header is present (§6).
- [ ] Italian mirror is structurally identical to English.
