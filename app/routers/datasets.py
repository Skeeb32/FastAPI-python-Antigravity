"""
Tabular dataset transformation and profiling router.
Demonstrates:
- Dynamic schema validation within Request Body: https://fastapi.tiangolo.com/tutorial/body/
- Tabular record transformation, imputation, winsorizing, and feature scaling
- Decoupled pure Python transformation engine
"""

import time
from fastapi import APIRouter, HTTPException, status
from app.models.common import APIResponse, AuditMetadata, ProcessingStatus
from app.models.dataset import (
    DatasetTransformRequest,
    DatasetTransformResponse,
)
from app.services.data_transformer import DatasetTransformer

router = APIRouter(prefix="/datasets", tags=["Dataset Transformation & Profiling"])


@router.post(
    "/transform",
    response_model=APIResponse[DatasetTransformResponse],
    status_code=status.HTTP_200_OK,
    summary="Transform, Impute & Normalize Tabular Dataset",
    description=(
        "Consumes a tabular record payload with transformation rules. Executes numeric imputation, "
        "min/max clamping, feature scaling (Min-Max or Standard Z-Score), and calculates column summary profiles."
    )
)
async def transform_dataset(
    transform_request: DatasetTransformRequest = ...
) -> APIResponse[DatasetTransformResponse]:
    """
    Demonstrates FastAPI Request Body processing for batch data engineering workflows.
    Data manipulation is executed by DatasetTransformer.
    """
    start_time = time.perf_counter()

    try:
        response = DatasetTransformer.transform_dataset(transform_request)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return APIResponse(
            status=ProcessingStatus.SUCCESS,
            message=(
                f"Dataset '{response.dataset_name}' transformed successfully. "
                f"Input rows: {response.original_row_count}, Output rows: {response.transformed_row_count}."
            ),
            data=response,
            metadata=AuditMetadata(
                execution_time_ms=elapsed_ms,
                processed_records_count=response.transformed_row_count
            )
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dataset transformation failure: {str(exc)}"
        )
