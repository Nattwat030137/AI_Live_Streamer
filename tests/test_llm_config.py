"""Regression tests สำหรับ LLMConfig."""

from __future__ import annotations

import os
from contextlib import contextmanager
from collections.abc import Iterator

from app.llm.config import (
    DEFAULT_LLM_PROVIDER,
    DEFAULT_OPENAI_MODEL,
    LLMConfig,
    load_llm_config,
)


@contextmanager
def temporary_environment(
    values: dict[str, str | None],
) -> Iterator[None]:
    """ตั้งค่า Environment หลายรายการชั่วคราว."""

    original_values = {
        key: os.environ.get(
            key
        )
        for key in values
    }

    original_exists = {
        key: key in os.environ
        for key in values
    }

    try:
        for key, value in values.items():
            if value is None:
                os.environ.pop(
                    key,
                    None,
                )
            else:
                os.environ[key] = value

        yield

    finally:
        for key in values:
            if original_exists[key]:
                original_value = (
                    original_values[key]
                )

                assert original_value is not None

                os.environ[key] = (
                    original_value
                )
            else:
                os.environ.pop(
                    key,
                    None,
                )


def main() -> None:
    """รัน Regression Test ของ LLMConfig."""

    print("=" * 60)
    print("LLM Config Regression Test")
    print("=" * 60)

    passed = 0
    total = 7

    with temporary_environment(
        {
            "LLM_PROVIDER": None,
            "OPENAI_API_KEY": None,
            "OPENAI_MODEL": None,
            "OPENAI_TIMEOUT_SECONDS": None,
            "OPENAI_TEMPERATURE": None,
            "OPENAI_MAX_OUTPUT_TOKENS": None,
        }
    ):
        default_config = load_llm_config()

    assert (
        default_config.provider
        == DEFAULT_LLM_PROVIDER
    )
    assert (
        default_config.openai_model
        == DEFAULT_OPENAI_MODEL
    )
    assert (
        default_config.has_openai_api_key
        is False
    )

    passed += 1
    print("Default config......................PASS")

    with temporary_environment(
        {
            "LLM_PROVIDER": "OPENAI",
            "OPENAI_API_KEY": "test-key",
            "OPENAI_MODEL": "test-model",
            "OPENAI_TIMEOUT_SECONDS": "45",
            "OPENAI_TEMPERATURE": "0.3",
            "OPENAI_MAX_OUTPUT_TOKENS": "700",
        }
    ):
        environment_config = (
            load_llm_config()
        )

    assert (
        environment_config.provider
        == "openai"
    )
    assert (
        environment_config.openai_model
        == "test-model"
    )
    assert (
        environment_config
        .openai_timeout_seconds
        == 45.0
    )
    assert (
        environment_config
        .openai_temperature
        == 0.3
    )
    assert (
        environment_config
        .openai_max_output_tokens
        == 700
    )
    assert (
        environment_config.has_openai_api_key
        is True
    )

    passed += 1
    print("Environment config.................PASS")

    masked = environment_config.to_dict()

    assert masked["openai_api_key"] == (
        "***configured***"
    )
    assert (
        "test-key"
        not in str(masked)
    )

    passed += 1
    print("Secret masking.....................PASS")

    unmasked = environment_config.to_dict(
        include_secrets=True
    )

    assert unmasked["openai_api_key"] == (
        "test-key"
    )

    passed += 1
    print("Explicit secret export.............PASS")

    assert (
        environment_config
        .require_openai_api_key()
        == "test-key"
    )

    passed += 1
    print("Require API key....................PASS")

    try:
        default_config.require_openai_api_key()
    except ValueError as error:
        assert "OPENAI_API_KEY" in str(
            error
        )
    else:
        raise AssertionError(
            "Config ที่ไม่มี API Key "
            "ต้องเกิด ValueError"
        )

    passed += 1
    print("Missing API key....................PASS")

    invalid_cases = (
        {
            "openai_timeout_seconds": 0.0,
        },
        {
            "openai_temperature": 3.0,
        },
        {
            "openai_max_output_tokens": 0,
        },
    )

    for overrides in invalid_cases:
        try:
            LLMConfig(
                **overrides
            )
        except ValueError:
            continue

        raise AssertionError(
            f"Config ต้องไม่รับค่า: "
            f"{overrides}"
        )

    passed += 1
    print("Validation.........................PASS")

    print("=" * 60)
    print(
        f"{passed} / {total} PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
