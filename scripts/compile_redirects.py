#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0

import json
import sys
from pathlib import Path


def parse_redirects(file_path: Path):
    routes = []
    with open(file_path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) != 3:
                print(f"Warning: line {line_num} does not have exactly 3 parts: {line}")
                continue

            from_path, to_path, code = parts
            try:
                code = int(code)
            except ValueError:
                print(f"Warning: line {line_num} has invalid status code: {code}")
                continue

            if from_path.endswith("*"):
                from_prefix = from_path[:-1]
                if to_path.endswith(":splat") or to_path.endswith(":splat/"):
                    to_prefix = to_path.replace(":splat", "")
                    # If it ended in splat/ and we removed splat, it ends in /.
                    # Let's ensure no double slash.
                    to_prefix = to_prefix.replace("//", "/")
                    routes.append(
                        {
                            "type": "prefix",
                            "from": from_prefix,
                            "to": to_prefix,
                            "strip": True,
                            "code": code,
                        }
                    )
                else:
                    routes.append(
                        {
                            "type": "prefix",
                            "from": from_prefix,
                            "to": to_path,
                            "strip": False,
                            "code": code,
                        }
                    )
            else:
                routes.append(
                    {
                        "type": "exact",
                        "from": from_path,
                        "to": to_path,
                        "strip": False,
                        "code": code,
                    }
                )
    return routes


def generate_worker(routes, out_dir: Path):
    routes_json = json.dumps(routes, indent=2)

    worker_js = f"""// SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
// SPDX-License-Identifier: Apache-2.0

// ZENZIC ROUTING KERNEL v9 (RUNTIME)
// Auto-generated from docs/_redirects

export const ROUTES = {routes_json};

export function matchRoute(path) {{
    for (const r of ROUTES) {{
        if (r.type === "exact" && path === r.from) {{
            return r;
        }}
        if (r.type === "prefix" && path.startsWith(r.from)) {{
            return r;
        }}
    }}
    return null;
}}

export default {{
    async fetch(request) {{
        const url = new URL(request.url);
        const path = url.pathname;

        const route = matchRoute(path);

        if (!route) {{
            return new Response("Not Found", {{ status: 404 }});
        }}

        let target = route.to;
        if (route.strip) {{
            target = path.replace(route.from, route.to);
        }}

        return Response.redirect(new URL(target, url.origin), route.code);
    }},
}};
"""
    with open(out_dir / "worker.js", "w", encoding="utf-8") as f:
        f.write(worker_js)


def generate_tests(routes, out_dir: Path):
    test_cases = []

    for r in routes:
        if r["type"] == "exact":
            test_cases.append((r["from"], r["to"]))
        elif r["type"] == "prefix":
            # Test exact prefix match if not empty
            test_cases.append((r["from"], r["to"] if r["strip"] else r["to"]))

            # Test with trailing subpath
            test_subpath = "test-item/foo"
            input_path = r["from"] + test_subpath
            if r["strip"]:
                expected = r["to"] + test_subpath
            else:
                expected = r["to"]
            test_cases.append((input_path, expected))

    # Add negative tests
    test_cases.append(("/random-path-that-does-not-exist", None))

    tests_json = json.dumps(test_cases, indent=2)

    test_js = f"""// SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
// SPDX-License-Identifier: Apache-2.0

// ZENZIC ROUTING KERNEL TEST SUITE
import {{ matchRoute }} from "./worker.js";

const TEST_CASES = {tests_json};

let pass = 0;
let fail = 0;

for (const [input, expected] of TEST_CASES) {{
    const route = matchRoute(input);

    let result = null;
    if (route) {{
        if (route.strip) {{
            result = input.replace(route.from, route.to);
        }} else {{
            result = route.to;
        }}
    }}

    if (result === expected) {{
        pass++;
    }} else {{
        fail++;
        console.error(`FAIL: ${{input}}\\n  Expected: ${{expected}}\\n  Got:      ${{result}}`);
    }}
}}

console.log(`\\nTests completed: ${{pass}} passed, ${{fail}} failed.`);
if (fail > 0) {{
    process.exit(1);
}}
"""
    with open(out_dir / "test.js", "w", encoding="utf-8") as f:
        f.write(test_js)


if __name__ == "__main__":
    workspace_root = Path(__file__).parent.parent
    redirects_path = workspace_root / "docs" / "_redirects"
    out_dir = workspace_root / "cloudflare_worker"

    if not redirects_path.exists():
        print(f"Error: {redirects_path} not found.")
        sys.exit(1)

    routes = parse_redirects(redirects_path)
    generate_worker(routes, out_dir)
    generate_tests(routes, out_dir)

    print(f"Successfully compiled {len(routes)} routes to {out_dir}/worker.js and test.js")
