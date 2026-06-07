from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import agent, health, ui
from app.core.config import get_settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="raw-api-agent",
        description="Goal-driven AI agent using raw Gemini function calling — no frameworks.",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.include_router(ui.router)
    application.include_router(health.router)
    application.include_router(agent.router)
    return application


app = create_app()
