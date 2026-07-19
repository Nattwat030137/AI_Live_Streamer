"""จุดเริ่มต้นของโปรแกรม AI Live Streamer."""

from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    RateLimitError,
)

from app.ai_engine import ask_ai
from app.voice_engine import speak
from core.logger import logger


def main() -> None:
    """รับคำถาม แสดงคำตอบ และพูดคำตอบออกลำโพง."""

    logger.info("โปรแกรม AI Live Streamer เริ่มทำงาน")

    print()
    print("พิมพ์ข้อความเพื่อคุยกับ AI")
    print("AI จะตอบเป็นข้อความและพูดออกลำโพงอัตโนมัติ")
    print("พิมพ์ exit เพื่อปิดโปรแกรม")
    print()

    while True:
        user_message = input("คุณ: ").strip()

        if user_message.lower() == "exit":
            logger.info("ปิดโปรแกรม")
            print("AI: ขอบคุณค่ะ แล้วพบกันใหม่")
            break

        if not user_message:
            print("AI: กรุณาพิมพ์ข้อความก่อนนะคะ")
            continue

        try:
            print("AI กำลังคิด...")

            answer = ask_ai(user_message)

            print(f"AI: {answer}")
            print("AI กำลังพูด...")

            # voice_engine.py จะจัดการ Log ของระบบเสียงเอง
            speak(answer)

            print()

        except AuthenticationError:
            logger.error("API Key ไม่ถูกต้อง")
            print("เกิดข้อผิดพลาด: API Key ไม่ถูกต้อง")
            break

        except RateLimitError:
            logger.error("เครดิตหรือขีดจำกัด API ไม่เพียงพอ")
            print(
                "เกิดข้อผิดพลาด: "
                "กรุณาตรวจสอบเครดิตและ Usage Limit"
            )
            break

        except APIConnectionError:
            logger.error("ไม่สามารถเชื่อมต่อ OpenAI ได้")
            print(
                "เกิดข้อผิดพลาด: "
                "กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต"
            )
            break

        except APIStatusError as error:
            logger.error(
                "OpenAI API Error: %s",
                error.status_code,
            )
            print(
                "เกิดข้อผิดพลาดจาก OpenAI API "
                f"รหัส {error.status_code}"
            )
            break

        except Exception as error:
            logger.exception(
                "เกิดข้อผิดพลาดระหว่างการทำงาน: %s",
                error,
            )
            print(f"เกิดข้อผิดพลาด: {error}")


if __name__ == "__main__":
    main()