"""
Pure Python order settlement and calculation engine.

Features:
- Tiered loyalty discount computations
- Promotional coupon applications with business constraints
- Multi-region sales tax calculation
- Line-item breakdown and subtotal aggregations
- Cryptographic SHA-256 audit receipt hashing
"""

from datetime import datetime, timezone
import hashlib
import json
from typing import Dict, List, Tuple
from app.models.order import (
    CustomerTier,
    OrderSettlementRequest,
    OrderSettlementResponse,
    SettledLineItem,
)


class OrderSettlementEngine:
    """
    Business service executing pricing, discount rules, tax, and order finalization.
    """

    TIER_DISCOUNT_RATES: Dict[CustomerTier, float] = {
        CustomerTier.STANDARD: 0.0,
        CustomerTier.SILVER: 0.05,
        CustomerTier.GOLD: 0.10,
        CustomerTier.PLATINUM: 0.15,
    }

    COUNTRY_TAX_RATES: Dict[str, float] = {
        "US": 0.075,   # Average sales tax
        "CA": 0.13,    # Harmonized sales tax
        "GB": 0.20,    # UK VAT
        "DE": 0.19,    # German VAT
        "FR": 0.20,    # French VAT
        "JP": 0.10,    # Japanese consumption tax
    }

    PROMO_DISCOUNTS: Dict[str, Tuple[str, float]] = {
        "WELCOME10": ("percent", 0.10),
        "ANTIGRAVITY20": ("percent", 0.20),
        "VIPFLASH": ("flat", 25.0),
    }

    @classmethod
    def settle_order(cls, request: OrderSettlementRequest) -> OrderSettlementResponse:
        """
        Executes order financial settlement logic.
        """
        subtotal = 0.0
        settled_items: List[SettledLineItem] = []

        tier_rate = cls.TIER_DISCOUNT_RATES.get(request.customer.tier, 0.0)
        tax_rate = 0.0 if request.customer.tax_exempt else cls.COUNTRY_TAX_RATES.get(
            request.shipping_country.upper(), 0.08
        )

        for item in request.items:
            gross = round(item.quantity * item.unit_price, 2)
            subtotal += gross

            # Individual line item tier discount
            item_tier_discount = round(gross * tier_rate, 2)
            discounted_basis = max(0.0, gross - item_tier_discount)
            item_tax = round(discounted_basis * tax_rate, 2)
            item_net = round(discounted_basis + item_tax, 2)

            settled_items.append(
                SettledLineItem(
                    item_id=item.item_id,
                    name=item.name,
                    quantity=item.quantity,
                    unit_price=round(item.unit_price, 2),
                    gross_total=gross,
                    discount_amount=item_tier_discount,
                    tax_amount=item_tax,
                    net_total=item_net,
                )
            )

        subtotal = round(subtotal, 2)
        tier_discount_total = round(sum(i.discount_amount for i in settled_items), 2)
        tax_total = round(sum(i.tax_amount for i in settled_items), 2)

        # Apply promotional discount on subtotal after tier discounts
        promo_discount_total = 0.0
        if request.promo_code:
            promo_key = request.promo_code.upper()
            if promo_key in cls.PROMO_DISCOUNTS:
                disc_type, disc_val = cls.PROMO_DISCOUNTS[promo_key]
                if disc_type == "percent":
                    promo_discount_total = round((subtotal - tier_discount_total) * disc_val, 2)
                elif disc_type == "flat":
                    promo_discount_total = min(round(disc_val, 2), max(0.0, subtotal - tier_discount_total))

        # Shipping logic: free if subtotal >= 100, else $9.99
        shipping_fee = 0.0 if subtotal >= 100.0 else 9.99

        grand_total = max(
            0.0,
            round(subtotal - tier_discount_total - promo_discount_total + tax_total + shipping_fee, 2)
        )

        settled_at = datetime.now(timezone.utc)

        # Generate cryptographic audit checksum hash
        audit_payload = {
            "order_id": request.order_id,
            "customer_id": request.customer.customer_id,
            "subtotal": subtotal,
            "grand_total": grand_total,
            "items_count": len(settled_items),
            "settled_at": settled_at.isoformat(),
        }
        checksum = hashlib.sha256(
            json.dumps(audit_payload, sort_keys=True).encode("utf-8")
        ).hexdigest()

        return OrderSettlementResponse(
            order_id=request.order_id,
            customer_id=request.customer.customer_id,
            currency=request.currency.value,
            subtotal=subtotal,
            tier_discount_amount=tier_discount_total,
            promo_discount_amount=promo_discount_total,
            total_tax_amount=tax_total,
            shipping_fee=shipping_fee,
            grand_total=grand_total,
            checksum_hash=checksum,
            settled_at=settled_at,
            items=settled_items,
        )
