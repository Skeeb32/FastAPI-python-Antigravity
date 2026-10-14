"""
Application configuration settings.
"""

from typing import List
from pydantic import BaseModel, Field


class Settings(BaseModel):
    PROJECT_NAME: str = "FastAPI-python-Antigravity"
    PROJECT_DESCRIPTION: str = (
        "Enterprise-grade FastAPI backend service and Python data processing engine "
        "showcasing Pydantic request body validation, statistical telemetry pipelines, "
        "and decoupled data transformation services."
    )
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])


settings = Settings()
