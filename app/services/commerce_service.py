"""Commerce service for processing customer messages."""

from __future__ import annotations

from time import perf_counter

from app.services.models import CommerceResponse


class CommerceService:
    """
    Transport-independent business service for AI Commerce.

    The service can later be used by Console, LINE, TikTok,
    OBS, or a Web API without changing the response model.
    """

    def process_message(
        self,
        customer_message: str,
        platform: str = "shopee",
    ) -> CommerceResponse:
        """
        Process a customer message and return a standard response.

        Sprint 30.3 establishes the public service interface.
        The complete commerce pipeline will be connected later.
        """

        started_at = perf_counter()

        message = customer_message.strip()
        selected_platform = platform.strip().lower() or "shopee"

        if not message:
            elapsed_ms = (perf_counter() - started_at) * 1000

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

        elapsed_ms = (perf_counter() - started_at) * 1000

        return CommerceResponse(
            text="CommerceService is ready.",
            allowed=True,
            risk_score=0.0,
            compliance_score=100.0,
            execution_time_ms=elapsed_ms,
            metadata={
                "customer_message": message,
                "platform": selected_platform,
                "status": "service_ready",
            },
        )