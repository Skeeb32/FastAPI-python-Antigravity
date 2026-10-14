# FastAPI-python-Antigravity

> **High-Performance Python Backend Services & Data Processing Engine**  
> *Demonstrating FastAPI API Architecture, Pydantic Request Body Validation, and Decoupled Python Data Processing Pipelines.*

[![Python](https://img.shields.io/badge/Python-3.8%2B%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-e92063.svg?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📌 Executive Summary & Architecture Narrative

In modern distributed architectures, **Python** serves as the powerhouse for backend services, numerical analysis, and batch data processing. **FastAPI** provides an asynchronous, standards-based (OpenAPI 3.1, JSON Schema) framework for routing and exposing endpoints, while **Pydantic** models declare, coerce, and validate request bodies with granular constraints.

### Addressing Framework Ownership vs. Python Processing Ownership
When discussing backend and API contributions in technical interviews or engineering reviews:
- **FastAPI Layer (API Surface)**: Acts as the HTTP transport and contract layer. It handles routing, dependency injection, query/path parameter parsing, OpenAPI documentation generation, and ASGI concurrency.
- **Pydantic Layer (Contract & Ingestion)**: Enforces strict data contracts, validates types, evaluates regex/boundary constraints, and serializes responses as described in the official [FastAPI Request Body Tutorial](https://fastapi.tiangolo.com/tutorial/body/).
- **Python Processing Layer (Core Service Logic)**: Where the heavy computation and domain logic reside. The processing algorithms (statistical aggregation, quantile calculations, z-score anomaly detection, tiered pricing engines, and tabular normalization) are written as **pure Python services** (`app/services/`), decoupled from the web framework. This allows the business logic to run in CLI scripts, background workers (Celery, Temporal), or serverless functions without requiring FastAPI.

---

## 🏗️ Project Structure

```text
FastAPI-python-Antigravity/
├── app/
│   ├── __init__.py
│   ├── main.py                    # App factory, CORS middleware, 422 exception handlers
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py              # Application settings and environment variables
│   ├── models/                    # Pydantic v2 schemas and Request Body models
│   │   ├── __init__.py
│   │   ├── common.py              # Generic API response wrapper & audit metadata
│   │   ├── telemetry.py           # Sensor readings, edge device metadata, batch models
│   │   ├── order.py               # Commercial line items, customer tiers, settlement models
│   │   └── dataset.py             # Tabular records, transform configs, profiling models
│   ├── services/                  # Pure Python data processing engines (Framework-Independent)
│   │   ├── __init__.py
│   │   ├── telemetry_processor.py # Statistical aggregations, quantiles, Z-score outliers
│   │   ├── order_service.py       # Tiered discounts, promo codes, regional tax, SHA-256 seal
│   │   └── data_transformer.py    # Imputation, winsorizing clamps, Min-Max & Z-scaling
│   └── routers/                   # FastAPI endpoints & route definitions
│       ├── __init__.py
│       ├── health.py              # /healthz and /api/v1/system/info
│       ├── telemetry.py           # POST /api/v1/telemetry/{device_group}/process
│       ├── orders.py              # POST /api/v1/orders/{merchant_id}/settle
│       └── datasets.py            # POST /api/v1/datasets/transform
├── tests/                         # Full Pytest test suite (Integration & Pure Python)
│   ├── __init__.py
│   ├── conftest.py                # TestClient fixtures
│   ├── test_health.py
│   ├── test_telemetry.py
│   ├── test_orders.py
│   ├── test_datasets.py
│   └── test_pure_services.py     # Validates services independent of FastAPI
├── requirements.txt
├── pyproject.toml
├── .gitignore
└── README.md
```

---

## 🚀 Key Endpoints & Real-World Implementations

### 1. Telemetry Batch Ingestion & Statistical Outlier Detection
- **Endpoint**: `POST /api/v1/telemetry/{device_group}/process`
- **FastAPI & Pydantic Patterns**:
  - Combined **Path Parameter** (`device_group`), **Query Parameter** (`dry_run: bool`), and **Request Body** (`TelemetryBatchRequest`).
  - Nested schemas: `DeviceMetadata` containing hardware UUIDs, regex-validated firmware versions, and custom tag dictionaries.
  - List bodies: `List[SensorReading]` with constraints (`min_length=1`, max 5,000 via `@field_validator`).
- **Python Processing Engine**:
  - Groups metric data points by sensor type.
  - Calculates summary metrics: count, minimum, maximum, sample mean, variance, and sample standard deviation.
  - Computes exact quantiles ($p_{50}, p_{95}, p_{99}$) using linear interpolation.
  - Detects anomalies using normalized Z-Scores:
    $$\mathcal{Z} = \frac{x - \mu}{\sigma}$$
    Flagging observations exceeding configured standard deviation thresholds ($\mathcal{Z} \ge 2.5$) as warning or critical.

#### Example Request Body
```json
{
  "device": {
    "device_id": "edge-turbine-001",
    "firmware_version": "v3.1.0",
    "deployment_zone": "eu-north-offshore",
    "tags": {
      "facility": "rig-7",
      "cluster": "wind"
    }
  },
  "readings": [
    {"sensor_id": "s-01", "sensor_type": "temperature", "value": 45.2, "unit": "celsius"},
    {"sensor_id": "s-02", "sensor_type": "temperature", "value": 46.1, "unit": "celsius"},
    {"sensor_id": "s-03", "sensor_type": "temperature", "value": 45.8, "unit": "celsius"},
    {"sensor_id": "s-04", "sensor_type": "temperature", "value": 182.4, "unit": "celsius"}
  ],
  "options": {
    "detect_anomalies": true,
    "z_score_threshold": 2.0,
    "compute_percentiles": true
  }
}
```

---

### 2. Multi-Item Commercial Order Settlement & Cryptographic Audit
- **Endpoint**: `POST /api/v1/orders/{merchant_id}/settle`
- **FastAPI & Pydantic Patterns**:
  - Enums for customer tiers (`standard`, `silver`, `gold`, `platinum`) and currencies (`USD`, `EUR`, `GBP`, `CAD`).
  - Custom cross-field validation (`@model_validator(mode="after")`) ensuring promo voucher eligibility.
  - Bounded numeric fields (`unit_price > 0.0`, `1 <= quantity <= 1000`).
- **Python Processing Engine**:
  - Evaluates tiered volume discounts (5% Silver, 10% Gold, 15% Platinum).
  - Applies eligible promotional vouchers (percentage-based or flat discount).
  - Calculates destination country sales tax / VAT with exemption handling.
  - Computes shipping rules (free for orders $\ge \$100$, otherwise $\$9.99$).
  - Emits an immutable, deterministic **SHA-256 audit digest** over the settled ledger:
    $$\text{Checksum} = \text{SHA256}(\text{JSON}(\text{order\_id}, \text{subtotal}, \text{grand\_total}, \dots))$$

#### Example Request Body
```json
{
  "order_id": "ORD-2026-X992",
  "customer": {
    "customer_id": "CUST-4421",
    "email": "purchasing@acme-corp.com",
    "tier": "gold",
    "tax_exempt": false
  },
  "items": [
    {
      "item_id": "SKU-CORE-900",
      "name": "Rackmount Server Blade",
      "quantity": 2,
      "unit_price": 450.00,
      "category": "hardware"
    }
  ],
  "currency": "USD",
  "promo_code": "ANTIGRAVITY20",
  "shipping_country": "US"
}
```

---

### 3. Tabular Dataset Imputation, Scaling & Profiling
- **Endpoint**: `POST /api/v1/datasets/transform`
- **FastAPI & Pydantic Patterns**:
  - Heterogeneous dictionary collections (`List[Dict[str, Any]]`) paired with structured operational configurations (`ColumnTransformConfig`).
- **Python Processing Engine**:
  - Profiles incoming rows: null counts, distinct cardinality, inferring numeric vs categorical data types.
  - Executes configurable imputation strategies: `mean`, `median`, `zero`, or row-wise `drop`.
  - Enforces numeric clamping (winsorizing upper and lower boundaries).
  - Applies feature scaling:
    - **Min-Max Normalization**:
      $$x' = \frac{x - x_{\min}}{x_{\max} - x_{\min}}$$
    - **Standard Z-Score Normalization**:
      $$x' = \frac{x - \mu}{\sigma}$$

---

## 💻 Local Installation & Quickstart

### Prerequisites
- Python 3.8+ (tested up to Python 3.14)
- Git

### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/Skeeb32/FastAPI-python-Antigravity.git
cd FastAPI-python-Antigravity

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open your browser to:
- **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Schema Specification**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)
- **Health & Readiness Check**: [http://localhost:8000/healthz](http://localhost:8000/healthz)

---

## 🧪 Testing

The test suite covers both end-to-end FastAPI HTTP client calls (`fastapi.testclient.TestClient`) and isolated pure Python data processing logic:

```bash
pytest
```

Run with verbose reporting:
```bash
pytest -v --tb=short
```

---

## 📜 Official FastAPI Reference
- [FastAPI Tutorial: Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
