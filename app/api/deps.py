from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException

from app.core.config import Settings, get_settings


async def verify_api_key(
    x_api_key: Annotated[str, Header()],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
