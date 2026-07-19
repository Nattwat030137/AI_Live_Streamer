"""Shared types สำหรับ LLM Provider Layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class LLMRequest:
    """คำขอสำหรับ LLM Provider."""

    prompt: str
    customer_message: str = ""
    system_message: str = ""
    model: str = ""
    temperature: float | None = None
    max_output_tokens: int | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """ตรวจสอบค่าพื้นฐานของ Request."""

        if not self.prompt.strip():
            raise ValueError(
                "LLMRequest.prompt ต้องไม่ว่าง"
            )

        if (
            self.temperature is not None
            and not 0.0 <= self.temperature <= 2.0
        ):
            raise ValueError(
                "temperature ต้องอยู่ระหว่าง 0.0 ถึง 2.0"
            )

        if (
            self.max_output_tokens is not None
            and self.max_output_tokens <= 0
        ):
            raise ValueError(
                "max_output_tokens ต้องมากกว่า 0"
            )

    def to_dict(self) -> dict[str, Any]:
        """แปลง Request เป็น Dictionary."""

        return {
            "prompt": self.prompt,
            "customer_message": self.customer_message,
            "system_message": self.system_message,
            "model": self.model,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class LLMUsage:
    """ข้อมูล Token Usage จาก Provider."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def __post_init__(self) -> None:
        """ตรวจสอบ Token Usage."""

        if min(
            self.input_tokens,
            self.output_tokens,
            self.total_tokens,
        ) < 0:
            raise ValueError(
                "Token usage ต้องไม่เป็นค่าติดลบ"
            )

    def to_dict(self) -> dict[str, int]:
        """แปลง Usage เป็น Dictionary."""

        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """ผลลัพธ์มาตรฐานจาก LLM Provider."""

    text: str
    provider: str
    model: str
    response_type: str = "text"
    matched_rule: str = ""
    finish_reason: str = ""
    request_id: str = ""
    usage: LLMUsage = field(
        default_factory=LLMUsage
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """ตรวจสอบค่าพื้นฐานของ Response."""

        if not self.provider.strip():
            raise ValueError(
                "LLMResponse.provider ต้องไม่ว่าง"
            )

        if not self.model.strip():
            raise ValueError(
                "LLMResponse.model ต้องไม่ว่าง"
            )

    @property
    def has_text(self) -> bool:
        """ตรวจว่ามีข้อความตอบกลับหรือไม่."""

        return bool(
            self.text.strip()
        )

    def to_dict(self) -> dict[str, Any]:
        """แปลง Response เป็น Dictionary."""

        return {
            "text": self.text,
            "provider": self.provider,
            "model": self.model,
            "response_type": self.response_type,
            "matched_rule": self.matched_rule,
            "finish_reason": self.finish_reason,
            "request_id": self.request_id,
            "usage": self.usage.to_dict(),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class LLMHealthStatus:
    """สถานะความพร้อมของ LLM Provider."""

    healthy: bool
    provider: str
    message: str = ""
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """แปลง Health Status เป็น Dictionary."""

        return {
            "healthy": self.healthy,
            "provider": self.provider,
            "message": self.message,
            "metadata": dict(self.metadata),
        }
