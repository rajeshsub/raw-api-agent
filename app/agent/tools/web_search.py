from __future__ import annotations

from typing import Any

from google.genai import types

from app.agent.tools.base import Tool, ToolResult


class WebSearchTool(Tool):
    name = "web_search"
    description = (
        "Search the web for current information, news, facts, or recent events. "
        "Use this for anything that requires up-to-date or real-world knowledge."
    )

    def __init__(self, gemini: Any) -> None:
        self._gemini = gemini

    async def run(self, **kwargs: Any) -> ToolResult:
        query = str(kwargs.get("query", "")).strip()
        if not query:
            return ToolResult(success=False, output="", error="query is required")
        try:
            result = await self._gemini.search(query)
            return ToolResult(success=True, output=result)
        except Exception as exc:
            return ToolResult(success=False, output="", error=str(exc))

    def declaration(self) -> types.FunctionDeclaration:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description="Search query string.",
                    )
                },
                required=["query"],
            ),
        )
