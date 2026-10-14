"""
Pure Python telemetry statistical data processor.

Features:
- Statistical metric aggregation (mean, sample variance, standard deviation)
- Quantile / percentile computations (p50, p95, p99) using linear interpolation
- Outlier and anomaly detection via Z-Score calculation
- Clean separation from web framework layer
"""

import math
from typing import Dict, List, Tuple
from app.models.telemetry import (
    AnomalyItem,
    MetricSummary,
    SensorReading,
    TelemetryBatchRequest,
    TelemetryProcessResponse,
)


class TelemetryProcessor:
    """
    Engine for processing, validating, and calculating statistics on batches of telemetry data.
    """

    @staticmethod
    def _compute_percentile(sorted_data: List[float], percentile: float) -> float:
        """
        Calculates percentile using standard linear interpolation method.
        """
        if not sorted_data:
            return 0.0
        if len(sorted_data) == 1:
            return sorted_data[0]

        k = (len(sorted_data) - 1) * (percentile / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_data[int(k)]
        d0 = sorted_data[int(f)] * (c - k)
        d1 = sorted_data[int(c)] * (k - f)
        return round(d0 + d1, 4)

    @classmethod
    def process_batch(cls, request: TelemetryBatchRequest) -> TelemetryProcessResponse:
        """
        Main execution pipeline for telemetry batch processing.
        """
        # Group readings by sensor type
        grouped_readings: Dict[str, List[SensorReading]] = {}
        for r in request.readings:
            stype = r.sensor_type.value
            grouped_readings.setdefault(stype, []).append(r)

        metrics_summary: List[MetricSummary] = []
        anomalies: List[AnomalyItem] = []

        total_valid = 0

        for stype, readings in grouped_readings.items():
            values = [r.value for r in readings if not math.isnan(r.value) and not math.isinf(r.value)]
            count = len(values)
            if count == 0:
                continue

            total_valid += count
            min_val = min(values)
            max_val = max(values)
            mean_val = sum(values) / count

            # Standard deviation calculation
            if count > 1:
                variance = sum((x - mean_val) ** 2 for x in values) / (count - 1)
                std_dev = math.sqrt(variance)
            else:
                std_dev = 0.0

            sorted_vals = sorted(values)
            p50 = cls._compute_percentile(sorted_vals, 50.0) if request.options.compute_percentiles else None
            p95 = cls._compute_percentile(sorted_vals, 95.0) if request.options.compute_percentiles else None
            p99 = cls._compute_percentile(sorted_vals, 99.0) if request.options.compute_percentiles else None

            metrics_summary.append(
                MetricSummary(
                    sensor_type=stype,
                    count=count,
                    min_value=round(min_val, 4),
                    max_value=round(max_val, 4),
                    mean_value=round(mean_val, 4),
                    std_dev=round(std_dev, 4),
                    p50_value=p50,
                    p95_value=p95,
                    p99_value=p99,
                )
            )

            # Anomaly detection via Z-Score
            if request.options.detect_anomalies and std_dev > 1e-6:
                threshold = request.options.z_score_threshold
                for r in readings:
                    z = (r.value - mean_val) / std_dev
                    if abs(z) >= threshold:
                        severity = "critical" if abs(z) >= (threshold * 1.5) else "warning"
                        anomalies.append(
                            AnomalyItem(
                                sensor_id=r.sensor_id,
                                sensor_type=stype,
                                value=round(r.value, 4),
                                expected_mean=round(mean_val, 4),
                                z_score=round(z, 3),
                                timestamp=r.timestamp,
                                severity=severity,
                            )
                        )

        return TelemetryProcessResponse(
            device_id=request.device.device_id,
            total_received=len(request.readings),
            valid_readings_count=total_valid,
            anomalies_detected_count=len(anomalies),
            metrics_summary=metrics_summary,
            anomalies=anomalies,
        )
