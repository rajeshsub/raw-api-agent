from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.agent import loop
from app.agent.schemas import AgentResult, GoalRequest
from app.api.deps import verify_api_key
from app.core.config import Settings, get_settings
from app.core.gemini import GeminiClient, get_gemini_client

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/run", response_model=AgentResult)
async def run_agent(
    body: GoalRequest,
    _: Annotated[None, Depends(verify_api_key)],
    settings: Annotated[Settings, Depends(get_settings)],
    gemini: Annotated[GeminiClient, Depends(get_gemini_client)],
) -> AgentResult:
    return await loop.run(goal=body.goal, settings=settings, gemini=gemini)


@router.post("/stream")
async def stream_agent(
    body: GoalRequest,
    _: Annotated[None, Depends(verify_api_key)],
    settings: Annotated[Settings, Depends(get_settings)],
    gemini: Annotated[GeminiClient, Depends(get_gemini_client)],
) -> StreamingResponse:
    event_stream = loop.stream(goal=body.goal, settings=settings, gemini=gemini)

    async def generate() -> AsyncGenerator[str]:
        async for event in event_stream:
            yield f"event: {event.type}\ndata: {event.model_dump_json()}\n\n"

    return StreamingResponse(
        content=generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
