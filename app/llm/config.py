"""Configuration สำหรับ LLM Provider Layer."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


DEFAULT_LLM_PROVIDER = "mock"
DEFAULT_OPENAI_MODEL = "gpt-5-mini"
DEFAULT_OPENAI_TIMEOUT_SECONDS = 30.0
DEFAULT_OPENAI_MAX_OUTPUT_TOKENS = 500


def _read_text(
    name: str,
    default: str = "",
) -> str:
    """อ่าน Environment Variable เป็นข้อความ."""

    return os.getenv(
        name,
        default,
    ).strip()


def _read_optional_float(
    name: str,
) -> float | None:
    """อ่าน Environment Variable เป็น float หรือ None."""

    raw_value = _read_text(
        name
    )

    if not raw_value:
        return None

    try:
        return float(
            raw_value
        )
    except ValueError as error:
        raise ValueError(
            f"{name} ต้องเป็นตัวเลข"
        ) from error


def _read_positive_float(
    name: str,
    default: float,
) -> float:
    """อ่าน Environment Variable เป็น float ค่าบวก."""

    raw_value = _read_text(
        name
    )

    value = (
        default
        if not raw_value
        else float(raw_value)
    )

    if value <= 0:
        raise ValueError(
            f"{name} ต้องมากกว่า 0"
        )

    return value


def _read_positive_int(
    name: str,
    default: int,
) -> int:
    """อ่าน Environment Variable เป็น int ค่าบวก."""

    raw_value = _read_text(
        name
    )

    value = (
        default
        if not raw_value
        else int(raw_value)
    )

    if value <= 0:
        raise ValueError(
            f"{name} ต้องมากกว่า 0"
        )

    return value


@dataclass(frozen=True, slots=True)
class LLMConfig:
    """ค่าตั้งต้นของ LLM Provider Layer."""

    provider: str = DEFAULT_LLM_PROVIDER
    openai_api_key: str = ""
    openai_model: str = DEFAULT_OPENAI_MODEL
    openai_timeout_seconds: float = (
        DEFAULT_OPENAI_TIMEOUT_SECONDS
    )
    openai_temperature: float | None = None
    openai_max_output_tokens: int = (
        DEFAULT_OPENAI_MAX_OUTPUT_TOKENS
    )

    def __post_init__(self) -> None:
        """ตรวจสอบค่าพื้นฐาน."""

        normalized_provider = (
            self.provider
            .strip()
            .lower()
        )

        object.__setattr__(
            self,
            "provider",
            normalized_provider
            or DEFAULT_LLM_PROVIDER,
        )

        object.__setattr__(
            self,
            "openai_model",
            self.openai_model.strip()
            or DEFAULT_OPENAI_MODEL,
        )

        if self.openai_timeout_seconds <= 0:
            raise ValueError(
                "openai_timeout_seconds "
                "ต้องมากกว่า 0"
            )

        if self.openai_max_output_tokens <= 0:
            raise ValueError(
                "openai_max_output_tokens "
                "ต้องมากกว่า 0"
            )

        if (
            self.openai_temperature is not None
            and not 0.0
            <= self.openai_temperature
            <= 2.0
        ):
            raise ValueError(
                "openai_temperature "
                "ต้องอยู่ระหว่าง 0.0 ถึง 2.0"
            )

    @classmethod
    def from_environment(
        cls,
    ) -> "LLMConfig":
        """สร้าง Config จาก Environment Variables."""

        return cls(
            provider=_read_text(
                "LLM_PROVIDER",
                DEFAULT_LLM_PROVIDER,
            ),
            openai_api_key=_read_text(
                "OPENAI_API_KEY"
            ),
            openai_model=_read_text(
                "OPENAI_MODEL",
                DEFAULT_OPENAI_MODEL,
            ),
            openai_timeout_seconds=(
                _read_positive_float(
                    "OPENAI_TIMEOUT_SECONDS",
                    DEFAULT_OPENAI_TIMEOUT_SECONDS,
                )
            ),
            openai_temperature=(
                _read_optional_float(
                    "OPENAI_TEMPERATURE"
                )
            ),
            openai_max_output_tokens=(
                _read_positive_int(
                    "OPENAI_MAX_OUTPUT_TOKENS",
                    DEFAULT_OPENAI_MAX_OUTPUT_TOKENS,
                )
            ),
        )

    @property
    def has_openai_api_key(
        self,
    ) -> bool:
        """ตรวจว่ามี OpenAI API Key หรือไม่."""

        return bool(
            self.openai_api_key.strip()
        )

    def require_openai_api_key(
        self,
    ) -> str:
        """คืน API Key หรือเกิด ValueError เมื่อไม่มี."""

        if not self.has_openai_api_key:
            raise ValueError(
                "ไม่พบ OPENAI_API_KEY"
            )

        return self.openai_api_key

    def to_dict(
        self,
        *,
        include_secrets: bool = False,
    ) -> dict[str, Any]:
        """แปลง Config เป็น Dictionary."""

        api_key_value = (
            self.openai_api_key
            if include_secrets
            else (
                "***configured***"
                if self.has_openai_api_key
                else ""
            )
        )

        return {
            "provider": self.provider,
            "openai_api_key": api_key_value,
            "openai_model": self.openai_model,
            "openai_timeout_seconds": (
                self.openai_timeout_seconds
            ),
            "openai_temperature": (
                self.openai_temperature
            ),
            "openai_max_output_tokens": (
                self.openai_max_output_tokens
            ),
            "has_openai_api_key": (
                self.has_openai_api_key
            ),
        }


def load_llm_config() -> LLMConfig:
    """โหลด LLM Config จาก Environment Variables."""

    return LLMConfig.from_environment()


def main() -> None:
    """แสดงค่าตั้งต้นโดยไม่เปิดเผย API Key."""

    config = load_llm_config()

    print("=" * 60)
    print("LLM Configuration")
    print("=" * 60)

    for key, value in config.to_dict().items():
        print(
            f"{key}: {value}"
        )

    print("=" * 60)


if __name__ == "__main__":
    main()
