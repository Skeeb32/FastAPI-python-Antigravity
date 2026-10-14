"""
Integration and validation tests for Order Settlement API endpoints.
Tests FastAPI Request Body ingestion and Pydantic validation rules.
"""

from fastapi.testclient import TestClient


def test_order_settlement_standard_customer(client: TestClient):
    payload = {
        "order_id": "ORD-2026-TEST01",
        "customer": {
            "customer_id": "CUST-9999",
            "email": "alex.doe@example.com",
            "tier": "standard",
            "tax_exempt": False,
        },
        "items": [
            {
                "item_id": "SKU-CPU-01",
                "name": "Server Processor",
                "quantity": 2,
                "unit_price": 250.00,
                "category": "electronics",
            },
            {
                "item_id": "SKU-RAM-02",
                "name": "64GB DDR5 RAM",
                "quantity": 4,
                "unit_price": 100.00,
                "category": "electronics",
            },
        ],
        "currency": "USD",
        "shipping_country": "US",
    }

    response = client.post("/api/v1/orders/merchant-corp/settle", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "success"
    data = res_json["data"]
    assert data["order_id"] == "ORD-2026-TEST01"
    assert data["subtotal"] == 900.00
    assert data["tier_discount_amount"] == 0.0  # standard tier
    assert data["shipping_fee"] == 0.0  # free over 100
    assert data["grand_total"] > 900.00  # taxes added
    assert len(data["checksum_hash"]) == 64  # sha256


def test_order_settlement_platinum_tier_and_promo(client: TestClient):
    payload = {
        "order_id": "ORD-2026-PLATINUM",
        "customer": {
            "customer_id": "VIP-8888",
            "email": "executive@enterprise.org",
            "tier": "platinum",
            "tax_exempt": True,
        },
        "items": [
            {
                "item_id": "SKU-SUITE-ENTERPRISE",
                "name": "Enterprise License Pack",
                "quantity": 1,
                "unit_price": 1000.00,
            }
        ],
        "currency": "USD",
        "promo_code": "ANTIGRAVITY20",
        "shipping_country": "US",
    }

    response = client.post("/api/v1/orders/acme-hq/settle", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    data = res_json["data"]
    # 1000 subtotal. Platinum = 15% discount ($150). Net = $850.
    # ANTIGRAVITY20 = 20% on remaining ($170). Net = $680. Tax exempt = $0 tax.
    assert data["subtotal"] == 1000.00
    assert data["tier_discount_amount"] == 150.00
    assert data["promo_discount_amount"] == 170.00
    assert data["total_tax_amount"] == 0.00
    assert data["grand_total"] == 680.00


def test_order_settlement_invalid_promo_rejected(client: TestClient):
    payload = {
        "order_id": "ORD-2026-ERR",
        "customer": {
            "customer_id": "CUST-1",
            "email": "user@test.com",
            "tier": "standard",
        },
        "items": [
            {
                "item_id": "SKU-01",
                "name": "Item",
                "quantity": 1,
                "unit_price": 50.0,
            }
        ],
        "promo_code": "INVALID_CODE_99",
    }

    response = client.post("/api/v1/orders/shop/settle", json=payload)
    assert response.status_code == 422
    res_json = response.json()
    assert res_json["status"] == "failed"
    assert "promo code" in str(res_json).lower()
