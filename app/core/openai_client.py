"""ตัวเชื่อมต่อ OpenAI สำหรับ AI Engine."""

from __future__ import annotations

from typing import Any, Protocol

from openai import OpenAI

from config.settings import OPENAI_API_KEY


DEFAULT_AI_MODEL = "gpt-5-mini"
DEFAULT_FALLBACK_ANSWER = (
    "ขออนุญาตให้แอดมินตรวจสอบข้อมูลให้ค่ะ"
)


class ResponsesAPIProtocol(Protocol):
    """รูปแบบขั้นต่ำของ Responses API ที่ระบบต้องใช้."""

    def create(
        self,
        *,
        model: str,
        instructions: str,
        input: Any,
    ) -> Any:
        """สร้างคำตอบจากโมเดล."""


class OpenAIClientProtocol(Protocol):
    """รูปแบบขั้นต่ำของ OpenAI Client."""

    responses: ResponsesAPIProtocol


def create_openai_client(
    api_key: str | None = None,
) -> OpenAI:
    """สร้าง OpenAI Client จาก API Key."""

    selected_api_key = (
        api_key
        if api_key is not None
        else OPENAI_API_KEY
    )

    if not selected_api_key:
        raise ValueError(
            "ไม่พบ OPENAI_API_KEY "
            "กรุณาตรวจสอบไฟล์ .env"
        )

    return OpenAI(
        api_key=selected_api_key
    )


def normalize_conversation(
    messages: list[dict[str, str]],
) -> list[dict[str, str]]:
    """ตรวจและทำความสะอาดรายการข้อความก่อนส่ง API."""

    normalized_messages: list[
        dict[str, str]
    ] = []

    allowed_roles = {
        "user",
        "assistant",
        "system",
        "developer",
    }

    for message in messages:
        if not isinstance(
            message,
            dict,
        ):
            continue

        role = str(
            message.get(
                "role",
                "",
            )
        ).strip()

        content = str(
            message.get(
                "content",
                "",
            )
        ).strip()

        if role not in allowed_roles:
            continue

        if not content:
            continue

        normalized_messages.append(
            {
                "role": role,
                "content": content,
            }
        )

    return normalized_messages


def extract_output_text(
    response: Any,
    fallback_answer: str = (
        DEFAULT_FALLBACK_ANSWER
    ),
) -> str:
    """อ่านข้อความจาก Response และใช้ข้อความสำรองเมื่อว่าง."""

    output_text = str(
        getattr(
            response,
            "output_text",
            "",
        )
        or ""
    ).strip()

    if output_text:
        return output_text

    return fallback_answer


def generate_response(
    *,
    client: OpenAIClientProtocol,
    instructions: str,
    conversation: list[dict[str, str]],
    model: str = DEFAULT_AI_MODEL,
    fallback_answer: str = (
        DEFAULT_FALLBACK_ANSWER
    ),
) -> str:
    """ส่ง Prompt และบทสนทนาไปยัง Responses API."""

    cleaned_instructions = (
        instructions.strip()
    )

    if not cleaned_instructions:
        raise ValueError(
            "instructions ต้องไม่เป็นข้อความว่าง"
        )

    cleaned_model = model.strip()

    if not cleaned_model:
        raise ValueError(
            "model ต้องไม่เป็นข้อความว่าง"
        )

    normalized_conversation = (
        normalize_conversation(
            conversation
        )
    )

    if not normalized_conversation:
        raise ValueError(
            "conversation ต้องมีข้อความ"
            "อย่างน้อยหนึ่งรายการ"
        )

    response = client.responses.create(
        model=cleaned_model,
        instructions=cleaned_instructions,
        input=normalized_conversation,
    )

    return extract_output_text(
        response=response,
        fallback_answer=fallback_answer,
    )


class AIResponseClient:
    """Facade สำหรับสร้างคำตอบจาก OpenAI."""

    def __init__(
        self,
        client: OpenAIClientProtocol | None = None,
        model: str = DEFAULT_AI_MODEL,
        fallback_answer: str = (
            DEFAULT_FALLBACK_ANSWER
        ),
    ) -> None:
        self._client = client
        self.model = model
        self.fallback_answer = (
            fallback_answer
        )

    @property
    def client(
        self,
    ) -> OpenAIClientProtocol:
        """คืน Client และสร้างเมื่อถูกเรียกครั้งแรก."""

        if self._client is None:
            self._client = (
                create_openai_client()
            )

        return self._client

    def generate(
        self,
        *,
        instructions: str,
        conversation: list[
            dict[str, str]
        ],
    ) -> str:
        """สร้างคำตอบจาก Prompt และ Conversation."""

        return generate_response(
            client=self.client,
            instructions=instructions,
            conversation=conversation,
            model=self.model,
            fallback_answer=(
                self.fallback_answer
            ),
        )