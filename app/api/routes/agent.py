from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from app.agent import loop
from app.agent.schemas import AgentResult, GoalRequest
from app.agent.tools.file_ops import ToolSecurityError
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
    return await loop.run(
        goal=body.goal,
        enabled_tools=body.enabled_tools or None,
        settings=settings,
        gemini=gemini,
    )


@router.post("/stream")
async def stream_agent(
    body: GoalRequest,
    _: Annotated[None, Depends(verify_api_key)],
    settings: Annotated[Settings, Depends(get_settings)],
    gemini: Annotated[GeminiClient, Depends(get_gemini_client)],
) -> StreamingResponse:
    event_stream = loop.stream(
        goal=body.goal,
        enabled_tools=body.enabled_tools or None,
        settings=settings,
        gemini=gemini,
    )

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


@router.get("/workspace/{file_path:path}")
async def download_workspace_file(
    file_path: str,
    _: Annotated[None, Depends(verify_api_key)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> FileResponse:
    workspace = settings.agent_workspace.resolve()
    try:
        resolved = (workspace / file_path).resolve()
        if not resolved.is_relative_to(workspace):
            raise ToolSecurityError("path traversal rejected")
    except ToolSecurityError as exc:
        raise HTTPException(status_code=400, detail="Invalid file path") from exc

    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=resolved,
        filename=resolved.name,
        media_type="application/octet-stream",
    )
