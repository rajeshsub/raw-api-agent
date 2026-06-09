from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.gemini import FunctionCallInfo, GeminiClient, GeminiResponse

TEST_API_KEY = "test-api-key-secret"


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "workspace"
    ws.mkdir()
    return ws


@pytest.fixture
def settings(workspace: Path) -> Settings:
    return Settings(
        gemini_api_key="test-gemini-key",
        api_key=TEST_API_KEY,
        tavily_api_key="test-tavily-key",
        agent_workspace=workspace,
        max_agent_iterations=5,
    )


@pytest.fixture
def mock_gemini_final() -> GeminiClient:
    client: GeminiClient = MagicMock(spec=GeminiClient)
    client.generate = AsyncMock(  # type: ignore[method-assign]
        return_value=GeminiResponse(
            text="Final answer from agent.",
            function_calls=[],
            model_content=None,
        )
    )
    return client


@pytest.fixture
def mock_gemini_tool_then_final(workspace: Path) -> GeminiClient:
    from google.genai import types

    tool_response = GeminiResponse(
        text=None,
        function_calls=[
            FunctionCallInfo(name="calculate", args={"expression": "2 + 2"})
        ],
        model_content=types.Content(role="model", parts=[]),
    )
    final_response = GeminiResponse(
        text="The answer is 4.",
        function_calls=[],
        model_content=None,
    )
    client: GeminiClient = MagicMock(spec=GeminiClient)
    client.generate = AsyncMock(side_effect=[tool_response, final_response])  # type: ignore[method-assign]
    return client


@pytest.fixture
def mock_gemini_max_iter() -> GeminiClient:
    from google.genai import types

    always_tool = GeminiResponse(
        text=None,
        function_calls=[
            FunctionCallInfo(name="calculate", args={"expression": "1 + 1"})
        ],
        model_content=types.Content(role="model", parts=[]),
    )
    client: GeminiClient = MagicMock(spec=GeminiClient)
    client.generate = AsyncMock(return_value=always_tool)  # type: ignore[method-assign]
    return client


@pytest.fixture
def test_client(
    settings: Settings, mock_gemini_final: GeminiClient
) -> Generator[TestClient]:
    from app.core.config import get_settings
    from app.core.gemini import get_gemini_client
    from app.main import create_app

    application = create_app()
    application.dependency_overrides[get_settings] = lambda: settings
    application.dependency_overrides[get_gemini_client] = lambda: mock_gemini_final
    with (
        patch("app.main.get_settings", return_value=settings),
        TestClient(application) as client,
    ):
        yield client
    application.dependency_overrides.clear()
