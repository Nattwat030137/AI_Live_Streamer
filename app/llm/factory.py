"""Factory สำหรับสร้าง LLM Provider."""

from __future__ import annotations

import os
from typing import Any

from app.llm.base import LLMProvider
from app.llm.mock_provider import MockProvider


DEFAULT_PROVIDER_NAME = "mock"


class LLMFactory:
    """สร้าง LLM Provider จากชื่อหรือ Environment Variable."""

    _ALIASES: dict[str, str] = {
        "mock": "mock",
        "test": "mock",
        "development": "mock",
        "dev": "mock",
        "openai": "openai",
        "open-ai": "openai",
    }

    @classmethod
    def create(
        cls,
        provider_name: str | None = None,
        **provider_options: Any,
    ) -> LLMProvider:
        """
        สร้าง Provider ตามชื่อที่กำหนด.

        ถ้าไม่ระบุชื่อ จะอ่านจาก LLM_PROVIDER
        และใช้ mock เป็นค่าเริ่มต้น
        """

        resolved_name = cls.resolve_provider_name(
            provider_name
        )

        if resolved_name == "mock":
            return MockProvider(
                **provider_options
            )

        if resolved_name == "openai":
            from app.llm.openai_provider import (
                OpenAIProvider,
            )

            return OpenAIProvider(
                **provider_options
            )

        raise ValueError(
            "ไม่รองรับ LLM Provider: "
            f"{resolved_name!r}"
        )

    @classmethod
    def resolve_provider_name(
        cls,
        provider_name: str | None = None,
    ) -> str:
        """คืนชื่อ Provider มาตรฐาน."""

        raw_name = (
            provider_name
            if provider_name is not None
            else os.getenv(
                "LLM_PROVIDER",
                DEFAULT_PROVIDER_NAME,
            )
        )

        normalized_name = (
            str(raw_name)
            .strip()
            .lower()
        )

        if not normalized_name:
            normalized_name = (
                DEFAULT_PROVIDER_NAME
            )

        return cls._ALIASES.get(
            normalized_name,
            normalized_name,
        )

    @classmethod
    def supported_providers(
        cls,
    ) -> tuple[str, ...]:
        """คืนรายชื่อ Provider ที่สร้างได้จริง."""

        return (
            "mock",
            "openai",
        )

    @classmethod
    def is_supported(
        cls,
        provider_name: str,
    ) -> bool:
        """ตรวจว่า Provider รองรับหรือไม่."""

        resolved_name = (
            cls.resolve_provider_name(
                provider_name
            )
        )

        return resolved_name in (
            cls.supported_providers()
        )


def create_llm_provider(
    provider_name: str | None = None,
    **provider_options: Any,
) -> LLMProvider:
    """Shortcut สำหรับสร้าง LLM Provider."""

    return LLMFactory.create(
        provider_name,
        **provider_options,
    )


def main() -> None:
    """ทดสอบ Factory แบบ Command Line."""

    provider = LLMFactory.create()

    print("=" * 60)
    print("LLM Factory")
    print("=" * 60)
    print(
        f"Provider: {provider.provider_name}"
    )
    print(
        f"Default model: {provider.default_model}"
    )
    print(
        "Supported: "
        f"{LLMFactory.supported_providers()}"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
