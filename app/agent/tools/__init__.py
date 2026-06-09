from __future__ import annotations

from pathlib import Path

from app.agent.tools.base import Tool, ToolResult
from app.agent.tools.calculator import CalculatorTool
from app.agent.tools.file_ops import FileReadTool, FileWriteTool
from app.agent.tools.web_search import WebSearchTool

__all__ = [
    "Tool",
    "ToolResult",
    "FileReadTool",
    "FileWriteTool",
    "CalculatorTool",
    "WebSearchTool",
    "build_tool_registry",
]


def build_tool_registry(workspace: Path, tavily_api_key: str) -> dict[str, Tool]:
    tools: list[Tool] = [
        FileReadTool(workspace=workspace),
        FileWriteTool(workspace=workspace),
        CalculatorTool(),
        WebSearchTool(tavily_api_key=tavily_api_key),
    ]
    return {t.name: t for t in tools}
