# Endpoints

This page is listed under `{"Endpoints" = "api/endpoints.md"}` in the nav section.

## `GET /status`

Returns the service health status.

In this fixture, the endpoint payload is intentionally simple because the goal
is not API complexity but documentation consistency: valid JSON snippets,
portable relative links, and enough narrative content to pass quality checks
without introducing artificial boilerplate. The same pattern can be extended to
real endpoints with authentication, pagination, and versioning sections.

**Response:**

```json
{"status": "ok", "version": "1.0.0"}
```

Back to [API Reference](index.md) or the [home page](../index.md).
