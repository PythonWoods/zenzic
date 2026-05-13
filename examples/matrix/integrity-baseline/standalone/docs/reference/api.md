<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# API Reference

This document describes all available API endpoints. For configuration details,
see the [configuration guide](../how-to/configure.md).

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check — returns 200 when the service is operational |
| `POST` | `/check` | Run a full Zenzic check on the provided documentation directory |

## Response Codes

All endpoints return standard HTTP status codes. A `200` response indicates success.
A `422` response indicates invalid input — check the `errors` field in the response
body for details. The `/check` endpoint additionally returns a JSON report of all
findings discovered during the documentation scan.
