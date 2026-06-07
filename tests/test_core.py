from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.gemini import GeminiClient

# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------


def test_get_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import get_settings

    monkeypatch.setenv("GEMINI_API_KEY", "key-abc")
    monkeypatch.setenv("API_KEY", "api-xyz")
    get_settings.cache_clear()
    try:
        s = get_settings()
        assert s.gemini_api_key == "key-abc"
        assert s.api_key == "api-xyz"
        assert s.gemini_model == "gemini-2.5-flash"
    finally:
        get_settings.cache_clear()


# ---------------------------------------------------------------------------
# logging
# ---------------------------------------------------------------------------


def test_get_logger() -> None:
    from app.core.logging import get_logger

    logger = get_logger("test.module")
    assert logger is not None


# ---------------------------------------------------------------------------
# GeminiClient — init
# ---------------------------------------------------------------------------


def test_gemini_client_init() -> None:
    with patch("google.genai.Client") as mock_cls:
        client = GeminiClient(api_key="my-key", model="my-model")
    mock_cls.assert_called_once_with(api_key="my-key")
    assert client._model == "my-model"


# ---------------------------------------------------------------------------
# GeminiClient.generate helpers
# ---------------------------------------------------------------------------


def _make_client() -> tuple[GeminiClient, MagicMock]:
    with patch("google.genai.Client") as mock_cls:
        inner: MagicMock = MagicMock()
        mock_cls.return_value = inner
        client = GeminiClient(api_key="k", model="m")
    return client, inner


# ---------------------------------------------------------------------------
# GeminiClient.generate — no candidates
# ---------------------------------------------------------------------------


async def test_generate_no_candidates() -> None:
    client, inner = _make_client()
    resp = MagicMock()
    resp.candidates = []
    inner.aio.models.generate_content = AsyncMock(return_value=resp)

    result = await client.generate(
        messages=[], tool_declarations=[], system_instruction="s"
    )
    assert result.text is None
    assert result.function_calls == []


# ---------------------------------------------------------------------------
# GeminiClient.generate — candidate with no content
# ---------------------------------------------------------------------------


async def test_generate_no_content() -> None:
    client, inner = _make_client()
    candidate = MagicMock()
    candidate.content = None
    resp = MagicMock()
    resp.candidates = [candidate]
    inner.aio.models.generate_content = AsyncMock(return_value=resp)

    result = await client.generate(
        messages=[], tool_declarations=[], system_instruction="s"
    )
    assert result.text is None


# ---------------------------------------------------------------------------
# GeminiClient.generate — candidate with empty parts list
# ---------------------------------------------------------------------------


async def test_generate_no_parts() -> None:
    client, inner = _make_client()
    content = MagicMock()
    content.parts = []
    candidate = MagicMock()
    candidate.content = content
    resp = MagicMock()
    resp.candidates = [candidate]
    inner.aio.models.generate_content = AsyncMock(return_value=resp)

    result = await client.generate(
        messages=[], tool_declarations=[], system_instruction="s"
    )
    assert result.text is None


# ---------------------------------------------------------------------------
# GeminiClient.generate — text response
# ---------------------------------------------------------------------------


async def test_generate_text_response() -> None:
    client, inner = _make_client()
    part = MagicMock()
    part.thought = False
    part.function_call = None
    part.text = "hello world"
    content = MagicMock()
    content.parts = [part]
    candidate = MagicMock()
    candidate.content = content
    resp = MagicMock()
    resp.candidates = [candidate]
    inner.aio.models.generate_content = AsyncMock(return_value=resp)

    result = await client.generate(
        messages=[], tool_declarations=[], system_instruction="s"
    )
    assert result.text == "hello world"
    assert result.function_calls == []
    assert result.model_content is content
    assert result.is_final is True


# ---------------------------------------------------------------------------
# GeminiClient.generate — function call response
# ---------------------------------------------------------------------------


async def test_generate_function_call_response() -> None:
    client, inner = _make_client()
    fn = MagicMock()
    fn.name = "calculate"
    fn.args = {"expression": "1+1"}
    part = MagicMock()
    part.thought = False
    part.function_call = fn
    part.text = None
    content = MagicMock()
    content.parts = [part]
    candidate = MagicMock()
    candidate.content = content
    resp = MagicMock()
    resp.candidates = [candidate]
    inner.aio.models.generate_content = AsyncMock(return_value=resp)

    from google.genai import types

    result = await client.generate(
        messages=[],
        tool_declarations=[MagicMock(spec=types.FunctionDeclaration)],
        system_instruction="s",
    )
    assert len(result.function_calls) == 1
    assert result.function_calls[0].name == "calculate"
    assert result.function_calls[0].args == {"expression": "1+1"}
    assert result.is_final is False


