# Security Breach Demo — Scoring Override

This fixture demonstrates the **Security Override** in the Quartz Scoring Engine.

The project is otherwise spotless — clean links, complete navigation, no orphans.
Yet the score collapses to **0/100** because a single credential is present.

## Why a perfect project can score zero

The Zenzic Safe Harbor guarantee is unconditional:

> *A documentation portal that leaks credentials is not safe — regardless of
> how beautifully structured it is.*

## Deployment configuration

The deployment pipeline connects to AWS S3 for static asset hosting.
The access credentials below are used for the staging environment.

<!-- markdownlint-disable-next-line MD040 -- untagged block is intentional: Z505 + Z201 test fixture -->
```
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLEKEY
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

## Score breakdown

| Category | Weight | Status |
|----------|--------|--------|
| Structural | 40% | ✅ Clean |
| Content | 30% | ✅ Clean |
| Navigation | 20% | ✅ Clean |
| Brand | 10% | ✅ Clean |
| **Security Override** | — | 🔴 **Score → 0/100** |

## Run it

```bash
cd examples/scoring/security-breach

# Shield detects Z201 → exit code 2 (non-suppressible)
zenzic check references

# Score collapses to 0/100 (security_override = true)
zenzic score
```
