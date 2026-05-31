<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD045 -->

# Z403 — Missing Alt Text Gallery Example

This page contains an image element with no alt text,
demonstrating **Z403 MISSING_ALT** detection.

## Architecture Overview

The following diagram shows the system components:

![](diagram.png)

The `![](diagram.png)` syntax above has an empty alt attribute → **Z403**.

## What Zenzic Reports

```text
docs/index.md:9:  Z403  MISSING_ALT  image 'diagram.png' has no alt text
```

Run `zenzic check assets` to reproduce the finding.
