<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z001 CORE_CONFIG_STRUCTURE — Gallery Example

**Category:** Z0xx Core / Bootstrap
**Expected exit:** 1 (errors)

## What this demonstrates

`.zenzic.toml` defines `suppression_cap = "high"` which violates the configuration schema (`suppression_cap` must be an integer). Zenzic immediately aborts the scan during bootstrap phase and outputs a validation error with code **Z001 CORE_CONFIG_STRUCTURE**.

## Run it

```bash
zenzic lab z001
# or directly:
zenzic check all
```

## Expected output

```text
Error: Configuration validation failed.
Detailed errors in .zenzic.toml:
  - line 10: Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='high', input_type=str]
```

## Real-world fix

Correct the configuration error in `.zenzic.toml` or `pyproject.toml` (e.g. by setting `suppression_cap` to an integer, or removing the invalid key).
