"""จัดเก็บและเติมบริบทสินค้าให้บทสนทนาต่อเนื่อง."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.search_executor import SearchExecutionResult


FOLLOW_UP_WORDS = (
    "แล้ว",
    "ล่ะ",
    "ละ",
    "ราคา",
    "เท่าไร",
    "เท่าไหร่",
    "มีของไหม",
    "มีของมั้ย",
    "มีสี",
    "สีอะไร",
    "สีขาว",
    "สีน้ำตาล",
    "เคลือบ",
    "ไม่เคลือบ",
    "แบบไหน",
    "ขนาดไหน",
    "กี่ใบ",
    "กี่ชิ้น",
    "รุ่นเดิม",
    "อันเดิม",
    "ตัวเดิม",
)


@dataclass(slots=True)
class ConversationContext:
    """บริบทสินค้าล่าสุดของบทสนทนา."""

    last_user_message: str = ""
    last_model: str = ""
    last_product_name: str = ""
    last_keywords: list[str] = field(
        default_factory=list
    )
    last_summary: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def has_product_context(self) -> bool:
        """คืน True เมื่อมีข้อมูลสินค้าเดิมให้ใช้อ้างอิง."""

        return bool(
            self.last_model
            or self.last_product_name
            or self.last_keywords
        )

    def clear(self) -> None:
        """ล้างบริบททั้งหมด."""

        self.last_user_message = ""
        self.last_model = ""
        self.last_product_name = ""
        self.last_keywords.clear()
        self.last_summary.clear()


def is_follow_up_message(
    message: str,
) -> bool:
    """ตรวจว่าข้อความมีลักษณะเป็นคำถามต่อเนื่องหรือไม่."""

    cleaned_message = message.strip()

    if not cleaned_message:
        return False

    if any(
        word in cleaned_message
        for word in FOLLOW_UP_WORDS
    ):
        return True

    # ข้อความสั้นมักเป็นคำถามต่อจากข้อความก่อนหน้า
    return len(cleaned_message) <= 18


def get_context_reference(
    context: ConversationContext,
) -> str:
    """สร้างข้อความอ้างอิงสินค้าจากบริบทล่าสุด."""

    if context.last_model:
        return f"รุ่น {context.last_model}"

    if context.last_product_name:
        return context.last_product_name

    if context.last_keywords:
        return context.last_keywords[0]

    return ""


def enrich_message(
    message: str,
    context: ConversationContext,
) -> str:
    """เติมบริบทสินค้าเดิมให้ข้อความคำถามต่อเนื่อง."""

    cleaned_message = message.strip()

    if not cleaned_message:
        return ""

    if not context.has_product_context:
        return cleaned_message

    if not is_follow_up_message(
        cleaned_message
    ):
        return cleaned_message

    reference = get_context_reference(
        context
    )

    if not reference:
        return cleaned_message

    # ไม่เติมซ้ำ หากข้อความระบุรุ่นหรือสินค้าเดิมอยู่แล้ว
    if reference in cleaned_message:
        return cleaned_message

    return (
        f"{reference} "
        f"{cleaned_message}"
    )


def extract_first_product_name(
    products: list[dict[str, Any]],
) -> str:
    """ดึงชื่อสินค้ารายการแรกจากผลค้นหา."""

    if not products:
        return ""

    return str(
        products[0].get(
            "product_name",
            "",
        )
    ).strip()


def update_context(
    context: ConversationContext,
    user_message: str,
    search_result: SearchExecutionResult,
) -> None:
    """อัปเดตบริบทจากผลการค้นหาล่าสุด."""

    context.last_user_message = (
        user_message.strip()
    )

    model = str(
        search_result.summary.get(
            "model",
            "",
        )
        or ""
    ).strip()

    if model:
        context.last_model = model

    product_name = (
        extract_first_product_name(
            search_result.products
        )
    )

    if product_name:
        context.last_product_name = (
            product_name
        )

    if search_result.searched_keywords:
        context.last_keywords = list(
            search_result.searched_keywords
        )

    if search_result.summary:
        context.last_summary = dict(
            search_result.summary
        )


class ContextEngine:
    """Facade สำหรับบริหารบริบทบทสนทนา."""

    def __init__(
        self,
        context: ConversationContext | None = None,
    ) -> None:
        self.context = (
            context
            if context is not None
            else ConversationContext()
        )

    def enrich(
        self,
        message: str,
    ) -> str:
        """เติมบริบทให้ข้อความลูกค้า."""

        return enrich_message(
            message=message,
            context=self.context,
        )

    def update(
        self,
        user_message: str,
        search_result: SearchExecutionResult,
    ) -> None:
        """บันทึกบริบทจากผลค้นหาล่าสุด."""

        update_context(
            context=self.context,
            user_message=user_message,
            search_result=search_result,
        )

    def clear(self) -> None:
        """ล้างบริบทสินค้า."""

        self.context.clear()