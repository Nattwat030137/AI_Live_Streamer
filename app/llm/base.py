"""Base interface สำหรับ LLM Provider."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

from app.llm.types import (
    LLMHealthStatus,
    LLMRequest,
    LLMResponse,
)


class LLMProvider(ABC):
    """Interface กลางสำหรับ LLM Provider ทุกชนิด."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """ชื่อ Provider เช่น mock หรือ openai."""

    @property
    @abstractmethod
    def default_model(self) -> str:
        """ชื่อ Model เริ่มต้นของ Provider."""

    @abstractmethod
    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """สร้างคำตอบแบบไม่ Streaming."""

    def generate_text(
        self,
        request: LLMRequest,
    ) -> str:
        """สร้างคำตอบและคืนเฉพาะข้อความ."""

        return self.generate(
            request
        ).text

    def stream(
        self,
        request: LLMRequest,
    ) -> Iterator[str]:
        """
        Streaming Interface เริ่มต้น.

        Provider ที่รองรับ Streaming จริง
        สามารถ Override เมธอดนี้ได้
        """

        response = self.generate(
            request
        )

        if response.text:
            yield response.text

    def health_check(
        self,
    ) -> LLMHealthStatus:
        """ตรวจสอบสถานะ Provider."""

        return LLMHealthStatus(
            healthy=True,
            provider=self.provider_name,
            message="Provider พร้อมใช้งาน",
            metadata={
                "default_model": self.default_model,
            },
        )

    def metadata(
        self,
    ) -> dict[str, Any]:
        """คืนข้อมูลสรุปของ Provider."""

        return {
            "provider": self.provider_name,
            "default_model": self.default_model,
            "supports_streaming": (
                self.supports_streaming
            ),
        }

    @property
    def supports_streaming(
        self,
    ) -> bool:
        """ระบุว่า Provider รองรับ Streaming จริงหรือไม่."""

        return False
