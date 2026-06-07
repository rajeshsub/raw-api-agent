# ADR-0003: google-genai SDK over google-generativeai

**Status:** Accepted

## Context

Google maintains two Python SDKs for Gemini:
- `google-generativeai` — original SDK, now in maintenance mode
- `google-genai` — new unified SDK, actively developed

## Decision

Use `google-genai` (the new unified SDK).

## Rationale

`google-generativeai` is in maintenance mode as of 2025. The new `google-genai` SDK provides:
- Proper async support via `client.aio.models.*`
- Full support for Gemini 2.x and 2.5 models
- Better type annotations
- Unified API for both Gemini Developer API and Vertex AI

Using a maintenance-mode library creates risk of broken compatibility with newer Gemini models and features.

## Consequences

Import path changes: `from google import genai` and `from google.genai import types`. The API surface differs from `google-generativeai` — developers familiar with the old SDK need to learn the new one. Breaking changes between `google-genai` versions are possible but the library is now the official Google-recommended path.
