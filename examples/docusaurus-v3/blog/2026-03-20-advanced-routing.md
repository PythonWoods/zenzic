---
title: Advanced Routing with Docusaurus
date: 2026-03-20
tags: [tutorial, docusaurus]
authors: [pythonwoods]
---

This second post explores routing conventions in Docusaurus v3. It carries the
`tutorial` and `docusaurus` tags, so Zenzic will extend the virtual route set:

- `/blog/tags/tutorial/` — now backed by **two** source files (union of posts)
- `/blog/tags/docusaurus/`

<!-- truncate -->

## Tag slugs and Zenzic validation

Docusaurus converts tag labels to URL slugs by lowercasing and stripping special
characters. Zenzic applies the same normalisation (`_slugify_tag`) so the virtual
route URLs it registers are identical to those Docusaurus would render — no false
positives, no missed routes.

## Source file traceability

Every virtual route carries a `source_files` set that lists the exact blog posts
whose frontmatter activated it. The `/blog/tags/tutorial/` route, for instance,
traces back to both `2026-01-15-getting-started.md` and this file. If either post
is deleted, the route remains valid as long as one source survives — and Zenzic
will tell you exactly which file broke coverage when the last one disappears.
