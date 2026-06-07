from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from app.agent.tools.base import Tool, ToolResult
from app.agent.tools.calculator import CalculatorTool
from app.agent.tools.file_ops import FileReadTool, FileWriteTool
from app.agent.tools.web_search import WebSearchTool

if TYPE_CHECKING:
    from app.core.gemini import GeminiClient

__all__ = [
    "Tool",
    "ToolResult",
    "FileReadTool",
    "FileWriteTool",
    "CalculatorTool",
    "WebSearchTool",
    "build_tool_registry",
]


def build_tool_registry(workspace: Path, gemini: GeminiClient) -> dict[str, Tool]:
    tools: list[Tool] = [
        FileReadTool(workspace=workspace),
        FileWriteTool(workspace=workspace),
        CalculatorTool(),
        WebSearchTool(gemini=gemini),
    ]
    return {t.name: t for t in tools}
