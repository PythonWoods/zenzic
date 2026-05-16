# Z108: Empty Link Text (EMPTY_LINK_TEXT)

This example demonstrates the detection of empty links by the `Z108` rule.

## Technical Explanation

The `Z108` rule identifies Markdown links that have no descriptive text or contain only whitespace (e.g., `[]()` or `[  ](https://example.com)`). These are problematic for accessibility (screen readers) and user experience.

## Impact on Score

This rule falls under the **Structural** bucket. A violation will deduct points from the Technical Debt Score, potentially causing the CI pipeline to fail if the score drops below the configured `fail_under` threshold.

## Remediation

To fix a `Z108` violation, populate the link with meaningful, descriptive text that clearly indicates the link's destination or purpose.

* **Bad:** `[](/docs/api)`
* **Good:** `[API Documentation](/docs/api)`
