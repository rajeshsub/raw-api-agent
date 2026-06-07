from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from google.genai import types


@dataclass
class ToolResult:
    success: bool
    output: str
    error: str | None = None


class Tool(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    async def run(self, **kwargs: Any) -> ToolResult: ...

    @abstractmethod
    def declaration(self) -> types.FunctionDeclaration: ...
