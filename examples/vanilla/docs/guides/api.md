<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Python API Reference

Zenzic exposes a programmatic interface for integration into build scripts,
pre-commit hooks, and CI pipelines that cannot use the CLI directly.

## Single-file scanning

```python
from pathlib import Path
from zenzic.core.scanner import ReferenceScanner

scanner = ReferenceScanner(file_path=Path("docs/index.md"))
report = scanner.scan()

for finding in report.rule_findings:
    print(f"{finding.file_path}:{finding.line_no} — {finding.message}")
```

## Full documentation tree

```python
from pathlib import Path
from zenzic.core.scanner import scan_docs_references_with_links

reports = scan_docs_references_with_links(docs_root=Path("docs"))
for report in reports:
    if report.has_errors():
        print(f"Errors in {report.file_path}")
```

## Exit code conventions

| Code | Meaning |
| --- | --- |
| `0` | All checks passed |
| `1` | One or more check failures (broken links, orphans, etc.) |
| `2` | Shield event — credential detected (non-suppressible) |

## Related

- [Setup guide](setup.md)
- [Home](../index.md)
