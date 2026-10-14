"""
Dataset transformation and analytical processing domain models.
Demonstrates dynamic row-record validation, operations configuration, and profile outputs.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ImputationStrategy(str, Enum):
    DROP = "drop"
    MEAN = "mean"
    MEDIAN = "median"
    ZERO = "zero"


class ScalingMethod(str, Enum):
    NONE = "none"
    MIN_MAX = "min_max"
    STANDARD = "standard"


class ColumnTransformConfig(BaseModel):
    column_name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Name of the numeric column to transform."
    )
    imputation: ImputationStrategy = Field(
        default=ImputationStrategy.MEAN,
        description="Strategy for replacing missing / null / NaN values."
    )
    scaling: ScalingMethod = Field(
        default=ScalingMethod.MIN_MAX,
        description="Normalization or scaling algorithm."
    )
    clamp_min: Optional[float] = Field(
        default=None,
        description="Optional lower bound clamp for outliers."
    )
    clamp_max: Optional[float] = Field(
        default=None,
        description="Optional upper bound clamp for outliers."
    )


class DatasetTransformRequest(BaseModel):
    """
    Request body for tabular data processing.
    Accepts row-oriented dictionary records and transformation rules.
    Follows: https://fastapi.tiangolo.com/tutorial/body/
    """
    dataset_name: str = Field(
        ...,
        min_length=3,
        max_length=80,
        description="Descriptive name of the dataset.",
        examples=["housing-market-features-2026"]
    )
    records: List[Dict[str, Any]] = Field(
        ...,
        min_length=1,
        description="Collection of row records represented as key-value maps.",
        examples=[
            [{"id": 1, "price": 450000, "sqft": 1850, "rooms": 3},
             {"id": 2, "price": 620000, "sqft": 2400, "rooms": 4}]
        ]
    )
    columns_to_transform: List[ColumnTransformConfig] = Field(
        default_factory=list,
        description="Column-specific transformation and normalization specs."
    )
    drop_unspecified_columns: bool = Field(
        default=False,
        description="If True, only transformed columns and an id column will be retained."
    )


class ColumnProfile(BaseModel):
    column_name: str
    data_type: str
    count: int
    missing_count: int
    unique_count: int
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None


class DatasetTransformResponse(BaseModel):
    dataset_name: str
    original_row_count: int
    transformed_row_count: int
    column_profiles: List[ColumnProfile]
    transformed_records: List[Dict[str, Any]]
