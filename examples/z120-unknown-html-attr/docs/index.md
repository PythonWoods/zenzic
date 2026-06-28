<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Documentation Index

This page demonstrates **Z120 UNKNOWN_HTML_ATTRIBUTE**.

## Examples of unknown attributes

A link with `hreflang` (HTML5 standard but not in Safe-Core list):

<a href="./target.md" hreflang="en">English version</a>

A link with `ping` attribute (rarely used, triggers Z120):

<a href="./target.md" ping="https://analytics.example.com/track">Tracked link</a>

A link with `referrerpolicy` (security-relevant, not yet in Safe-Core):

<a href="./target.md" referrerpolicy="no-referrer">No-referrer link</a>

## Multiline tag — stress test (5+ attributes)

<a
  href="./target.md"
  class="nav-link"
  title="Titolo del link"
  rel="noopener"
  hreflang="it"
>Collegamento italiano</a>

## How to suppress

If the attribute is intentional, add `data-zenzic-ignore`:

```html
<a href="./target.md" hreflang="en" data-zenzic-ignore>English</a>
```
