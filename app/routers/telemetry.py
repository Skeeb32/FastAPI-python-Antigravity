"""
Telemetry batch ingestion and statistical processing router.
Demonstrates:
- FastAPI Request Body validation with Pydantic: https://fastapi.tiangolo.com/tutorial/body/
- Path parameters + Request Body combination
- Query parameters + Request Body combination
- Error handling and structured API responses
"""

import time
from fastapi import APIRouter, HTTPException, Path, Query, status
from app.models.common import APIResponse, AuditMetadata, ProcessingStatus
from app.models.telemetry import (
    TelemetryBatchRequest,
    TelemetryProcessResponse,
)
from app.services.telemetry_processor import TelemetryProcessor

router = APIRouter(prefix="/telemetry", tags=["Telemetry Ingestion & Processing"])


@router.post(
    "/{device_group}/process",
    response_model=APIResponse[TelemetryProcessResponse],
    status_code=status.HTTP_200_OK,
    summary="Ingest & Statistically Process Sensor Batch",
    description=(
        "Ingests a batch of IoT sensor observations. Validates the request body via Pydantic models, "
        "detects statistical anomalies via Z-score evaluation, and computes distributional percentiles (p50, p95, p99)."
    )
)
async def process_telemetry_batch(
    device_group: str = Path(
        ...,
        min_length=2,
        max_length=32,
        description="Logical grouping or fleet cluster name for target device."
    ),
    dry_run: bool = Query(
        default=False,
        description="If True, validates and parses request body without committing telemetry metrics."
    ),
    payload: TelemetryBatchRequest = ...
) -> APIResponse[TelemetryProcessResponse]:
    """
    Combines Path Parameter, Query Parameter, and Pydantic Request Body.
    Pure Python processing is cleanly delegated to TelemetryProcessor.
    """
    start_time = time.perf_counter()

    try:
        # Business logic executed by pure Python data processing service
        result = TelemetryProcessor.process_batch(payload)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        status_flag = (
            ProcessingStatus.WARNING
            if result.anomalies_detected_count > 0
            else ProcessingStatus.SUCCESS
        )

        message = (
            f"Telemetry processed for device '{payload.device.device_id}' in group '{device_group}'. "
            f"Detected {result.anomalies_detected_count} anomalies across {result.valid_readings_count} readings."
        )
        if dry_run:
            message = f"[DRY RUN] {message}"

        return APIResponse(
            status=status_flag,
            message=message,
            data=result,
            metadata=AuditMetadata(
                execution_time_ms=elapsed_ms,
                processed_records_count=len(payload.readings)
            )
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Telemetry data processing failed: {str(exc)}"
        )
