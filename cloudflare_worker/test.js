// SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
// SPDX-License-Identifier: Apache-2.0

// ZENZIC ROUTING KERNEL TEST SUITE
import { matchRoute } from "./worker.js";

const TEST_CASES = [
  [
    "/docs",
    "/"
  ],
  [
    "/docs/",
    "/"
  ],
  [
    "/doc",
    "/"
  ],
  [
    "/doc/",
    "/"
  ],
  [
    "/it",
    "/"
  ],
  [
    "/it/",
    "/"
  ],
  [
    "/developers/explanation/adr-vault/adr-lint-source",
    "/developers/explanation/adr-vault/records/adr-lint-source/"
  ],
  [
    "/developers/explanation/adr-vault/adr-discovery",
    "/developers/explanation/adr-vault/records/adr-discovery/"
  ],
  [
    "/developers/explanation/adr-vault/adr-020",
    "/developers/explanation/adr-vault/records/adr-020-mirror-law/"
  ],
  [
    "/developers/explanation/adr-vault/adr-021",
    "/developers/explanation/adr-vault/records/adr-021-parallel-audit/"
  ],
  [
    "/developers/explanation/adr-vault/adr-regex-acl",
    "/developers/explanation/adr-vault/records/adr-regex-acl/"
  ],
  [
    "/developers/explanation/adr-vault/adr-path-sovereignty",
    "/developers/explanation/adr-vault/records/adr-path-sovereignty/"
  ],
  [
    "/developers/explanation/adr-vault/adr-agnostic-universalism",
    "/developers/explanation/adr-vault/records/adr-agnostic-universalism/"
  ],
  [
    "/developers/explanation/adr-vault/adr-native-telemetry",
    "/developers/explanation/adr-vault/records/adr-native-telemetry/"
  ],
  [
    "/developers/explanation/adr-vault/adr-unified-perimeter",
    "/developers/explanation/adr-vault/records/adr-unified-perimeter/"
  ],
  [
    "/developers/explanation/adr-discovery",
    "/developers/explanation/adr-vault/records/adr-discovery/"
  ],
  [
    "/developers/explanation/adr-parallel-early-termination",
    "/developers/explanation/adr-vault/records/adr-021-parallel-audit/"
  ],
  [
    "/developers/explanation/adr-bilingual-structural",
    "/developers/explanation/adr-vault/records/adr-bilingual-structural/"
  ],
  [
    "/developers/explanation/adr-sovereign-sandbox",
    "/developers/explanation/adr-vault/records/adr-007-sovereign-sandbox/"
  ],
  [
    "/developers/explanation/adr-zero-subprocesses",
    "/developers/explanation/adr-vault/records/adr-002-zero-subprocesses/"
  ],
  [
    "/it/developers/explanation/adr-vault/",
    "/developers/explanation/adr-vault/records/"
  ],
  [
    "/it/developers/explanation/adr-vault/test-item/foo",
    "/developers/explanation/adr-vault/records/test-item/foo"
  ],
  [
    "/blog/welcome",
    "/blog/2026/04/28/welcome-to-the-zenzic-blog/"
  ],
  [
    "/blog/welcome/",
    "/blog/2026/04/28/welcome-to-the-zenzic-blog/"
  ],
  [
    "/blog/zenzic-v0160-engineering-determinism-into-documentation-pipelines",
    "/blog/2026/06/27/zenzic-v0160-engineering-determinism-into-documentation-pipelines/"
  ],
  [
    "/it/blog/",
    "/blog/"
  ],
  [
    "/it/blog/test-item/foo",
    "/blog/"
  ],
  [
    "/it/docs/how-to/examples/",
    "/tutorials/examples/"
  ],
  [
    "/it/docs/how-to/examples/test-item/foo",
    "/tutorials/examples/test-item/foo"
  ],
  [
    "/it/docs/tutorials/examples/",
    "/tutorials/examples/"
  ],
  [
    "/it/docs/tutorials/examples/test-item/foo",
    "/tutorials/examples/test-item/foo"
  ],
  [
    "/it/docs/how-to/",
    "/how-to/"
  ],
  [
    "/it/docs/how-to/test-item/foo",
    "/how-to/test-item/foo"
  ],
  [
    "/docs/how-to/",
    "/how-to/"
  ],
  [
    "/docs/how-to/test-item/foo",
    "/how-to/test-item/foo"
  ],
  [
    "/it/docs/reference/",
    "/reference/"
  ],
  [
    "/it/docs/reference/test-item/foo",
    "/reference/test-item/foo"
  ],
  [
    "/docs/reference/",
    "/reference/"
  ],
  [
    "/docs/reference/test-item/foo",
    "/reference/test-item/foo"
  ],
  [
    "/it/docs/explanation/",
    "/explanation/"
  ],
  [
    "/it/docs/explanation/test-item/foo",
    "/explanation/test-item/foo"
  ],
  [
    "/docs/explanation/",
    "/explanation/"
  ],
  [
    "/docs/explanation/test-item/foo",
    "/explanation/test-item/foo"
  ],
  [
    "/it/docs/developers/",
    "/developers/"
  ],
  [
    "/it/docs/developers/test-item/foo",
    "/developers/test-item/foo"
  ],
  [
    "/docs/developers/",
    "/developers/"
  ],
  [
    "/docs/developers/test-item/foo",
    "/developers/test-item/foo"
  ],
  [
    "/tutorials/examples/z6xx-brand/z602-i18n-parity/",
    "/tutorials/examples/"
  ],
  [
    "/tutorials/examples/z6xx-brand/z602-i18n-parity",
    "/tutorials/examples/"
  ],
  [
    "/blog/tags/",
    "/blog/"
  ],
  [
    "/blog/tags/test-item/foo",
    "/blog/"
  ],
  [
    "/category/",
    "/"
  ],
  [
    "/category/test-item/foo",
    "/"
  ],
  [
    "/developers/category/",
    "/developers/"
  ],
  [
    "/developers/category/test-item/foo",
    "/developers/"
  ],
  [
    "/it/",
    "/"
  ],
  [
    "/it/test-item/foo",
    "/"
  ],
  [
    "/docs/",
    "/"
  ],
  [
    "/docs/test-item/foo",
    "/"
  ],
  [
    "/random-path-that-does-not-exist",
    null
  ]
];

let pass = 0;
let fail = 0;

for (const [input, expected] of TEST_CASES) {
    const route = matchRoute(input);

    let result = null;
    if (route) {
        if (route.strip) {
            result = input.replace(route.from, route.to);
        } else {
            result = route.to;
        }
    }

    if (result === expected) {
        pass++;
    } else {
        fail++;
        console.error(`FAIL: ${input}\n  Expected: ${expected}\n  Got:      ${result}`);
    }
}

console.log(`\nTests completed: ${pass} passed, ${fail} failed.`);
if (fail > 0) {
    process.exit(1);
}
