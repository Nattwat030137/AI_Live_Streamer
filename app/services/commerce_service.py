"""Commerce service for processing customer messages."""

from __future__ import annotations

from time import perf_counter

from app.intent_engine import Intent, detect_intent
from app.product_attribute import (
    ProductAttribute,
    detect_product_attribute,
)
from app.services.models import (
    CommerceContext,
    CommerceResponse,
)


class CommerceService:
    """
    Transport-independent business service for AI Commerce.

    The service can later be used by Console, LINE, TikTok,
    OBS, or a Web API without changing the response model.
    """

    def prepare_context(
        self,
        *,
        message: str,
        platform: str = "shopee",
    ) -> CommerceContext:
        """Prepare typed intent and product-attribute context."""

        response = self.process_message(
            customer_message=message,
            platform=platform,
        )

        if not response.allowed:
            raise ValueError(
                "Cannot prepare commerce context "
                "for an empty customer message."
            )

        return CommerceContext(
            intent=Intent(
                response.metadata["intent"]
            ),
            product_attribute=ProductAttribute(
                response.metadata[
                    "product_attribute"
                ]
            ),
        )

    def process_message(
        self,
        customer_message: str,
        platform: str = "shopee",
    ) -> CommerceResponse:
        """Process a customer message and return a standard response."""

        started_at = perf_counter()

        message = customer_message.strip()
        selected_platform = (
            platform.strip().lower() or "shopee"
        )

        if not message:
            elapsed_ms = (
                perf_counter() - started_at
            ) * 1000

            return CommerceResponse(
                text="กรุณาระบุข้อความของลูกค้า",
                allowed=False,
                risk_score=0.0,
                compliance_score=100.0,
                execution_time_ms=elapsed_ms,
                metadata={
                    "platform": selected_platform,
                    "status": "empty_message",
                },
            )

        intent = detect_intent(message)
        product_attribute = detect_product_attribute(
            message
        )

        elapsed_ms = (
            perf_counter() - started_at
        ) * 1000

        return CommerceResponse(
            text="CommerceService is ready.",
            allowed=True,
            risk_score=0.0,
            compliance_score=100.0,
            execution_time_ms=elapsed_ms,
            metadata={
                "customer_message": message,
                "platform": selected_platform,
                "intent": intent.value,
                "product_attribute": (
                    product_attribute.value
                ),
                "status": "intent_analyzed",
            },
        )
