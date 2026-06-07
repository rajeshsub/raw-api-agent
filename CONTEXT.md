# Domain Glossary — raw-api-agent

**Goal**
Natural language instruction submitted by a user describing what the agent should accomplish. Bounded by reasonable length. Not empty.

**Agent Loop**
Core iteration process: send messages to the model, receive a response, dispatch any requested tools, append results, repeat until the model signals completion or the iteration cap is reached.

**Step**
One completed tool invocation within an agent run: the tool name, the arguments provided, and the result returned.

**Tool**
A named capability the agent can invoke by including a function call in its response. Each tool has a declaration (schema) registered with the model.

**AgentResult**
The final output of a completed agent run: the model's answer text, the list of steps taken, a partial flag, and an optional error message.

**Workspace**
A sandboxed local directory where the agent may read and write files. Paths outside this boundary are rejected.

**Event**
A typed message emitted during a streaming agent run. Types: `thinking`, `tool_call`, `tool_result`, `answer`, `error`.

**Correlation ID**
A UUID assigned at the start of each agent run and threaded through all structured log entries for that run, enabling full trace reconstruction.
