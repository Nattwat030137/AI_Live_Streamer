"""ระบบเก็บความจำบทสนทนาระยะสั้น."""

from typing import Literal, TypedDict


Role = Literal["user", "assistant"]


class ChatMessage(TypedDict):
    """รูปแบบข้อมูลข้อความหนึ่งรายการ."""

    role: Role
    content: str


class ConversationMemory:
    """เก็บข้อความล่าสุดของผู้ใช้และ AI ไว้ในหน่วยความจำ."""

    def __init__(self, max_messages: int = 10) -> None:
        """กำหนดจำนวนข้อความสูงสุดที่ต้องการจดจำ."""

        if max_messages < 2:
            raise ValueError(
                "max_messages ต้องมีค่าอย่างน้อย 2"
            )

        self.max_messages = max_messages
        self.messages: list[ChatMessage] = []

    def add_message(
        self,
        role: Role,
        content: str,
    ) -> None:
        """เพิ่มข้อความใหม่เข้าสู่ความจำ."""

        cleaned_content = content.strip()

        if not cleaned_content:
            return

        self.messages.append(
            {
                "role": role,
                "content": cleaned_content,
            }
        )

        # เก็บเฉพาะข้อความล่าสุดตามจำนวนที่กำหนด
        self.messages = self.messages[
            -self.max_messages:
        ]

    def add_user_message(self, content: str) -> None:
        """เพิ่มข้อความของผู้ใช้."""

        self.add_message(
            role="user",
            content=content,
        )

    def add_assistant_message(self, content: str) -> None:
        """เพิ่มคำตอบของ AI."""

        self.add_message(
            role="assistant",
            content=content,
        )

    def get_messages(self) -> list[ChatMessage]:
        """คืนสำเนารายการข้อความทั้งหมด."""

        return self.messages.copy()

    def clear(self) -> None:
        """ล้างความจำบทสนทนาทั้งหมด."""

        self.messages.clear()

    def __len__(self) -> int:
        """คืนจำนวนข้อความที่อยู่ในความจำ."""

        return len(self.messages)