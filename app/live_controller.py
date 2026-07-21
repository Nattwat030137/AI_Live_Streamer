"""Application controller for live AI commerce."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.llm.factory import create_llm_provider
from app.policies.engine import GovernanceEngine
from app.services import (
    CommerceService,
    ResponseGenerationService,
)
from app.services.models import CommerceResponse


VoiceCallback = Callable[[str], None]


class LiveCommerceController:
    """Connect commerce processing with an optional voice output."""

    def __init__(
        self,
        *,
        provider_name: str | None = None,
        provider_options: dict[str, Any] | None = None,
        commerce_service: CommerceService | None = None,
        voice_callback: VoiceCallback | None = None,
    ) -> None:
        """Initialize the live commerce application flow."""

        if commerce_service is None:
            provider = create_llm_provider(
                provider_name,
                **dict(provider_options or {}),
            )
            generation_service = (
                ResponseGenerationService(
                    provider=provider,
                )
            )
            commerce_service = CommerceService(
                response_generation_service=(
                    generation_service
                ),
                governance_engine=GovernanceEngine(),
            )

        self.commerce_service = commerce_service
        self.voice_callback = voice_callback

    def process_message(
        self,
        customer_message: str,
        *,
        platform: str = "shopee",
        speak_response: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> CommerceResponse:
        """Process one live message and optionally speak its reply."""

        response = self.commerce_service.process_message(
            customer_message,
            platform=platform,
            metadata=metadata,
        )

        should_speak = (
            speak_response
            and self.voice_callback is not None
            and response.allowed
            and bool(response.text.strip())
        )

        if should_speak:
            self.voice_callback(response.text)

        return response