"""ทดสอบ OpenAI Client Wrapper โดยไม่ยิง API จริง."""

from types import SimpleNamespace
from typing import Any

from app.core.openai_client import (
    AIResponseClient,
    DEFAULT_FALLBACK_ANSWER,
    extract_output_text,
    generate_response,
    normalize_conversation,
)


class FakeResponsesAPI:
    """จำลอง Responses API."""

    def __init__(
        self,
        output_text: str,
    ) -> None:
        self.output_text = output_text
        self.calls: list[
            dict[str, Any]
        ] = []

    def create(
        self,
        *,
        model: str,
        instructions: str,
        input: Any,
    ) -> Any:
        """บันทึก Arguments และคืน Response จำลอง."""

        self.calls.append(
            {
                "model": model,
                "instructions": (
                    instructions
                ),
                "input": input,
            }
        )

        return SimpleNamespace(
            output_text=self.output_text
        )


class FakeOpenAIClient:
    """จำลอง OpenAI Client."""

    def __init__(
        self,
        output_text: str,
    ) -> None:
        self.responses = FakeResponsesAPI(
            output_text=output_text
        )


def main() -> None:
    """ตรวจ Wrapper โดยไม่เชื่อมต่ออินเทอร์เน็ต."""

    normalized = normalize_conversation(
        [
            {
                "role": "user",
                "content": (
                    "  มีถ้วยคัพเค้กไหม  "
                ),
            },
            {
                "role": "assistant",
                "content": (
                    " มีค่ะ "
                ),
            },
            {
                "role": "invalid",
                "content": "ตัดออก",
            },
            {
                "role": "user",
                "content": "   ",
            },
        ]
    )

    assert normalized == [
        {
            "role": "user",
            "content": (
                "มีถ้วยคัพเค้กไหม"
            ),
        },
        {
            "role": "assistant",
            "content": "มีค่ะ",
        },
    ]

    fake_client = FakeOpenAIClient(
        output_text=(
            "มีค่ะ รุ่น 5040 "
            "มีสีขาวและน้ำตาลค่ะ"
        )
    )

    answer = generate_response(
        client=fake_client,
        instructions=(
            "ตอบเหมือนพนักงานขาย"
        ),
        conversation=[
            {
                "role": "user",
                "content": (
                    "มีรุ่น 5040 ไหม"
                ),
            }
        ],
        model="test-model",
    )

    assert answer == (
        "มีค่ะ รุ่น 5040 "
        "มีสีขาวและน้ำตาลค่ะ"
    )

    assert len(
        fake_client.responses.calls
    ) == 1

    api_call = (
        fake_client.responses.calls[0]
    )

    assert api_call[
        "model"
    ] == "test-model"

    assert api_call[
        "instructions"
    ] == "ตอบเหมือนพนักงานขาย"

    assert api_call[
        "input"
    ][0]["role"] == "user"

    empty_response = SimpleNamespace(
        output_text="   "
    )

    assert extract_output_text(
        empty_response
    ) == DEFAULT_FALLBACK_ANSWER

    facade_client = FakeOpenAIClient(
        output_text="ทดสอบสำเร็จค่ะ"
    )

    response_client = AIResponseClient(
        client=facade_client,
        model="test-model",
    )

    facade_answer = (
        response_client.generate(
            instructions=(
                "ตอบสั้นและสุภาพ"
            ),
            conversation=[
                {
                    "role": "user",
                    "content": (
                        "สอบถามสินค้า"
                    ),
                }
            ],
        )
    )

    assert facade_answer == (
        "ทดสอบสำเร็จค่ะ"
    )

    try:
        generate_response(
            client=fake_client,
            instructions="",
            conversation=[
                {
                    "role": "user",
                    "content": "ทดสอบ",
                }
            ],
        )

    except ValueError as error:
        assert "instructions" in str(
            error
        )

    else:
        raise AssertionError(
            "ควรเกิด ValueError "
            "เมื่อ instructions ว่าง"
        )

    print("=" * 60)
    print(
        "OpenAI Client Wrapper "
        "ผ่านการทดสอบทั้งหมด"
    )
    print("=" * 60)

    print(
        "คำตอบจำลอง:",
        answer,
    )

    print(
        "จำนวน API Call จำลอง:",
        len(
            fake_client.responses.calls
        ),
    )

    print("=" * 60)


if __name__ == "__main__":
    main()