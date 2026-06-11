from __future__ import annotations

from pathlib import Path
from typing import Any

from google.genai import types

from app.agent.tools.base import Tool, ToolResult


class ToolSecurityError(Exception):
    pass


class _FileToolBase(Tool):
    def __init__(self, workspace: Path) -> None:
        self._workspace = workspace.resolve()

    def _safe_path(self, relative: str) -> Path:
        resolved = (self._workspace / relative).resolve()
        if not resolved.is_relative_to(self._workspace):
            raise ToolSecurityError(f"Path traversal rejected: {relative!r}")
        return resolved


class FileWriteTool(_FileToolBase):
    name = "file_write"
    description = (
        "Write content to a file in the workspace. "
        "Creates parent directories if they do not exist."
    )

    async def run(self, **kwargs: Any) -> ToolResult:
        path_str = str(kwargs.get("path", "")).strip()
        content = str(kwargs.get("content", ""))
        if not path_str:
            return ToolResult(success=False, output="", error="path is required")

        try:
            safe = self._safe_path(path_str)
            safe.parent.mkdir(parents=True, exist_ok=True)
            safe.write_text(content, encoding="utf-8")
            byte_count = len(content.encode("utf-8"))
            return ToolResult(
                success=True,
                output=f"Written {byte_count} bytes to {path_str}",
            )
        except ToolSecurityError as exc:
            return ToolResult(success=False, output="", error=str(exc))
        except Exception as exc:
            return ToolResult(success=False, output="", error=str(exc))

    def declaration(self) -> types.FunctionDeclaration:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "path": types.Schema(
                        type=types.Type.STRING,
                        description="Relative path from workspace root.",
                    ),
                    "content": types.Schema(
                        type=types.Type.STRING,
                        description="Full content to write to the file.",
                    ),
                },
                required=["path", "content"],
            ),
        )
