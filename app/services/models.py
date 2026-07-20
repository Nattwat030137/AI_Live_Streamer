"""Data models used by application commerce services."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.intent_engine import Intent
from app.product_attribute import ProductAttribute


@dataclass(slots=True)
class CommerceContext:
    """Typed analysis context prepared for a customer message."""

    intent: Intent
    product_attribute: ProductAttribute


@dataclass(slots=True)
class CommerceResponse:
    """
    Standard response returned by CommerceService.

    This model is transport-independent and can be used by
    Console, LINE, TikTok, OBS, and Web API.
    """

    text: str
    allowed: bool = True
    risk_score: float = 0.0
    compliance_score: float = 100.0
    execution_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
