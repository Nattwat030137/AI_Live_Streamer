"""Regression tests สำหรับ OpenAIProvider."""

from __future__ import annotations

from dataclasses import dataclass

from app.llm.config import LLMConfig
from app.llm.openai_provider import (
    OpenAIProvider,
)
from app.llm.types import (
    LLMRequest,
    LLMResponse,
)


@dataclass
class FakeUsage:
    """Usage จำลองจาก OpenAI SDK."""

    input_tokens: int = 12
    output_tokens: int = 8
    total_tokens: int = 20


@dataclass
class FakeIncompleteDetails:
    """Incomplete details จำลอง."""

    reason: str = ""


@dataclass
class FakeRawResponse:
    """Response จำลองจาก OpenAI SDK."""

    id: str = "resp_test_123"
    model: str = "test-model"
    status: str = "completed"
    output_text: str = "คำตอบจาก OpenAI จำลอง"
    usage: FakeUsage | None = None
    incomplete_details: (
        FakeIncompleteDetails | None
    ) = None


class FakeResponsesAPI:
    """responses.create() จำลอง."""

    def __init__(self) -> None:
        self.last_payload = None

    def create(self, **kwargs):
        """บันทึก Payload และคืน Response จำลอง."""

        self.last_payload = kwargs
        return FakeRawResponse(usage=FakeUsage())


class FakeOpenAIClient:
    """OpenAI Client จำลอง."""

    def __init__(self) -> None:
        self.responses = FakeResponsesAPI()


def main() -> None:
    """รัน Regression Test ของ OpenAIProvider."""

    print("=" * 60)
    print("OpenAI Provider Regression Test")
    print("=" * 60)

    passed = 0
    total = 8

    config = LLMConfig(
        provider="openai",
        openai_api_key="test-key",
        openai_model="test-model",
        openai_timeout_seconds=15.0,
        openai_temperature=0.2,
        openai_max_output_tokens=300,
    )

    dry_provider = OpenAIProvider(
        config=config,
        dry_run=True,
    )

    dry_response = dry_provider.generate(
        LLMRequest(
            prompt="ตอบอย่างสุภาพ",
            customer_message="สวัสดีครับ",
            system_message="คุณคือผู้ช่วยฝ่ายขาย",
        )
    )

    assert isinstance(
        dry_response,
        LLMResponse,
    )
    assert dry_response.provider == "openai"
    assert dry_response.model == "test-model"
    assert dry_response.finish_reason == "dry_run"
    assert (
        dry_response.metadata["dry_run"]
        is True
    )

    passed += 1
    print("Dry run.............................PASS")

    dry_payload = (
        dry_response
        .metadata["request_payload"]
    )

    assert dry_payload["model"] == "test-model"
    assert dry_payload["instructions"] == (
        "คุณคือผู้ช่วยฝ่ายขาย"
    )
    assert "สวัสดีครับ" in (
        dry_payload["input"]
    )
    assert dry_payload[
        "max_output_tokens"
    ] == 300
    assert dry_payload[
        "temperature"
    ] == 0.2

    passed += 1
    print("Request mapping.....................PASS")

    fake_client = FakeOpenAIClient()

    provider = OpenAIProvider(
        config=config,
        client=fake_client,
    )

    response = provider.generate(
        LLMRequest(
            prompt="ตอบข้อมูลสินค้า",
            customer_message="รุ่น5040",
            model="request-model",
            max_output_tokens=200,
            temperature=0.4,
        )
    )

    assert response.provider == "openai"
    assert response.model == "test-model"
    assert response.text == (
        "คำตอบจาก OpenAI จำลอง"
    )
    assert response.request_id == (
        "resp_test_123"
    )
    assert response.finish_reason == (
        "completed"
    )

    passed += 1
    print("Response mapping....................PASS")

    assert response.usage.input_tokens == 12
    assert response.usage.output_tokens == 8
    assert response.usage.total_tokens == 20

    passed += 1
    print("Usage mapping.......................PASS")

    payload = fake_client.responses.last_payload

    assert payload is not None
    assert payload["model"] == (
        "request-model"
    )
    assert payload[
        "max_output_tokens"
    ] == 200
    assert payload["temperature"] == 0.4

    passed += 1
    print("Request overrides...................PASS")

    health = provider.health_check()

    assert health.healthy is True
    assert health.provider == "openai"

    passed += 1
    print("Health check........................PASS")

    metadata = provider.metadata()

    assert metadata["provider"] == "openai"
    assert metadata["dry_run"] is False
    assert metadata["supports_streaming"] is False

    passed += 1
    print("Provider metadata...................PASS")

    class ErrorResponsesAPI:
        def create(self, **kwargs):
            raise ValueError("simulated failure")

    class ErrorClient:
        responses = ErrorResponsesAPI()

    error_provider = OpenAIProvider(
        config=config,
        client=ErrorClient(),
    )

    try:
        error_provider.generate(
            LLMRequest(
                prompt="ทดสอบ error",
            )
        )
    except RuntimeError as error:
        assert (
            "OpenAI Responses API "
            "request failed"
            in str(error)
        )
    else:
        raise AssertionError(
            "Provider ต้องแปลง API Error "
            "เป็น RuntimeError"
        )

    passed += 1
    print("Error mapping.......................PASS")

    print("=" * 60)
    print(
        f"{passed} / {total} PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
