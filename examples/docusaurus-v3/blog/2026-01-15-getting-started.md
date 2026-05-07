---
title: Getting Started with Docusaurus
date: 2026-01-15
tags: [tutorial, quickstart]
authors: [pythonwoods]
---

Welcome to the first post on this example blog. This post is tagged with `tutorial`
and `quickstart`, so Zenzic will generate two virtual routes:

- `/blog/tags/tutorial/`
- `/blog/tags/quickstart/`

Both routes are validated against every link in `docs/` that references them.

<!-- truncate -->

## Why Virtual Routes matter

When you write `[see tutorials](/blog/tags/tutorial/)` in a docs page, Zenzic
verifies that at least one blog post carries `tags: [tutorial]` in its frontmatter.
If no post does, Docusaurus will never render that page and the link silently 404s.

Zenzic catches this at lint time — no build needed.
