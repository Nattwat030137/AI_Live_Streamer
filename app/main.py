"""Console entry point for AI Live Streamer."""

from __future__ import annotations

from collections.abc import Callable

from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    RateLimitError,
)

from app.live_controller import LiveCommerceController

from core.logger import logger


InputCallback = Callable[[str], str]
OutputCallback = Callable[[str], None]


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


def main() -> None:
    """Create production dependencies and run the console."""

    from app.voice_engine import speak

    controller = LiveCommerceController(
        voice_callback=speak,
    )
    run_console(controller)


if __name__ == "__main__":
    main()