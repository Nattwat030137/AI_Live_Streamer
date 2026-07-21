"""Commerce service for processing customer messages."""

from __future__ import annotations

from time import perf_counter

from app.intent_engine import Intent, detect_intent
from app.memory.conversation import ConversationMemory
from app.product_attribute import (
    ProductAttribute,
    detect_product_attribute,
)
from app.services.models import (
    CommerceContext,
    CommerceResponse,
)
from app.services.search_planning_service import (
    SearchPlanningService,
)


class CommerceService:
    """
    Transport-independent business service for AI Commerce.

    The service can later be used by Console, LINE, TikTok,
    OBS, or a Web API without changing the response model.
    """

    def __init__(
        self,
        *,
        memory: ConversationMemory | None = None,
    ) -> None:
        """Initialize commerce and search-planning services."""

        self.memory = memory or ConversationMemory()
        self.search_planning_service = (
            SearchPlanningService(
                memory=self.memory,
            )
        )

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
        """
        Analyze a customer message and prepare its search plan.
        """

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

        planning_result = (
            self.search_planning_service.prepare(
                customer_message=message,
            )
        )

        resolved_models = list(
            planning_result.resolved_models
        )

        self.memory.add_customer(
            message,
            metadata={
                "models": resolved_models,
                "intent": intent.value,
                "product_attribute": (
                    product_attribute.value
                ),
                "platform": selected_platform,
            },
        )

        self.memory.update_context(
            intent=intent.value,
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
                "resolved_models": resolved_models,
                "search_plan": (
                    planning_result.search_plan_data
                ),
                "search_status": "prepared",
                "status": "intent_analyzed",
            },
        )