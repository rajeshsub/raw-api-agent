# ADR-0002: POST method for SSE streaming endpoint

**Status:** Accepted

## Context

Server-Sent Events (SSE) are traditionally consumed via the browser's `EventSource` API, which only supports GET requests. The streaming endpoint needs to accept a `goal` parameter, which could be placed in a query string for a GET request or in a request body for a POST request.

## Decision

Use `POST /agent/stream` with the goal in the JSON request body, not `GET /agent/stream?goal=...`.

## Rationale

GET query parameters have practical length limits (typically 2000–8000 characters depending on browser and proxy). A goal like "Research all regulatory filings from 2024 for these 10 companies and write a comparative analysis" could approach or exceed this limit as goals grow more complex.

POST with a JSON body has no such constraint and is consistent with the `POST /agent/run` endpoint, giving both endpoints the same request shape `{"goal": "..."}`.

## Consequences

Browser clients cannot use the native `EventSource` API (which only supports GET). Clients must use `fetch` with response body streaming instead. This is well-supported in modern browsers and Node.js. Example client code is provided in the README.
