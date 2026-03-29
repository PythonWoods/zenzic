<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Tutorial

This tutorial page is intentionally well-formed: it has enough content to pass the placeholder
check and does not contain any forbidden stub patterns. The only issue here is the invalid Python
code block below.

## Installation

Install Zenzic as a project dev dependency:

```bash
uv add --dev zenzic
```

Then run all checks:

```bash
zenzic check all
```

## Broken snippet

The following Python block contains a `SyntaxError` — the function definition is missing its
closing colon. Zenzic's snippet check will catch this at build time.

```python
def my_function() ->
    return "This line is unreachable because the signature is broken"
```

No other issues exist on this page.
