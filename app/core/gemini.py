from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog
from google import genai
from google.genai import types

logger = structlog.get_logger(__name__)


@dataclass
class FunctionCallInfo:
    name: str
    args: dict[str, Any]


@dataclass
class GeminiResponse:
    text: str | None
    function_calls: list[FunctionCallInfo] = field(default_factory=list)
    model_content: types.Content | None = None
    thoughts: str | None = None

    @property
    def is_final(self) -> bool:
        return len(self.function_calls) == 0


class GeminiClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def generate(
        self,
        messages: list[types.Content],
        tool_declarations: list[types.FunctionDeclaration],
        system_instruction: str,
    ) -> GeminiResponse:
        tools: list[Any] = (
            [types.Tool(function_declarations=tool_declarations)]
            if tool_declarations
            else []
        )
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=tools or None,
            temperature=0.1,
            thinking_config=types.ThinkingConfig(include_thoughts=True),
        )

        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=messages,
            config=config,
        )

        function_calls: list[FunctionCallInfo] = []
        text: str | None = None
        thoughts: str | None = None
        model_content: types.Content | None = None

        candidates = response.candidates
        if not candidates:
            return GeminiResponse(text=None)

        candidate = candidates[0]
        raw_content = candidate.content
        if not raw_content or not raw_content.parts:
            return GeminiResponse(text=None)

        model_content = raw_content

        for part in raw_content.parts:
            if getattr(part, "thought", False):
                thoughts = (thoughts or "") + (part.text or "")
            elif part.function_call is not None:
                fn = part.function_call
                function_calls.append(
                    FunctionCallInfo(
                        name=fn.name or "",
                        args=dict(fn.args) if fn.args else {},
                    )
                )
            elif part.text is not None:
                text = (text or "") + part.text

        return GeminiResponse(
            text=text,
            function_calls=function_calls,
            model_content=model_content,
            thoughts=thoughts,
        )

    async def search(self, query: str) -> str:
        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.1,
        )
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=[types.Content(role="user", parts=[types.Part(text=query)])],
            config=config,
        )
        candidates = response.candidates
        if not candidates:
            return "No results found."
        raw_content = candidates[0].content
        if not raw_content or not raw_content.parts:
            return "No results found."
        text = ""
        for part in raw_content.parts:
            if part.text:
                text += part.text
        return text or "No results found."


def get_gemini_client() -> GeminiClient:
    from app.core.config import get_settings

    settings = get_settings()
    return GeminiClient(api_key=settings.gemini_api_key, model=settings.gemini_model)
