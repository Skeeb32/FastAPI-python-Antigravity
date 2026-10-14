"""
Telemetry domain models: sensor reading schemas, batch request bodies, and statistical outputs.
Demonstrates nested Pydantic models, field constraints, and custom validators as per FastAPI tutorial.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class SensorType(str, Enum):
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    HUMIDITY = "humidity"
    VIBRATION = "vibration"
    VOLTAGE = "voltage"
    CURRENT = "current"


class SensorReading(BaseModel):
    """
    Individual sensor metric data point.
    Demonstrates scalar validation, constraints, and defaults.
    """
    sensor_id: str = Field(
        ...,
        min_length=3,
        max_length=64,
        description="Unique identifier for the sensor hardware.",
        examples=["sensor-temp-01a"]
    )
    sensor_type: SensorType = Field(
        ...,
        description="Categorical type of sensor."
    )
    value: float = Field(
        ...,
        description="Observed numeric sensor measurement value.",
        examples=[42.85]
    )
    unit: str = Field(
        ...,
        min_length=1,
        max_length=16,
        description="Unit of measurement (e.g. celsius, bar, percent, V, A).",
        examples=["celsius"]
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Observation timestamp in UTC."
    )
    is_calibrated: bool = Field(
        default=True,
        description="Whether this reading was captured by a certified calibrated sensor."
    )


class DeviceMetadata(BaseModel):
    """
    Hardware and environment context for device.
    Demonstrates nested model composition.
    """
    device_id: str = Field(
        ...,
        min_length=4,
        max_length=64,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        description="Unique device hardware serial number or identifier.",
        examples=["edge-node-alpha-402"]
    )
    firmware_version: str = Field(
        ...,
        pattern=r"^v?\d+\.\d+(\.\d+)?(-[a-zA-Z0-9.]+)?$",
        description="Semantic version string of the edge agent firmware.",
        examples=["v2.4.1"]
    )
    deployment_zone: str = Field(
        default="datacenter-us-east-1",
        description="Physical or logical cluster zone where device is hosted."
    )
    tags: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom key-value labels for filtering and categorization."
    )


class TelemetryProcessingOptions(BaseModel):
    """
    Configurable parameters governing the backend Python statistical processing.
    """
    detect_anomalies: bool = Field(
        default=True,
        description="Flag to compute z-scores and flag values exceeding threshold."
    )
    z_score_threshold: float = Field(
        default=2.5,
        gt=0.0,
        le=5.0,
        description="Number of standard deviations from mean to flag as an outlier."
    )
    impute_missing_timestamps: bool = Field(
        default=False,
        description="Interpolate or impute missing cadence readings."
    )
    compute_percentiles: bool = Field(
        default=True,
        description="Calculate 50th, 95th, and 99th percentiles."
    )


class TelemetryBatchRequest(BaseModel):
    """
    FastAPI Request Body model representing a batch of sensor readings from an edge node.
    Follows: https://fastapi.tiangolo.com/tutorial/body/
    """
    device: DeviceMetadata = Field(
        ...,
        description="Hardware and deployment metadata for the edge node."
    )
    readings: List[SensorReading] = Field(
        ...,
        min_length=1,
        description="Collection of sensor observations to be processed.",
    )
    options: TelemetryProcessingOptions = Field(
        default_factory=TelemetryProcessingOptions,
        description="Execution toggles for data processing."
    )

    @field_validator("readings")
    @classmethod
    def validate_readings_limit(cls, v: List[SensorReading]) -> List[SensorReading]:
        if len(v) > 5000:
            raise ValueError("Telemetry batches must not exceed 5000 readings per request.")
        return v


class MetricSummary(BaseModel):
    sensor_type: str
    count: int
    min_value: float
    max_value: float
    mean_value: float
    std_dev: float
    p50_value: Optional[float] = None
    p95_value: Optional[float] = None
    p99_value: Optional[float] = None


class AnomalyItem(BaseModel):
    sensor_id: str
    sensor_type: str
    value: float
    expected_mean: float
    z_score: float
    timestamp: datetime
    severity: str


class TelemetryProcessResponse(BaseModel):
    device_id: str
    total_received: int
    valid_readings_count: int
    anomalies_detected_count: int
    metrics_summary: List[MetricSummary]
    anomalies: List[AnomalyItem]
