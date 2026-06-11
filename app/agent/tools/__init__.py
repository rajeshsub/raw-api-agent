from __future__ import annotations

from pathlib import Path

from app.agent.tools.base import Tool, ToolResult
from app.agent.tools.calculator import CalculatorTool
from app.agent.tools.file_ops import FileWriteTool
from app.agent.tools.web_search import WebSearchTool

__all__ = [
    "Tool",
    "ToolResult",
    "FileWriteTool",
    "CalculatorTool",
    "WebSearchTool",
    "build_tool_registry",
]


def build_tool_registry(
    workspace: Path,
    tavily_api_key: str,
    enabled_tools: list[str] | None = None,
) -> dict[str, Tool]:
    all_tools: list[Tool] = [
        FileWriteTool(workspace=workspace),
        CalculatorTool(),
        WebSearchTool(tavily_api_key=tavily_api_key),
    ]
    if enabled_tools is not None:
        all_tools = [t for t in all_tools if t.name in enabled_tools]
    return {t.name: t for t in all_tools}
