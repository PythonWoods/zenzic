# Inline Suppression Examples

This page demonstrates the `zenzic:ignore` inline syntax.
Five violations are suppressed here — each costs 1 pt of Technical Debt.

## Usage Pattern

Append the ignore comment at the end of the line containing the violation:

1. AncientBrand was the original name of this product. <!-- zenzic:ignore: Z601 historical reference -->
2. The AncientBrand SDK is still referenced in internal docs. <!-- zenzic:ignore: Z601 historical reference -->
3. AncientBrand 2.0 was the last version released under the old name. <!-- zenzic:ignore: Z601 historical reference -->
4. Migration from AncientBrand requires a configuration update. <!-- zenzic:ignore: Z601 historical reference -->
5. AncientBrand users should follow the migration guide below. <!-- zenzic:ignore: Z601 historical reference -->

## Why Inline Suppression Costs Points

Each `zenzic:ignore` comment is counted as an **active suppression**.
Active suppressions are Technical Debt: they hide findings from the audit stream.

The quality score deducts **1 pt per suppression** (up to the governance cap of 30),
and **2 pt per suppression** beyond the cap.

Use `zenzic explain Z601` to see the exact penalty for this rule.
