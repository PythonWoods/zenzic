# Zenzic Master Test Suite

## Z1xx: Link Integrity & HTML Hygiene

[Broken Relative Link](missing_page.md)
[Missing Anchor](#this-anchor-does-not-exist)
[Absolute Path Violation](/home/user/docs/secret.md)
[Circular Anchor](#z1xx-link-integrity--html-hygiene)
[](#empty-link-text)

<a href="valid.md" fakeattr="yes">Unknown Attribute (Z120)</a>
<a>Missing Href (Z121)</a>
<a href="#">Jump Link (Z122)</a>
<a href="mailto:test@example.com">Non-HTTP Scheme (Z123)</a>
<a href="valid.md" onclick="stealData()">Opaque Context (Z124)</a>

## Z2xx: Security (Inviolable)

Here is a leaked token: AKIAIOSFODNN7EXAMPLE
[Relative Path Traversal](../../../.env)
[Fatal OS Traversal](/etc/passwd)
<a href="javascript:alert('XSS')">Forbidden Scheme (Z205)</a>

## Z3xx: Reference Integrity

This is a [dangling reference][dangle].



## Z4xx: Asset Structure

![](https://example.com/image.png)
<img src="https://example.com/image.png">

## Z5xx: Content Quality

We need to fix this TODO before the next release.

```python
def broken_syntax(
```

```
echo "This code block has no language specified"
```

## Z6xx: Governance
<!-- zenzic:ignore: Z999 -->
