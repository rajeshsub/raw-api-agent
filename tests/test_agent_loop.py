from __future__ import annotations

from pathlib import Path

from app.agent import loop
from app.agent.schemas import AgentResult
from app.core.config import Settings
from app.core.gemini import GeminiClient


async def test_run_logs_thoughts(settings: Settings) -> None:
    from unittest.mock import AsyncMock, MagicMock

    from app.core.gemini import GeminiClient, GeminiResponse

    mock: GeminiClient = MagicMock(spec=GeminiClient)
    mock.generate = AsyncMock(  # type: ignore[method-assign]
        return_value=GeminiResponse(
            text="Done.", function_calls=[], thoughts="Let me think about this."
        )
    )
    result = await loop.run(goal="test", settings=settings, gemini=mock)
    assert result.answer == "Done."


async def test_run_final_answer(
    settings: Settings, mock_gemini_final: GeminiClient
) -> None:
    result = await loop.run(
        goal="test goal", settings=settings, gemini=mock_gemini_final
    )
    assert isinstance(result, AgentResult)
    assert result.answer == "Final answer from agent."
    assert result.partial is False
    assert result.steps == []


async def test_run_tool_then_final(
    settings: Settings,
    mock_gemini_tool_then_final: GeminiClient,
    workspace: Path,
) -> None:
    result = await loop.run(
        goal="calculate 2+2",
        settings=settings,
        gemini=mock_gemini_tool_then_final,
    )
    assert isinstance(result, AgentResult)
    assert result.partial is False
    assert len(result.steps) == 1
    assert result.steps[0].tool == "calculate"
    assert result.steps[0].args == {"expression": "2 + 2"}
    assert result.steps[0].result == "4"


async def test_run_max_iterations(
    settings: Settings, mock_gemini_max_iter: GeminiClient
) -> None:
    result = await loop.run(
        goal="loop forever", settings=settings, gemini=mock_gemini_max_iter
    )
    assert result.partial is True
    assert result.error == "max_iterations_reached"
    assert result.answer is None
    assert len(result.steps) == settings.max_agent_iterations


async def test_stream_emits_events(
    settings: Settings, mock_gemini_tool_then_final: GeminiClient
) -> None:
    events = []
    gen = loop.stream(
        goal="stream test", settings=settings, gemini=mock_gemini_tool_then_final
    )
    async for event in gen:
        events.append(event)

    types_seen = [e.type for e in events]
    assert "thinking" in types_seen
    assert "tool_call" in types_seen
    assert "tool_result" in types_seen
    assert "answer" in types_seen


async def test_stream_max_iterations(
    settings: Settings, mock_gemini_max_iter: GeminiClient
) -> None:
    events = []
    async for event in loop.stream(
        goal="loop forever", settings=settings, gemini=mock_gemini_max_iter
    ):
        events.append(event)

    last = events[-1]
    assert last.type == "error"
    assert last.message == "max_iterations_reached"


async def test_stream_unknown_tool(settings: Settings) -> None:
    from unittest.mock import AsyncMock, MagicMock

    from google.genai import types

    from app.core.gemini import FunctionCallInfo, GeminiClient, GeminiResponse

    unknown = GeminiResponse(
        text=None,
        function_calls=[FunctionCallInfo(name="nonexistent_tool", args={})],
        model_content=types.Content(role="model", parts=[]),
    )
    final = GeminiResponse(text="Done.", function_calls=[], model_content=None)
    mock: GeminiClient = MagicMock(spec=GeminiClient)
    mock.generate = AsyncMock(side_effect=[unknown, final])  # type: ignore[method-assign]

    events = []
    async for event in loop.stream(goal="test", settings=settings, gemini=mock):
        events.append(event)

    tool_results = [e for e in events if e.type == "tool_result"]
    assert any("Error: unknown tool" in (e.result or "") for e in tool_results)


async def test_run_unknown_tool(settings: Settings) -> None:
    from unittest.mock import AsyncMock, MagicMock

    from google.genai import types

    from app.core.gemini import FunctionCallInfo, GeminiClient, GeminiResponse

    unknown_tool_response = GeminiResponse(
        text=None,
        function_calls=[FunctionCallInfo(name="nonexistent_tool", args={})],
        model_content=types.Content(role="model", parts=[]),
    )
    final_response = GeminiResponse(text="Done.", function_calls=[], model_content=None)
    mock: GeminiClient = MagicMock(spec=GeminiClient)
    mock.generate = AsyncMock(side_effect=[unknown_tool_response, final_response])  # type: ignore[method-assign]

    result = await loop.run(goal="test", settings=settings, gemini=mock)
    assert result.steps[0].result.startswith("Error: unknown tool")
