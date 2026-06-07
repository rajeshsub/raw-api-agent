from __future__ import annotations

import math
from typing import Any

from google.genai import types
from simpleeval import simple_eval

from app.agent.tools.base import Tool, ToolResult

_FUNCTIONS: dict[str, Any] = {
    "sqrt": math.sqrt,
    "abs": abs,
    "round": round,
    "int": int,
    "float": float,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "ceil": math.ceil,
    "floor": math.floor,
}

_NAMES: dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
}


class CalculatorTool(Tool):
    name = "calculate"
    description = (
        "Evaluate a mathematical expression safely. "
        "Supports arithmetic, sqrt, trig, log, abs, round, pi, e. "
        "Example: '150 * 1.1' or 'sqrt(144)' or 'sin(pi/2)'."
    )

    async def run(self, **kwargs: Any) -> ToolResult:
        expression = str(kwargs.get("expression", "")).strip()
        if not expression:
            return ToolResult(success=False, output="", error="expression is required")

        try:
            result = simple_eval(
                expression,
                functions=_FUNCTIONS,
                names=_NAMES,
            )
            return ToolResult(success=True, output=str(result))
        except Exception as exc:
            return ToolResult(
                success=False, output="", error=f"Evaluation failed: {exc}"
            )

    def declaration(self) -> types.FunctionDeclaration:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "expression": types.Schema(
                        type=types.Type.STRING,
                        description=(
                            "Math expression to evaluate. "
                            "E.g. '150 * 1.1', 'sqrt(144)', 'sin(pi/2)'."
                        ),
                    )
                },
                required=["expression"],
            ),
        )
