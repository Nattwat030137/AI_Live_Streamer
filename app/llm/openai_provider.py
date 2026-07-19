"""OpenAI Provider สำหรับ LLM Provider Layer."""

from __future__ import annotations

from typing import Any, Protocol

from app.llm.base import LLMProvider
from app.llm.config import (
    LLMConfig,
    load_llm_config,
)
from app.llm.types import (
    LLMHealthStatus,
    LLMRequest,
    LLMResponse,
    LLMUsage,
)


class ResponsesAPIProtocol(Protocol):
    """Protocol ขั้นต่ำของ client.responses."""

    def create(
        self,
        **kwargs: Any,
    ) -> Any:
        """สร้าง OpenAI Response."""


class OpenAIClientProtocol(Protocol):
    """Protocol ขั้นต่ำของ OpenAI Client."""

    responses: ResponsesAPIProtocol


class OpenAIProvider(LLMProvider):
    """LLM Provider ที่เรียก OpenAI Responses API."""

    PROVIDER_NAME = "openai"

    def __init__(
        self,
        *,
        config: LLMConfig | None = None,
        client: OpenAIClientProtocol | None = None,
        dry_run: bool = False,
    ) -> None:
        """สร้าง OpenAI Provider."""

        self.config = (
            config
            if config is not None
            else load_llm_config()
        )
        self.dry_run = bool(dry_run)

        if client is not None:
            self._client = client
        elif self.dry_run:
            self._client = None
        else:
            self._client = self._create_client()

    @property
    def provider_name(self) -> str:
        """ชื่อ Provider."""

        return self.PROVIDER_NAME

    @property
    def default_model(self) -> str:
        """ชื่อ Model เริ่มต้น."""

        return self.config.openai_model

    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """สร้างคำตอบผ่าน OpenAI Responses API."""

        if self.dry_run:
            return self._build_dry_run_response(
                request
            )

        if self._client is None:
            raise RuntimeError(
                "OpenAI client ยังไม่พร้อมใช้งาน"
            )

        request_payload = self._build_request_payload(
            request
        )

        try:
            raw_response = (
                self._client.responses.create(
                    **request_payload
                )
            )
        except Exception as error:
            raise RuntimeError(
                "OpenAI Responses API request failed: "
                f"{error}"
            ) from error

        return self._map_response(
            raw_response=raw_response,
            requested_model=request_payload[
                "model"
            ],
        )

    def health_check(
        self,
    ) -> LLMHealthStatus:
        """
        ตรวจสถานะ Provider โดยไม่ยิง API.

        การตรวจนี้ยืนยันเพียง Config และ Client
        ไม่ได้ทดสอบ Network หรือเครดิตบัญชี
        """

        if self.dry_run:
            return LLMHealthStatus(
                healthy=True,
                provider=self.provider_name,
                message=(
                    "OpenAI Provider พร้อมในโหมด dry-run"
                ),
                metadata={
                    "dry_run": True,
                    "model": self.default_model,
                },
            )

        if not self.config.has_openai_api_key:
            return LLMHealthStatus(
                healthy=False,
                provider=self.provider_name,
                message="ไม่พบ OPENAI_API_KEY",
                metadata={
                    "dry_run": False,
                    "model": self.default_model,
                },
            )

        return LLMHealthStatus(
            healthy=self._client is not None,
            provider=self.provider_name,
            message=(
                "OpenAI Provider พร้อมใช้งาน"
                if self._client is not None
                else "OpenAI client ยังไม่พร้อม"
            ),
            metadata={
                "dry_run": False,
                "model": self.default_model,
            },
        )

    @property
    def supports_streaming(
        self,
    ) -> bool:
        """เวอร์ชันนี้ยังไม่เปิด Streaming."""

        return False

    def metadata(
        self,
    ) -> dict[str, Any]:
        """คืนข้อมูลสรุปของ Provider."""

        data = super().metadata()
        data.update(
            {
                "dry_run": self.dry_run,
                "timeout_seconds": (
                    self.config
                    .openai_timeout_seconds
                ),
                "max_output_tokens": (
                    self.config
                    .openai_max_output_tokens
                ),
                "has_api_key": (
                    self.config.has_openai_api_key
                ),
            }
        )
        return data

    def _create_client(
        self,
    ) -> OpenAIClientProtocol:
        """สร้าง OpenAI SDK Client."""

        api_key = (
            self.config.require_openai_api_key()
        )

        try:
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError(
                "ไม่พบแพ็กเกจ openai "
                "กรุณาติดตั้งด้วย pip install openai"
            ) from error

        return OpenAI(
            api_key=api_key,
            timeout=(
                self.config
                .openai_timeout_seconds
            ),
        )

    def _build_request_payload(
        self,
        request: LLMRequest,
    ) -> dict[str, Any]:
        """สร้าง Parameters สำหรับ responses.create()."""

        model = (
            request.model.strip()
            or self.default_model
        )

        instructions = (
            request.system_message.strip()
        )

        input_text = self._build_input_text(
            request
        )

        payload: dict[str, Any] = {
            "model": model,
            "input": input_text,
            "max_output_tokens": (
                request.max_output_tokens
                or self.config
                .openai_max_output_tokens
            ),
        }

        if instructions:
            payload["instructions"] = (
                instructions
            )

        temperature = (
            request.temperature
            if request.temperature is not None
            else self.config.openai_temperature
        )

        if temperature is not None:
            payload["temperature"] = temperature

        return payload

    @staticmethod
    def _build_input_text(
        request: LLMRequest,
    ) -> str:
        """รวม Prompt กับข้อความลูกค้า."""

        customer_message = (
            request.customer_message.strip()
        )

        if not customer_message:
            return request.prompt.strip()

        return (
            f"{request.prompt.strip()}\n\n"
            "Customer Message:\n"
            f"{customer_message}"
        )

    def _build_dry_run_response(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """คืนผลจำลองโดยไม่เรียก API."""

        payload = self._build_request_payload(
            request
        )

        return LLMResponse(
            text=(
                "[DRY RUN] OpenAI request "
                "validated successfully."
            ),
            provider=self.provider_name,
            model=str(payload["model"]),
            response_type="dry_run",
            matched_rule="",
            finish_reason="dry_run",
            request_id="",
            usage=LLMUsage(),
            metadata={
                "dry_run": True,
                "request_payload": payload,
            },
        )

    def _map_response(
        self,
        *,
        raw_response: Any,
        requested_model: str,
    ) -> LLMResponse:
        """แปลง OpenAI Response เป็น LLMResponse."""

        response_text = str(
            getattr(
                raw_response,
                "output_text",
                "",
            )
            or ""
        )

        response_id = str(
            getattr(
                raw_response,
                "id",
                "",
            )
            or ""
        )

        response_model = str(
            getattr(
                raw_response,
                "model",
                requested_model,
            )
            or requested_model
        )

        status = str(
            getattr(
                raw_response,
                "status",
                "",
            )
            or ""
        )

        usage = self._map_usage(
            getattr(
                raw_response,
                "usage",
                None,
            )
        )

        finish_reason = (
            self._resolve_finish_reason(
                raw_response=raw_response,
                status=status,
            )
        )

        return LLMResponse(
            text=response_text,
            provider=self.provider_name,
            model=response_model,
            response_type="text",
            matched_rule="",
            finish_reason=finish_reason,
            request_id=response_id,
            usage=usage,
            metadata={
                "status": status,
            },
        )

    @staticmethod
    def _map_usage(
        raw_usage: Any,
    ) -> LLMUsage:
        """แปลง Usage จาก OpenAI SDK."""

        if raw_usage is None:
            return LLMUsage()

        input_tokens = int(
            getattr(
                raw_usage,
                "input_tokens",
                0,
            )
            or 0
        )

        output_tokens = int(
            getattr(
                raw_usage,
                "output_tokens",
                0,
            )
            or 0
        )

        total_tokens = int(
            getattr(
                raw_usage,
                "total_tokens",
                input_tokens + output_tokens,
            )
            or (
                input_tokens
                + output_tokens
            )
        )

        return LLMUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

    @staticmethod
    def _resolve_finish_reason(
        *,
        raw_response: Any,
        status: str,
    ) -> str:
        """สร้าง Finish Reason จากสถานะ Response."""

        incomplete_details = getattr(
            raw_response,
            "incomplete_details",
            None,
        )

        incomplete_reason = str(
            getattr(
                incomplete_details,
                "reason",
                "",
            )
            or ""
        )

        if incomplete_reason:
            return incomplete_reason

        return status or "completed"


def main() -> None:
    """ทดสอบ OpenAI Provider แบบ dry-run."""

    provider = OpenAIProvider(
        dry_run=True
    )

    response = provider.generate(
        LLMRequest(
            prompt="ตอบอย่างสุภาพและกระชับ",
            customer_message="สวัสดีครับ",
            system_message=(
                "คุณคือ AI Sales Agent "
                "ของร้าน Bakery D'Ver"
            ),
        )
    )

    print("=" * 60)
    print("OpenAI Provider Dry Run")
    print("=" * 60)
    print(
        f"Provider: {response.provider}"
    )
    print(
        f"Model: {response.model}"
    )
    print(
        f"Finish reason: "
        f"{response.finish_reason}"
    )
    print(
        f"Text: {response.text}"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
