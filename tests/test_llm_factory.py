"""Regression tests สำหรับ LLMFactory ที่รองรับ Mock และ OpenAI."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from app.llm.base import LLMProvider
from app.llm.config import LLMConfig
from app.llm.factory import (
    LLMFactory,
    create_llm_provider,
)
from app.llm.mock_provider import MockProvider
from app.llm.openai_provider import (
    OpenAIProvider,
)
from app.llm.types import LLMRequest


@contextmanager
def temporary_environment(
    key: str,
    value: str | None,
) -> Iterator[None]:
    """ตั้งค่า Environment ชั่วคราว."""

    original_exists = key in os.environ
    original_value = os.environ.get(
        key
    )

    try:
        if value is None:
            os.environ.pop(
                key,
                None,
            )
        else:
            os.environ[key] = value

        yield

    finally:
        if original_exists:
            assert original_value is not None
            os.environ[key] = original_value
        else:
            os.environ.pop(
                key,
                None,
            )


def main() -> None:
    """รัน Regression Test ของ LLMFactory."""

    print("=" * 60)
    print("LLM Factory OpenAI Regression Test")
    print("=" * 60)

    passed = 0
    total = 11

    mock_provider = LLMFactory.create(
        "mock"
    )

    assert isinstance(
        mock_provider,
        MockProvider,
    )
    assert isinstance(
        mock_provider,
        LLMProvider,
    )

    passed += 1
    print("Create explicit mock...............PASS")

    alias_provider = LLMFactory.create(
        "test"
    )

    assert isinstance(
        alias_provider,
        MockProvider,
    )

    passed += 1
    print("Create mock alias..................PASS")

    with temporary_environment(
        "LLM_PROVIDER",
        None,
    ):
        default_provider = (
            LLMFactory.create()
        )

    assert isinstance(
        default_provider,
        MockProvider,
    )

    passed += 1
    print("Default provider...................PASS")

    openai_config = LLMConfig(
        provider="openai",
        openai_api_key="test-key",
        openai_model="test-model",
    )

    openai_provider = LLMFactory.create(
        "openai",
        config=openai_config,
        dry_run=True,
    )

    assert isinstance(
        openai_provider,
        OpenAIProvider,
    )
    assert isinstance(
        openai_provider,
        LLMProvider,
    )

    passed += 1
    print("Create explicit OpenAI............PASS")

    openai_alias = LLMFactory.create(
        "open-ai",
        config=openai_config,
        dry_run=True,
    )

    assert isinstance(
        openai_alias,
        OpenAIProvider,
    )

    passed += 1
    print("Create OpenAI alias...............PASS")

    with temporary_environment(
        "LLM_PROVIDER",
        "openai",
    ):
        environment_openai = (
            LLMFactory.create(
                config=openai_config,
                dry_run=True,
            )
        )

    assert isinstance(
        environment_openai,
        OpenAIProvider,
    )

    passed += 1
    print("Environment OpenAI................PASS")

    shortcut_provider = (
        create_llm_provider(
            "mock"
        )
    )

    assert isinstance(
        shortcut_provider,
        MockProvider,
    )

    passed += 1
    print("Shortcut function.................PASS")

    assert (
        LLMFactory.supported_providers()
        == (
            "mock",
            "openai",
        )
    )
    assert (
        LLMFactory.is_supported("mock")
        is True
    )
    assert (
        LLMFactory.is_supported("test")
        is True
    )
    assert (
        LLMFactory.is_supported("openai")
        is True
    )
    assert (
        LLMFactory.is_supported("open-ai")
        is True
    )
    assert (
        LLMFactory.is_supported("unknown")
        is False
    )

    passed += 1
    print("Provider metadata.................PASS")

    try:
        LLMFactory.create(
            "unknown-provider"
        )
    except ValueError as error:
        assert "ไม่รองรับ" in str(
            error
        )
    else:
        raise AssertionError(
            "Factory ต้องเกิด ValueError "
            "เมื่อ Provider ไม่รองรับ"
        )

    passed += 1
    print("Unsupported provider..............PASS")

    mock_response = mock_provider.generate(
        LLMRequest(
            prompt="ทดสอบ",
            customer_message="สวัสดีครับ",
        )
    )

    assert mock_response.provider == "mock"
    assert mock_response.matched_rule == (
        "GREETING"
    )

    passed += 1
    print("Mock generated response............PASS")

    openai_response = openai_provider.generate(
        LLMRequest(
            prompt="ตอบอย่างสุภาพ",
            customer_message="สวัสดีครับ",
        )
    )

    assert openai_response.provider == (
        "openai"
    )
    assert openai_response.finish_reason == (
        "dry_run"
    )
    assert (
        openai_response.metadata["dry_run"]
        is True
    )

    passed += 1
    print("OpenAI dry-run response............PASS")

    print("=" * 60)
    print(
        f"{passed} / {total} PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
