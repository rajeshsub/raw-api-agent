# raw-api-agent

Goal-driven AI agent built on raw Gemini function calling — no LangChain, no framework abstractions. Python 3.13 + FastAPI.

**Live demo:** [huggingface.co/spaces/rajeshsub/raw-api-agent](https://huggingface.co/spaces/rajeshsub/raw-api-agent) — every push to `main` is automatically deployed.

![raw-api-agent demo](assets/raw-api-agent-demo.gif)

## What it does

Send a natural language goal. The agent decides which tools to call, in what order, loops until done. Streams reasoning steps and final answer via Server-Sent Events.

## Why no LangChain

LangChain abstracts the function calling protocol behind convenience wrappers. This project calls the Gemini API directly to demonstrate how the tool use protocol actually works: what goes into the message history, how function call parts differ from text parts, how tool results feed back into the next model turn.

See [ADR-0001](docs/adr/0001-raw-gemini-no-langchain.md).

## Architecture

```
POST /agent/run         → runs agent loop → returns AgentResult (JSON)
POST /agent/stream      → runs agent loop → streams SSE events
GET  /health            → service status

Agent Loop:
  1. Send goal + message history to Gemini with tool declarations
  2. If STOP with text → return final answer
  3. If STOP with function_call parts → dispatch tools, append results to history
  4. Repeat up to max_iterations (default: 10)
  5. If cap reached → return partial: true + steps so far
```

## Tools

| Tool | Description |
|---|---|
| `file_read` | Read a file from workspace (sandboxed, no path traversal) |
| `file_write` | Write a file to workspace (creates parent dirs) |
| `calculate` | Evaluate math expressions safely via simpleeval (supports sqrt, trig, log) |

## SSE Event Format

```
event: thinking
data: {"type":"thinking","message":"Iteration 1: reasoning about next step..."}

event: tool_call
data: {"type":"tool_call","tool":"calculate","args":{"expression":"sqrt(2) * 100"}}

event: tool_result
data: {"type":"tool_result","tool":"calculate","result":"141.4213562373095"}

event: answer
data: {"type":"answer","content":"Python 3.13 was released on..."}
```

Stream endpoint requires `fetch` with streaming (not `EventSource` — see [ADR-0002](docs/adr/0002-post-for-sse-streaming.md)).

Example fetch client:
```javascript
const res = await fetch('/agent/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'X-API-Key': 'your-key' },
  body: JSON.stringify({ goal: 'Research Python 3.13 changes' })
});
for await (const chunk of res.body) {
  const text = new TextDecoder().decode(chunk);
  console.log(text);
}
```

## Quickstart

**Windows:**
```powershell
git clone https://github.com/rajeshsub/raw-api-agent
cd raw-api-agent
.\bootstrap.ps1
# Edit .env — add GEMINI_API_KEY and API_KEY
.venv\Scripts\uvicorn app.main:app --reload
```

**Linux/macOS:**
```bash
git clone https://github.com/rajeshsub/raw-api-agent
cd raw-api-agent
make bootstrap
# Edit .env — add GEMINI_API_KEY and API_KEY
make dev
```

## API Keys

| Key | Source |
|---|---|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com) |
| `API_KEY` | Choose any secret string — used for `X-API-Key` header auth |

## Example goals

```bash
# JSON answer
curl -X POST http://localhost:8000/agent/run \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"goal": "What is 15% of 2847?"}'

# Write to workspace
curl -X POST http://localhost:8000/agent/run \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"goal": "Calculate the compound interest on $10000 at 5% for 10 years and write the result to report.md"}'

# Stream events
curl -X POST http://localhost:8000/agent/stream \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"goal": "Calculate sqrt(2) * 100 rounded to 2 decimal places"}' \
  --no-buffer
```

## Running tests

```bash
# Linux/macOS
make test

# Windows
.venv\Scripts\pytest tests\ --cov=app --cov-fail-under=80
```

Tests are fully mocked — no real API calls, no keys needed.

## Linting

```bash
# Linux/macOS
make lint

# Windows
.venv\Scripts\ruff check app\ tests\
.venv\Scripts\black --check app\ tests\
.venv\Scripts\mypy app\ --strict
.venv\Scripts\bandit -r app\ -c pyproject.toml
```

## File security

`file_read` and `file_write` resolve all paths relative to `AGENT_WORKSPACE` and reject any path that escapes the workspace boundary (e.g. `../etc/passwd`). Uses `pathlib.Path.resolve()` + `is_relative_to()` — works cross-platform.

## Model

`gemini-2.5-flash` on paid tier — optimized for cost and tool use. Configurable via `GEMINI_MODEL` env var.
