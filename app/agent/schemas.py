from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator


class GoalRequest(BaseModel):
    goal: str
    enabled_tools: list[str] = []

    @field_validator("goal")
    @classmethod
    def goal_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("goal must not be empty")
        if len(v) > 4000:
            raise ValueError("goal must be 4000 characters or fewer")
        return v


class Step(BaseModel):
    tool: str
    args: dict[str, Any]
    result: str


class AgentResult(BaseModel):
    answer: str | None
    steps: list[Step]
    partial: bool = False
    error: str | None = None


class SSEEvent(BaseModel):
    type: str
    message: str | None = None
    tool: str | None = None
    args: dict[str, Any] | None = None
    result: str | None = None
    content: str | None = None
