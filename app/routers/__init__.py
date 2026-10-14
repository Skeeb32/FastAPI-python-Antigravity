"""
Routers package init.
"""

from app.routers.health import router as health_router
from app.routers.telemetry import router as telemetry_router
from app.routers.orders import router as orders_router
from app.routers.datasets import router as datasets_router

__all__ = [
    "health_router",
    "telemetry_router",
    "orders_router",
    "datasets_router",
]