# ---------------------------------------------------------------------------
# GeminiClient.generate — thought parts surfaced in response.thoughts
# ---------------------------------------------------------------------------


async def test_generate_thought_parts() -> None:
    client, inner = _make_client()
    thought_part = MagicMock()
    thought_part.thought = True
    thought_part.text = "I should calculate this."
    thought_part.function_call = None
    text_part = MagicMock()
    text_part.thought = False
    text_part.function_call = None
    text_part.text = "The answer is 42."
    content = MagicMock()
    content.parts = [thought_part, text_part]
    candidate = MagicMock()
    candidate.content = content
    resp = MagicMock()
    resp.candidates = [candidate]
    inner.aio.models.generate_content = AsyncMock(return_value=resp)

    result = await client.generate(
        messages=[], tool_declarations=[], system_instruction="s"
    )
    assert result.thoughts == "I should calculate this."
    assert result.text == "The answer is 42."


# ---------------------------------------------------------------------------
# GeminiClient.generate — no tool_declarations passes tools=None to config
# ---------------------------------------------------------------------------


async def test_generate_empty_tool_declarations() -> None:
    client, inner = _make_client()
    part = MagicMock()
    part.thought = False
    part.function_call = None
    part.text = "answer"
    content = MagicMock()
    content.parts = [part]
    candidate = MagicMock()
    candidate.content = content
    resp = MagicMock()
    resp.candidates = [candidate]
    inner.aio.models.generate_content = AsyncMock(return_value=resp)

    result = await client.generate(
        messages=[], tool_declarations=[], system_instruction="s"
    )
    assert result.text == "answer"
    _, call_kwargs = inner.aio.models.generate_content.call_args
    assert call_kwargs["config"].tools is None


# ---------------------------------------------------------------------------
# GeminiClient.search
# ---------------------------------------------------------------------------


async def test_search_returns_text() -> None:
    client, inner = _make_client()
    part = MagicMock()
    part.text = "Top news today: cricket."
    content = MagicMock()
    content.parts = [part]
    candidate = MagicMock()
    candidate.content = content
    resp = MagicMock()
    resp.candidates = [candidate]
    inner.aio.models.generate_content = AsyncMock(return_value=resp)

    result = await client.search("India news today")
    assert "cricket" in result


async def test_search_no_candidates() -> None:
    client, inner = _make_client()
    resp = MagicMock()
    resp.candidates = []
    inner.aio.models.generate_content = AsyncMock(return_value=resp)

    result = await client.search("something")
    assert result == "No results found."


async def test_search_no_content() -> None:
    client, inner = _make_client()
    candidate = MagicMock()
    candidate.content = None
    resp = MagicMock()
    resp.candidates = [candidate]
    inner.aio.models.generate_content = AsyncMock(return_value=resp)

    result = await client.search("something")
    assert result == "No results found."


async def test_search_empty_parts() -> None:
    client, inner = _make_client()
    content = MagicMock()
    content.parts = []
    candidate = MagicMock()
    candidate.content = content
    resp = MagicMock()
    resp.candidates = [candidate]
    inner.aio.models.generate_content = AsyncMock(return_value=resp)

    result = await client.search("something")
    assert result == "No results found."


async def test_search_no_text_in_parts() -> None:
    client, inner = _make_client()
    part = MagicMock()
    part.text = None
    content = MagicMock()
    content.parts = [part]
    candidate = MagicMock()
    candidate.content = content
    resp = MagicMock()
    resp.candidates = [candidate]
    inner.aio.models.generate_content = AsyncMock(return_value=resp)

    result = await client.search("something")
    assert result == "No results found."


# ---------------------------------------------------------------------------
# get_gemini_client
# ---------------------------------------------------------------------------


def test_get_gemini_client() -> None:
    from app.core.config import Settings
    from app.core.gemini import get_gemini_client

    settings = Settings(gemini_api_key="gk", api_key="ak")
    with (
        patch("app.core.config.get_settings", return_value=settings),
        patch("google.genai.Client"),
    ):
        client = get_gemini_client()
    assert isinstance(client, GeminiClient)
    assert client._model == settings.gemini_model
