"""
Pure Python service unit tests (framework-independent).
Demonstrates and validates core data processing logic in isolation from FastAPI.
"""

from app.models.dataset import (
    ColumnTransformConfig,
    DatasetTransformRequest,
    ImputationStrategy,
    ScalingMethod,
)
from app.models.order import (
    CustomerInfo,
    CustomerTier,
    LineItem,
    OrderSettlementRequest,
)
from app.models.telemetry import (
    DeviceMetadata,
    SensorReading,
    SensorType,
    TelemetryBatchRequest,
    TelemetryProcessingOptions,
)
from app.services.data_transformer import DatasetTransformer
from app.services.order_service import OrderSettlementEngine
from app.services.telemetry_processor import TelemetryProcessor


def test_pure_telemetry_processor():
    request = TelemetryBatchRequest(
        device=DeviceMetadata(
            device_id="test-sensor-hub",
            firmware_version="v2.0.0",
        ),
        readings=[
            SensorReading(
                sensor_id=f"temp-{i}",
                sensor_type=SensorType.TEMPERATURE,
                value=20.0 + i,
                unit="celsius",
            )
            for i in range(10)
        ],
        options=TelemetryProcessingOptions(
            detect_anomalies=True,
            z_score_threshold=2.5,
            compute_percentiles=True,
        ),
    )

    result = TelemetryProcessor.process_batch(request)
    assert result.device_id == "test-sensor-hub"
    assert result.valid_readings_count == 10
    assert len(result.metrics_summary) == 1
    summary = result.metrics_summary[0]
    assert summary.sensor_type == "temperature"
    assert summary.min_value == 20.0
    assert summary.max_value == 29.0
    assert summary.mean_value == 24.5
    assert summary.p50_value is not None


def test_pure_order_settlement_engine():
    request = OrderSettlementRequest(
        order_id="ORD-PURE-PY-01",
        customer=CustomerInfo(
            customer_id="CUST-GOLD-1",
            email="gold.member@domain.com",
            tier=CustomerTier.GOLD,
            tax_exempt=False,
        ),
        items=[
            LineItem(
                item_id="PROD-A",
                name="Widget A",
                quantity=10,
                unit_price=20.0,
            ),
            LineItem(
                item_id="PROD-B",
                name="Widget B",
                quantity=5,
                unit_price=40.0,
            ),
        ],
        promo_code="WELCOME10",
        shipping_country="US",
    )

    settlement = OrderSettlementEngine.settle_order(request)
    # Subtotal = 10*20 + 5*40 = 400.
    # Gold tier = 10% ($40). Remaining basis = $360.
    # WELCOME10 = 10% on $360 ($36). Net taxable basis = $324.
    # Shipping = $0 (>= 100).
    assert settlement.subtotal == 400.00
    assert settlement.tier_discount_amount == 40.00
    assert settlement.promo_discount_amount == 36.00
    assert settlement.shipping_fee == 0.00
    assert settlement.grand_total > 324.00
    assert settlement.checksum_hash is not None


def test_pure_dataset_transformer():
    request = DatasetTransformRequest(
        dataset_name="metrics_sample",
        records=[
            {"id": 1, "cpu_usage": 10.0, "latency": 100},
            {"id": 2, "cpu_usage": 20.0, "latency": 200},
            {"id": 3, "cpu_usage": 30.0, "latency": 300},
            {"id": 4, "cpu_usage": 40.0, "latency": 400},
            {"id": 5, "cpu_usage": 50.0, "latency": 500},
        ],
        columns_to_transform=[
            ColumnTransformConfig(
                column_name="cpu_usage",
                imputation=ImputationStrategy.MEAN,
                scaling=ScalingMethod.MIN_MAX,
            )
        ],
    )

    response = DatasetTransformer.transform_dataset(request)
    assert response.dataset_name == "metrics_sample"
    assert response.transformed_row_count == 5
    scaled_cpus = [r["cpu_usage"] for r in response.transformed_records]
    assert scaled_cpus[0] == 0.0
    assert scaled_cpus[-1] == 1.0
