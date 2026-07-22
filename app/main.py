"""Console entry point for AI Live Streamer."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable

from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    RateLimitError,
)

from app.live_controller import LiveCommerceController
from app.runtime_config import (
    RuntimeStatus,
    inspect_runtime_config,
)

from core.logger import logger


InputCallback = Callable[[str], str]
OutputCallback = Callable[[str], None]


def display_runtime_status_json(
    status: RuntimeStatus,
    *,
    output_callback: OutputCallback = print,
) -> None:
    """Display machine-readable runtime readiness."""

    status_data = {
        "ready": status.ready,
        "provider": status.provider_name,
        "voice_enabled": status.voice_enabled,
        "api_key_configured": (
            status.api_key_configured
        ),
        "product_database_exists": (
            status.product_database_exists
        ),
        "audio_directory_exists": (
            status.audio_directory_exists
        ),
        "errors": list(status.errors),
        "warnings": list(status.warnings),
    }

    output_callback(
        json.dumps(
            status_data,
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def display_runtime_status(
    status: RuntimeStatus,
    *,
    output_callback: OutputCallback = print,
) -> None:
    """Display runtime readiness without exposing secrets."""

    output_callback(
        f"LLM provider: {status.provider_name}"
    )
    output_callback(
        "Voice: "
        + (
            "enabled"
            if status.voice_enabled
            else "disabled"
        )
    )
    output_callback(
        "API key: "
        + (
            "configured"
            if status.api_key_configured
            else "missing"
        )
    )
    output_callback(
        "Product database: "
        + (
            "ready"
            if status.product_database_exists
            else "missing"
        )
    )

    for warning in status.warnings:
        output_callback(
            f"Warning: {warning}"
        )

    for error in status.errors:
        output_callback(
            f"Error: {error}"
        )


def resolve_voice_enabled(
    value: str | None = None,
) -> bool:
    """Resolve whether live voice output is enabled."""

    raw_value = (
        value
        if value is not None
        else os.getenv(
            "VOICE_ENABLED",
            "true",
        )
    )

    return raw_value.strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def create_live_controller(
    *,
    provider_name: str | None = None,
    voice_enabled: bool | None = None,
) -> LiveCommerceController:
    """Create the controller used by the console entry point."""

    resolved_voice_enabled = (
        resolve_voice_enabled()
        if voice_enabled is None
        else voice_enabled
    )

    voice_callback = None

    if resolved_voice_enabled:
        from app.voice_engine import speak

        voice_callback = speak

    return LiveCommerceController(
        provider_name=provider_name,
        voice_callback=voice_callback,
    )


def run_console(
    controller: LiveCommerceController,
    *,
    input_callback: InputCallback = input,
    output_callback: OutputCallback = print,
) -> None:
    """Run the interactive console with injectable input and output."""

    logger.info("เริ่มต้นโปรแกรม AI Live Streamer")

    output_callback("")
    output_callback("พิมพ์ข้อความเพื่อคุยกับ AI")
    output_callback(
        "AI จะตอบข้อความและพูดคำตอบอัตโนมัติ"
    )
    output_callback("พิมพ์ exit เพื่อปิดโปรแกรม")
    output_callback("")

    while True:
        try:
            user_message = input_callback(
                "คุณ: "
            ).strip()
        except (
            EOFError,
            KeyboardInterrupt,
        ):
            output_callback("")
            logger.info("ปิดโปรแกรม")
            break

        if user_message.lower() in {
            "exit",
            "quit",
            "q",
        }:
            logger.info("ปิดโปรแกรม")
            output_callback(
                "AI: ขอบคุณค่ะ แล้วพบกันใหม่"
            )
            break

        if not user_message:
            output_callback(
                "AI: กรุณาพิมพ์ข้อความก่อนนะคะ"
            )
            continue

        try:
            output_callback("AI กำลังคิด...")

            response = controller.process_message(
                user_message,
                platform="shopee",
            )

            output_callback(
                f"AI: {response.text}"
            )
            output_callback("")

        except AuthenticationError:
            logger.error("API Key ไม่ถูกต้อง")
            output_callback(
                "เกิดข้อผิดพลาด: API Key ไม่ถูกต้อง"
            )
            break

        except RateLimitError:
            logger.error(
                "เครดิตหรือขีดจำกัด API ไม่เพียงพอ"
            )
            output_callback(
                "เกิดข้อผิดพลาด: "
                "กรุณาตรวจสอบเครดิตและ Usage Limit"
            )
            break

        except APIConnectionError:
            logger.error(
                "ไม่สามารถเชื่อมต่อ OpenAI ได้"
            )
            output_callback(
                "เกิดข้อผิดพลาด: "
                "กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต"
            )
            break

        except APIStatusError as error:
            logger.error(
                "OpenAI API Error: %s",
                error.status_code,
            )
            output_callback(
                "เกิดข้อผิดพลาดจาก OpenAI API "
                f"รหัส {error.status_code}"
            )
            break

        except Exception as error:
            logger.exception(
                "เกิดข้อผิดพลาดระหว่างการทำงาน: %s",
                error,
            )
            output_callback(
                f"เกิดข้อผิดพลาด: {error}"
            )


def main(
    argv: list[str] | None = None,
    *,
    output_callback: OutputCallback = print,
) -> int:
    """Validate configuration and run the requested mode."""

    arguments = (
        list(argv)
        if argv is not None
        else sys.argv[1:]
    )

    runtime_status = inspect_runtime_config()

    if "--check-json" in arguments:
        display_runtime_status_json(
            runtime_status,
            output_callback=output_callback,
        )
        return 0 if runtime_status.ready else 1

    display_runtime_status(
        runtime_status,
        output_callback=output_callback,
    )

    if not runtime_status.ready:
        logger.error(
            "Runtime configuration is not ready"
        )
        return 1

    if "--check" in arguments:
        return 0

    controller = create_live_controller(
        provider_name=(
            runtime_status.provider_name
        ),
        voice_enabled=(
            runtime_status.voice_enabled
        ),
    )
    run_console(
        controller,
        output_callback=output_callback,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
