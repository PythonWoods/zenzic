# Z118 — Stale Global Suppression

This fixture demonstrates Zenzic's `Z118` governance code, which ensures that global suppressions (`directory_policies`, `excluded_file_patterns`, and `excluded_external_urls`) in `.zenzic.toml` are not stale.

If a policy suppresses an issue that no longer exists, Z118 flags it to prevent silent configuration rot.

## Setup

In `.zenzic.toml`:

```toml
[governance.directory_policies]
"docs/clean-page.md" = ["Z101"]
```

Because `docs/clean-page.md` has no broken links, the suppression is unused, triggering Z118.
