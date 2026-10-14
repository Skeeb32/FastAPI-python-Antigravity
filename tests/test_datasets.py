"""
Integration and validation tests for Dataset Transformation API endpoints.
Tests FastAPI Request Body ingestion and Pydantic validation rules.
"""

from fastapi.testclient import TestClient


def test_dataset_transform_success(client: TestClient):
    payload = {
        "dataset_name": "real-estate-sample",
        "records": [
            {"id": 1, "price": 100000, "sqft": 1000, "city": "Dallas"},
            {"id": 2, "price": 200000, "sqft": 2000, "city": "Austin"},
            {"id": 3, "price": 300000, "sqft": 3000, "city": "Houston"},
            {"id": 4, "price": None, "sqft": 2500, "city": "Dallas"},  # missing price
        ],
        "columns_to_transform": [
            {
                "column_name": "price",
                "imputation": "mean",  # mean of 100k, 200k, 300k is 200k
                "scaling": "min_max",
            },
            {
                "column_name": "sqft",
                "imputation": "median",
                "scaling": "none",
            },
        ],
        "drop_unspecified_columns": False,
    }

    response = client.post("/api/v1/datasets/transform", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "success"
    data = res_json["data"]
    assert data["dataset_name"] == "real-estate-sample"
    assert data["original_row_count"] == 4
    assert data["transformed_row_count"] == 4

    records = data["transformed_records"]
    # Check that row 4 had price imputed and then scaled
    assert records[3]["price"] is not None
    # Min-max scaled price should be between 0.0 and 1.0
    for r in records:
        assert 0.0 <= r["price"] <= 1.0


def test_dataset_transform_drop_imputation(client: TestClient):
    payload = {
        "dataset_name": "clean-sample",
        "records": [
            {"id": 1, "score": 90.0},
            {"id": 2, "score": None},
            {"id": 3, "score": 85.0},
        ],
        "columns_to_transform": [
            {
                "column_name": "score",
                "imputation": "drop",
                "scaling": "none",
            }
        ],
    }

    response = client.post("/api/v1/datasets/transform", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["transformed_row_count"] == 2
    assert all(r["score"] is not None for r in data["transformed_records"])
