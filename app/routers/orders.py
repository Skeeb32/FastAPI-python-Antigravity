"""
Commercial order calculation and financial settlement router.
Demonstrates:
- FastAPI Request Body validation with nested lists and cross-field constraints:
  https://fastapi.tiangolo.com/tutorial/body/
- Path parameter + Request Body combination
- Clean separation between HTTP routing and pure Python settlement math
"""

import time
from fastapi import APIRouter, HTTPException, Path, status
from app.models.common import APIResponse, AuditMetadata, ProcessingStatus
from app.models.order import (
    OrderSettlementRequest,
    OrderSettlementResponse,
)
from app.services.order_service import OrderSettlementEngine

router = APIRouter(prefix="/orders", tags=["Order Settlement & Pricing"])


@router.post(
    "/{merchant_id}/settle",
    response_model=APIResponse[OrderSettlementResponse],
    status_code=status.HTTP_200_OK,
    summary="Calculate & Settle Multi-Item Order",
    description=(
        "Processes an order settlement request body. Validates item constraints, applies loyalty "
        "tier and promotional discounts, calculates regional taxes, and produces a SHA-256 audit digest."
    )
)
async def settle_order(
    merchant_id: str = Path(
        ...,
        min_length=3,
        max_length=40,
        description="Originating merchant or subsidiary ID."
    ),
    order_request: OrderSettlementRequest = ...
) -> APIResponse[OrderSettlementResponse]:
    """
    Demonstrates FastAPI Request Body processing with complex nested structures.
    The pure Python financial calculation is handled by OrderSettlementEngine.
    """
    start_time = time.perf_counter()

    try:
        settlement = OrderSettlementEngine.settle_order(order_request)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return APIResponse(
            status=ProcessingStatus.SUCCESS,
            message=(
                f"Order '{settlement.order_id}' settled successfully for merchant '{merchant_id}'. "
                f"Grand total: {settlement.currency} {settlement.grand_total:.2f}"
            ),
            data=settlement,
            metadata=AuditMetadata(
                execution_time_ms=elapsed_ms,
                processed_records_count=len(order_request.items)
            )
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Order settlement calculation error: {str(exc)}"
        )
