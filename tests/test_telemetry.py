"""
Integration and validation tests for Telemetry API endpoints.
Tests FastAPI Request Body ingestion and Pydantic validation rules.
"""

from fastapi.testclient import TestClient


def test_telemetry_process_successful_batch(client: TestClient):
    payload = {
        "device": {
            "device_id": "edge-turbine-001",
            "firmware_version": "v3.1.0",
            "deployment_zone": "eu-north-offshore",
            "tags": {"facility": "rig-7", "cluster": "wind"},
        },
        "readings": [
            {
                "sensor_id": "sensor-temp-01",
                "sensor_type": "temperature",
                "value": 45.2,
                "unit": "celsius",
            },
            {
                "sensor_id": "sensor-temp-02",
                "sensor_type": "temperature",
                "value": 46.1,
                "unit": "celsius",
            },
            {
                "sensor_id": "sensor-temp-03",
                "sensor_type": "temperature",
                "value": 45.8,
                "unit": "celsius",
            },
            {
                "sensor_id": "sensor-temp-04",
                "sensor_type": "temperature",
                "value": 45.5,
                "unit": "celsius",
            },
            {
                "sensor_id": "sensor-press-01",
                "sensor_type": "pressure",
                "value": 2.15,
                "unit": "bar",
            },
        ],
        "options": {
            "detect_anomalies": True,
            "z_score_threshold": 2.5,
            "compute_percentiles": True,
        },
    }

    response = client.post("/api/v1/telemetry/fleet-alpha/process?dry_run=false", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "success"
    data = res_json["data"]
    assert data["device_id"] == "edge-turbine-001"
    assert data["total_received"] == 5
    assert data["valid_readings_count"] == 5
    assert len(data["metrics_summary"]) == 2  # temperature, pressure


def test_telemetry_detects_outlier_anomaly(client: TestClient):
    # Readings with a clear extreme outlier
    payload = {
        "device": {
            "device_id": "pump-station-42",
            "firmware_version": "v1.2",
            "deployment_zone": "us-west-desert",
        },
        "readings": [
            {"sensor_id": f"s-{i}", "sensor_type": "temperature", "value": 30.0, "unit": "celsius"}
            for i in range(15)
        ] + [
            # Extreme spike
            {"sensor_id": "s-spike", "sensor_type": "temperature", "value": 980.0, "unit": "celsius"}
        ],
        "options": {
            "detect_anomalies": True,
            "z_score_threshold": 2.0,
            "compute_percentiles": True,
        },
    }

    response = client.post("/api/v1/telemetry/pumps/process", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "warning"
    data = res_json["data"]
    assert data["anomalies_detected_count"] >= 1
    assert any(a["sensor_id"] == "s-spike" for a in data["anomalies"])


def test_telemetry_request_body_validation_error(client: TestClient):
    # Invalid payload: empty readings list, invalid sensor type, missing firmware
    invalid_payload = {
        "device": {
            "device_id": "dev-01",
            # missing firmware_version
        },
        "readings": [],  # min_length=1 constraint violated
    }

    response = client.post("/api/v1/telemetry/fleet-err/process", json=invalid_payload)
    assert response.status_code == 422
    res_json = response.json()
    assert res_json["status"] == "failed"
    assert "errors" in res_json
    error_locations = [e["loc"][-1] for e in res_json["errors"]]
    assert "firmware_version" in error_locations or "readings" in error_locations
