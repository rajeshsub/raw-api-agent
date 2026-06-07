# ADR-0001: Raw Gemini function calling — no LangChain

**Status:** Accepted

## Context

This project demonstrates a goal-driven AI agent with tool use. A common approach is to use LangChain or similar orchestration frameworks that abstract the function calling protocol.

## Decision

Call the Gemini API directly via `google-genai`. Build the message history, tool declarations, and function response messages manually.

## Rationale

LangChain's abstraction layer hides how function calling actually works at the API level. This project's purpose is to show depth of understanding: how `FunctionDeclaration` schemas are constructed, how the model signals a tool call via `function_call` parts in the response, how tool results are added back as `FunctionResponse` parts in the next user turn, and how the message history grows across iterations.

Using raw API also removes hidden retry logic, token management decisions, and prompt modifications that frameworks inject silently.

## Consequences

More code to write and maintain. No framework updates automatically fix breaking changes in the Gemini API. Requires understanding the message protocol to debug.
