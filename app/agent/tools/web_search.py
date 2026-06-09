from __future__ import annotations

import asyncio
import textwrap
from typing import Any

from google.genai import types
from tavily import TavilyClient

from app.agent.tools.base import Tool, ToolResult


class WebSearchTool(Tool):
    name = "web_search"
    description = (
        "Search the web for current information, news, facts, or recent events. "
        "Use this for anything that requires up-to-date or real-world knowledge."
    )

    def __init__(self, tavily_api_key: str) -> None:
        self._client = TavilyClient(api_key=tavily_api_key)

    async def run(self, **kwargs: Any) -> ToolResult:
        query = str(kwargs.get("query", "")).strip()
        if not query:
            return ToolResult(success=False, output="", error="query is required")
        try:
            response = await asyncio.to_thread(
                self._client.search, query=query, max_results=5
            )
            results = response.get("results", [])
            if not results:
                return ToolResult(success=True, output="No results found.")
            lines: list[str] = []
            for i, r in enumerate(results, 1):
                lines.append(f"{i}. {r.get('title', 'No title')}")
                lines.append(f"   URL: {r.get('url', '')}")
                content = r.get("content", "")
                if content:
                    lines.append(f"   {textwrap.shorten(content, width=300)}")
            return ToolResult(success=True, output="\n".join(lines))
        except Exception as exc:
            return ToolResult(success=False, output="", error=f"Search failed: {exc}")

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
