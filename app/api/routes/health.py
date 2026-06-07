from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    return {
        "status": "ok",
        "model": settings.gemini_model,
        "timestamp": datetime.now(tz=UTC).isoformat(),
    }
