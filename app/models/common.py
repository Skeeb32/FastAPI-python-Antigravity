"""
Shared Pydantic models, generic response wrappers, and enums.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ProcessingStatus(str, Enum):
    SUCCESS = "success"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


class AuditMetadata(BaseModel):
    timestamp_utc: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when processing occurred."
    )
    execution_time_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Server-side data processing latency in milliseconds."
    )
    processed_records_count: int = Field(
        default=0,
        ge=0,
        description="Total number of records evaluated."
    )


class APIResponse(BaseModel, Generic[DataT]):
    status: ProcessingStatus = Field(
        default=ProcessingStatus.SUCCESS,
        description="Overall processing status."
    )
    message: str = Field(
        default="Operation completed successfully.",
        description="Human-readable status summary."
    )
    data: Optional[DataT] = Field(
        default=None,
        description="Result payload returned by service."
    )
    metadata: AuditMetadata = Field(
        default_factory=AuditMetadata,
        description="Processing and audit metrics."
    )
