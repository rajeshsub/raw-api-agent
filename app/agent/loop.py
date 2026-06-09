from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import structlog
from google.genai import types

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.schemas import AgentResult, SSEEvent, Step
from app.agent.tools import build_tool_registry
from app.core.config import Settings, get_settings
from app.core.gemini import GeminiClient, get_gemini_client
from app.core.logging import bind_correlation_id

logger = structlog.get_logger(__name__)


def _tool_results_content(results: list[tuple[str, str]]) -> types.Content:
    return types.Content(
        role="user",
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    name=name,
                    response={"result": result},
                )
            )
            for name, result in results
        ],
    )


async def run(
    goal: str,
    settings: Settings | None = None,
    gemini: GeminiClient | None = None,
) -> AgentResult:
    correlation_id = str(uuid.uuid4())
    with bind_correlation_id(correlation_id):
        return await _run_loop(
            goal=goal,
            settings=settings or get_settings(),
            gemini=gemini or get_gemini_client(),
        )


def stream(
    goal: str,
    settings: Settings | None = None,
    gemini: GeminiClient | None = None,
) -> AsyncGenerator[SSEEvent]:
    correlation_id = str(uuid.uuid4())
    return _stream_loop(
        goal=goal,
        correlation_id=correlation_id,
        settings=settings or get_settings(),
        gemini=gemini or get_gemini_client(),
    )


async def _run_loop(
    goal: str,
    settings: Settings,
    gemini: GeminiClient,
) -> AgentResult:
    tool_map = build_tool_registry(
        workspace=settings.agent_workspace, tavily_api_key=settings.tavily_api_key
    )
    declarations = [t.declaration() for t in tool_map.values()]
    messages: list[types.Content] = [
        types.Content(role="user", parts=[types.Part(text=goal)])
    ]
    steps: list[Step] = []

    for iteration in range(settings.max_agent_iterations):
        logger.info("agent_iteration", iteration=iteration)
        response = await gemini.generate(
            messages=messages,
            tool_declarations=declarations,
            system_instruction=SYSTEM_PROMPT,
        )

        if response.thoughts:
            logger.info("agent_thinking", length=len(response.thoughts))
        if response.is_final:
            logger.info("agent_complete", steps=len(steps))
            return AgentResult(answer=response.text, steps=steps, partial=False)

        tool_results: list[tuple[str, str]] = []
        for fn_call in response.function_calls:
            logger.info("tool_dispatch", tool=fn_call.name)
            tool = tool_map.get(fn_call.name)
            if tool is None:
                result_str = f"Error: unknown tool '{fn_call.name}'"
            else:
                tool_result = await tool.run(**fn_call.args)
                result_str = (
                    tool_result.output
                    if tool_result.success
                    else (tool_result.error or "unknown error")
                )
            steps.append(Step(tool=fn_call.name, args=fn_call.args, result=result_str))
            tool_results.append((fn_call.name, result_str))

        if response.model_content is not None:
            messages.append(response.model_content)
        messages.append(_tool_results_content(tool_results))

    logger.warning("max_iterations_reached", max=settings.max_agent_iterations)
    return AgentResult(
        answer=None,
        steps=steps,
        partial=True,
        error="max_iterations_reached",
    )


async def _stream_loop(
    goal: str,
    correlation_id: str,
    settings: Settings,
    gemini: GeminiClient,
) -> AsyncGenerator[SSEEvent]:
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
    try:
        tool_map = build_tool_registry(
            workspace=settings.agent_workspace, tavily_api_key=settings.tavily_api_key
        )
        declarations = [t.declaration() for t in tool_map.values()]
        messages: list[types.Content] = [
            types.Content(role="user", parts=[types.Part(text=goal)])
        ]

        for iteration in range(settings.max_agent_iterations):
            response = await gemini.generate(
                messages=messages,
                tool_declarations=declarations,
                system_instruction=SYSTEM_PROMPT,
            )

            yield SSEEvent(
                type="thinking",
                message=response.thoughts
                or f"Iteration {iteration + 1}: reasoning about next step...",
            )

            if response.is_final:
                yield SSEEvent(type="answer", content=response.text)
                return

            tool_results: list[tuple[str, str]] = []
            for fn_call in response.function_calls:
                yield SSEEvent(type="tool_call", tool=fn_call.name, args=fn_call.args)

                tool = tool_map.get(fn_call.name)
                if tool is None:
                    result_str = f"Error: unknown tool '{fn_call.name}'"
                else:
                    tool_result = await tool.run(**fn_call.args)
                    result_str = (
                        tool_result.output
                        if tool_result.success
                        else (tool_result.error or "unknown error")
                    )

                tool_results.append((fn_call.name, result_str))
                yield SSEEvent(type="tool_result", tool=fn_call.name, result=result_str)

            if response.model_content is not None:
                messages.append(response.model_content)
            messages.append(_tool_results_content(tool_results))

        yield SSEEvent(type="error", message="max_iterations_reached")
    finally:
        structlog.contextvars.unbind_contextvars("correlation_id")
