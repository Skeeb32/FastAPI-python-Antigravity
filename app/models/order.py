"""
Order and financial settlement domain models.
Demonstrates complex Pydantic request bodies, nested collections, and validation.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class CustomerTier(str, Enum):
    STANDARD = "standard"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class CurrencyCode(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"


class LineItem(BaseModel):
    item_id: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="SKU or product identifier.",
        examples=["SKU-CORE-900"]
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Product title or description."
    )
    quantity: int = Field(
        ...,
        gt=0,
        le=1000,
        description="Number of units ordered."
    )
    unit_price: float = Field(
        ...,
        gt=0.0,
        description="Unit price before discounts or taxes."
    )
    category: str = Field(
        default="general",
        description="Merchandise category for differential taxation."
    )


class CustomerInfo(BaseModel):
    customer_id: str = Field(
        ...,
        min_length=4,
        max_length=64,
        description="Unique customer reference ID."
    )
    email: str = Field(
        ...,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        description="Customer email address."
    )
    tier: CustomerTier = Field(
        default=CustomerTier.STANDARD,
        description="Loyalty / membership tier affecting volume discounts."
    )
    tax_exempt: bool = Field(
        default=False,
        description="Flag indicating corporate or non-profit tax exemption."
    )


class OrderSettlementRequest(BaseModel):
    """
    Request body for processing and settling a commercial multi-item purchase.
    Follows: https://fastapi.tiangolo.com/tutorial/body/
    """
    order_id: str = Field(
        ...,
        min_length=6,
        max_length=64,
        description="Client-side generated idempotent order idempotency token or ID.",
        examples=["ORD-2026-X992"]
    )
    customer: CustomerInfo = Field(
        ...,
        description="Customer and account context."
    )
    items: List[LineItem] = Field(
        ...,
        min_length=1,
        description="Non-empty list of purchased items."
    )
    currency: CurrencyCode = Field(
        default=CurrencyCode.USD,
        description="Transactional currency."
    )
    promo_code: Optional[str] = Field(
        default=None,
        max_length=32,
        description="Optional coupon or promotional voucher code."
    )
    shipping_country: str = Field(
        default="US",
        min_length=2,
        max_length=2,
        description="ISO 3166-1 alpha-2 destination country code."
    )

    @model_validator(mode="after")
    def validate_promo_codes(self) -> "OrderSettlementRequest":
        if self.promo_code:
            valid_codes = {"WELCOME10", "ANTIGRAVITY20", "VIPFLASH"}
            if self.promo_code.upper() not in valid_codes:
                raise ValueError(
                    f"Promo code '{self.promo_code}' is invalid or expired. "
                    f"Eligible codes: {', '.join(sorted(valid_codes))}"
                )
        return self


class SettledLineItem(BaseModel):
    item_id: str
    name: str
    quantity: int
    unit_price: float
    gross_total: float
    discount_amount: float
    tax_amount: float
    net_total: float


class OrderSettlementResponse(BaseModel):
    order_id: str
    customer_id: str
    currency: str
    subtotal: float
    tier_discount_amount: float
    promo_discount_amount: float
    total_tax_amount: float
    shipping_fee: float
    grand_total: float
    checksum_hash: str
    settled_at: datetime
    items: List[SettledLineItem]
