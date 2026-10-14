"""
Pytest configuration and shared test fixtures.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """
    Synchronous FastAPI test client powered by httpx.
    """
    with TestClient(app) as test_client:
        yield test_client
