"""Mock Provider Adapter สำหรับ LLM Provider Layer."""

from __future__ import annotations

from typing import Any

from app.llm.base import LLMProvider
from app.llm.types import (
    LLMHealthStatus,
    LLMRequest,
    LLMResponse,
    LLMUsage,
)
from demo.knowledge_retriever import KnowledgeResult
from demo.mock_llm import MockLLMProvider


class MockProvider(LLMProvider):
    """
    Adapter ที่เชื่อม MockLLMProvider เดิมเข้ากับ LLMProvider Interface.

    จุดประสงค์คือรักษา Runtime เดิมที่ผ่าน Regression Test แล้ว
    โดยไม่ต้องแก้ demo/mock_llm.py ที่ถูก Lock ไว้
    """

    PROVIDER_NAME = "mock"

    def __init__(
        self,
        *,
        provider: MockLLMProvider | None = None,
    ) -> None:
        """สร้าง Mock Provider Adapter."""

        self._provider = (
            provider
            if provider is not None
            else MockLLMProvider()
        )

    @property
    def provider_name(self) -> str:
        """ชื่อ Provider."""

        return self.PROVIDER_NAME

    @property
    def default_model(self) -> str:
        """ชื่อ Model เริ่มต้น."""

        return self._provider.MODEL_NAME

    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """สร้างคำตอบผ่าน MockLLMProvider เดิม."""

        knowledge = self._extract_knowledge(
            request.metadata
        )

        legacy_response = self._provider.generate(
    prompt=request.prompt,
    customer_message=(
        request.customer_message
    ),
    knowledge=knowledge,
    product_attribute=(
        request.metadata.get(
            "product_attribute"
        )
    ),
)

        return LLMResponse(
            text=legacy_response.text,
            provider=self.provider_name,
            model=legacy_response.model,
            response_type=(
                legacy_response.response_type
            ),
            matched_rule=(
                legacy_response.matched_rule
            ),
            finish_reason="completed",
            usage=LLMUsage(),
            metadata={
                "adapter": (
                    "legacy_mock_llm_provider"
                ),
                "legacy_response": (
                    legacy_response.to_dict()
                ),
            },
        )

    def health_check(
        self,
    ) -> LLMHealthStatus:
        """ตรวจสอบว่า Mock Provider พร้อมใช้งาน."""

        return LLMHealthStatus(
            healthy=True,
            provider=self.provider_name,
            message=(
                "Mock Provider พร้อมใช้งาน"
            ),
            metadata={
                "default_model": (
                    self.default_model
                ),
                "adapter": (
                    "legacy_mock_llm_provider"
                ),
            },
        )

    @property
    def supports_streaming(
        self,
    ) -> bool:
        """Mock Provider ยังไม่มี Streaming จริง."""

        return False

    @staticmethod
    def _extract_knowledge(
        metadata: dict[str, Any],
    ) -> KnowledgeResult | None:
        """
        ดึง KnowledgeResult จาก Request metadata.

        Key มาตรฐานคือ metadata["knowledge"].
        """

        knowledge = metadata.get(
            "knowledge"
        )

        if knowledge is None:
            return None

        if not isinstance(
            knowledge,
            KnowledgeResult,
        ):
            raise TypeError(
                "metadata['knowledge'] "
                "ต้องเป็น KnowledgeResult"
            )

        return knowledge


def main() -> None:
    """ทดสอบ Mock Provider Adapter แบบ Command Line."""

    provider = MockProvider()

    request = LLMRequest(
        prompt=(
            "คุณคือ AI Sales Agent "
            "ของร้าน Bakery D'Ver"
        ),
        customer_message="สวัสดีครับ",
    )

    response = provider.generate(
        request
    )

    print("=" * 60)
    print("Mock Provider Adapter")
    print("=" * 60)
    print(
        f"Provider: {response.provider}"
    )
    print(
        f"Model: {response.model}"
    )
    print(
        f"Rule: {response.matched_rule}"
    )
    print(
        f"Text: {response.text}"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
