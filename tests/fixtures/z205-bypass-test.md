# Z205 Bypass Payloads

Questi payload servono a verificare che il parser prevenga il bypass dell'attributo security gate (Z205) tramite Parser Differential e Injection.

<!-- 1. Double Href Attack (Parser differential) -->
<a href="javascript:alert(1)" href="safe.md">Double Href Attack</a>

<!-- 2. HTML Entities -->
<a href="&#106;avascript:alert(1)">HTML Entities</a>

<!-- 3. Whitespace & Control Chars -->
<a href="java script:alert(1)">Whitespace</a>
<a href="java&#x09;script:alert(1)">Control Chars</a>
