// SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
// SPDX-License-Identifier: Apache-2.0

// ZENZIC ROUTING KERNEL v9 (RUNTIME)
// Auto-generated from docs/_redirects

export const ROUTES = [
  {
    "type": "prefix",
    "from": "/blog/tags/",
    "to": "/blog/",
    "strip": false,
    "code": 301
  },
  {
    "type": "prefix",
    "from": "/category/",
    "to": "/blog/",
    "strip": false,
    "code": 301
  },
  {
    "type": "exact",
    "from": "/developers/explanation/adr-discovery",
    "to": "/developers/explanation/adr-vault/records/adr-discovery/",
    "strip": false,
    "code": 301
  },
  {
    "type": "exact",
    "from": "/developers/explanation/adr-discovery/",
    "to": "/developers/explanation/adr-vault/records/adr-discovery/",
    "strip": false,
    "code": 301
  },
  {
    "type": "exact",
    "from": "/developers/explanation/adr-parallel-early-termination",
    "to": "/developers/explanation/adr-vault/records/adr-021-parallel-audit/",
    "strip": false,
    "code": 301
  },
  {
    "type": "exact",
    "from": "/developers/explanation/adr-parallel-early-termination/",
    "to": "/developers/explanation/adr-vault/records/adr-021-parallel-audit/",
    "strip": false,
    "code": 301
  },
  {
    "type": "exact",
    "from": "/developers/explanation/adr-bilingual-structural",
    "to": "/developers/explanation/adr-vault/records/adr-bilingual-structural/",
    "strip": false,
    "code": 301
  },
  {
    "type": "exact",
    "from": "/developers/explanation/adr-bilingual-structural/",
    "to": "/developers/explanation/adr-vault/records/adr-bilingual-structural/",
    "strip": false,
    "code": 301
  },
  {
    "type": "prefix",
    "from": "/developers/explanation/adr-vault/",
    "to": "/developers/explanation/adr-vault/records/",
    "strip": true,
    "code": 301
  },
  {
    "type": "exact",
    "from": "/blog/welcome",
    "to": "/blog/2026/04/28/welcome-to-the-zenzic-blog/",
    "strip": false,
    "code": 301
  },
  {
    "type": "exact",
    "from": "/blog/welcome/",
    "to": "/blog/2026/04/28/welcome-to-the-zenzic-blog/",
    "strip": false,
    "code": 301
  },
  {
    "type": "exact",
    "from": "/blog/zenzic-v0160-engineering-determinism-into-documentation-pipelines",
    "to": "/blog/2026/06/27/zenzic-v0160-engineering-determinism-into-documentation-pipelines/",
    "strip": false,
    "code": 301
  },
  {
    "type": "prefix",
    "from": "/it/docs/how-to/examples/",
    "to": "/tutorials/examples/",
    "strip": true,
    "code": 301
  },
  {
    "type": "prefix",
    "from": "/it/docs/tutorials/examples/",
    "to": "/tutorials/examples/",
    "strip": true,
    "code": 301
  },
  {
    "type": "prefix",
    "from": "/it/docs/how-to/",
    "to": "/how-to/",
    "strip": true,
    "code": 301
  },
  {
    "type": "prefix",
    "from": "/docs/how-to/",
    "to": "/how-to/",
    "strip": true,
    "code": 301
  },
  {
    "type": "prefix",
    "from": "/it/docs/reference/",
    "to": "/reference/",
    "strip": true,
    "code": 301
  },
  {
    "type": "prefix",
    "from": "/docs/reference/",
    "to": "/reference/",
    "strip": true,
    "code": 301
  },
  {
    "type": "prefix",
    "from": "/it/docs/explanation/",
    "to": "/explanation/",
    "strip": true,
    "code": 301
  },
  {
    "type": "prefix",
    "from": "/docs/explanation/",
    "to": "/explanation/",
    "strip": true,
    "code": 301
  },
  {
    "type": "prefix",
    "from": "/it/docs/tutorials/",
    "to": "/tutorials/",
    "strip": true,
    "code": 301
  },
  {
    "type": "prefix",
    "from": "/docs/tutorials/",
    "to": "/tutorials/",
    "strip": true,
    "code": 301
  },
  {
    "type": "prefix",
    "from": "/it/docs/developers/",
    "to": "/developers/",
    "strip": true,
    "code": 301
  },
  {
    "type": "prefix",
    "from": "/docs/developers/",
    "to": "/developers/",
    "strip": true,
    "code": 301
  },
  {
    "type": "prefix",
    "from": "/it/",
    "to": "/",
    "strip": true,
    "code": 301
  },
  {
    "type": "prefix",
    "from": "/docs/",
    "to": "/",
    "strip": true,
    "code": 301
  }
];

export function matchRoute(path) {
    for (const r of ROUTES) {
        if (r.type === "exact" && path === r.from) {
            return r;
        }
        if (r.type === "prefix" && path.startsWith(r.from)) {
            return r;
        }
    }
    return null;
}

export default {
    async fetch(request) {
        const url = new URL(request.url);
        const path = url.pathname;

        const route = matchRoute(path);

        if (!route) {
            return new Response("Not Found", { status: 404 });
        }

        let target = route.to;
        if (route.strip) {
            target = path.replace(route.from, route.to);
        }

        return Response.redirect(new URL(target, url.origin), route.code);
    },
};
