# Setup

Install dependencies and run a check:

```bash
pip install zenzic
zenzic check all --show-info
```

The `--show-info` flag reveals `MISSING_DIRECTORY_INDEX` findings for
directories that lack a landing page. These are info-level notices: they
do not affect the exit code or the quality score, but they highlight
potential 404 URLs in a live site.

Return to the [Guides index](index.md) or [Home](../index.md).
