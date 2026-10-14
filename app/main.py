"""
Main application module for FastAPI-python-Antigravity.
Configures FastAPI app, CORS middleware, custom exception handlers, and mounts API routers.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.routers import (
    datasets_router,
    health_router,
    orders_router,
    telemetry_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifecycle manager for startup and shutdown hooks.
    """
    # Startup tasks
    print(f"[{settings.PROJECT_NAME}] Starting up backend services and data processing engines...")
    yield
    # Shutdown tasks
    print(f"[{settings.PROJECT_NAME}] Gracefully shutting down...")


def create_application() -> FastAPI:
    """
    Application factory pattern.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom 422 Validation Error Handler with serializable context formatting
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Convert any non-serializable objects (such as Exception instances in ctx) to strings
        safe_errors = []
        for err in exc.errors():
            item = dict(err)
            if "ctx" in item and isinstance(item["ctx"], dict):
                item["ctx"] = {k: str(v) for k, v in item["ctx"].items()}
            safe_errors.append(item)

        return JSONResponse(
            status_code=422,
            content={
                "status": "failed",
                "message": "Pydantic Request Body validation failed. Check schema fields and types.",
                "errors": safe_errors,
            },
        )

    # Mount routers at root and API v1 prefix
    app.include_router(health_router)
    app.include_router(health_router, prefix=settings.API_V1_STR)
    app.include_router(telemetry_router, prefix=settings.API_V1_STR)
    app.include_router(orders_router, prefix=settings.API_V1_STR)
    app.include_router(datasets_router, prefix=settings.API_V1_STR)

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "status": "running",
            "health_check": "/healthz",
            "architecture_info": f"{settings.API_V1_STR}/system/info",
        }

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
