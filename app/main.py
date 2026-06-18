"""Ponto de entrada da API FastAPI. Rotas de negócio sob `/api/v1/`."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.meetings import router as meetings_router
from app.config import get_settings
from app.db import init_db
from app.observability import configure_logging

_logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    init_db()
    yield


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(meetings_router, prefix=settings.api_v1_prefix)
    app.include_router(auth_router, prefix=settings.api_v1_prefix)

    @app.exception_handler(Exception)
    async def on_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        _logger.error(
            "erro não tratado",
            extra={"component": "api", "job_id": None},
            exc_info=exc,
        )
        return JSONResponse(status_code=500, content={"detail": "erro interno"})

    @app.get("/health", tags=["infra"], summary="Healthcheck")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
