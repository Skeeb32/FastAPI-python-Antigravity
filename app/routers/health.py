"""
Health check and diagnostic routes.
"""

from datetime import datetime, timezone
import platform
import sys
import time
from fastapi import APIRouter
from app.models.common import APIResponse, AuditMetadata, ProcessingStatus

router = APIRouter(tags=["Health & System Diagnostics"])

START_TIME = time.time()


@router.get(
    "/healthz",
    response_model=APIResponse[dict],
    summary="Service Liveness and Readiness Probe",
    description="Returns service uptime, Python environment details, and healthy operating status."
)
async def health_check() -> APIResponse[dict]:
    uptime_seconds = round(time.time() - START_TIME, 2)
    payload = {
        "status": "healthy",
        "service": "FastAPI-python-Antigravity",
        "uptime_seconds": uptime_seconds,
        "python_version": sys.version,
        "platform": platform.platform(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return APIResponse(
        status=ProcessingStatus.SUCCESS,
        message="Service is fully operational.",
        data=payload,
        metadata=AuditMetadata(execution_time_ms=0.1, processed_records_count=1)
    )


@router.get(
    "/system/info",
    response_model=APIResponse[dict],
    summary="Architecture & Service Boundary Information",
    description=(
        "Describes real production endpoints, request body schemas, and explicit separation "
        "between FastAPI HTTP transport and pure Python data processing engines."
    )
)
async def system_info() -> APIResponse[dict]:
    payload = {
        "architecture": {
            "web_framework": "FastAPI (Asynchronous ASGI transport, OpenAPI 3.1 generation, dependency injection)",
            "validation_layer": "Pydantic v2 (Strict request body parsing, nested schema constraints, field validators)",
            "data_processing_layer": "Pure Python Services (Decoupled statistical engines, transformation pipelines, financial settlement)",
        },
        "endpoints_worked_on": [
            {
                "path": "POST /api/v1/telemetry/{device_group}/process",
                "purpose": "Batch sensor metric validation, z-score outlier detection, and quantile aggregation.",
                "request_body_tutorial_ref": "Nested models, List[Model], Field validation constraints.",
            },
            {
                "path": "POST /api/v1/orders/{merchant_id}/settle",
                "purpose": "Commercial multi-line order calculation, tiered customer discounts, regional VAT, and SHA-256 audit seal.",
                "request_body_tutorial_ref": "Root Request Body with child models, Enum validation, Cross-field validators.",
            },
            {
                "path": "POST /api/v1/datasets/transform",
                "purpose": "Tabular dataset imputation, winsorizing clamps, Min-Max / Standard scaling, and column profiling.",
                "request_body_tutorial_ref": "Dynamic row-dict schemas combined with typed operational configurations.",
            },
        ],
    }
    return APIResponse(
        status=ProcessingStatus.SUCCESS,
        message="System information and architectural boundary overview.",
        data=payload
    )
