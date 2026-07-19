from __future__ import annotations

from typing import Optional

from app.memory.conversation import ConversationMemory


REFERENCE_KEYWORDS = {
    "ใช้ถุง",
    "ถุง",
    "สี",
    "วัสดุ",
    "ราคา",
    "โปร",
    "โปรโมชั่น",
    "ส่ง",
    "ค่าส่ง",
    "สต๊อก",
    "สต็อก",
    "มีไหม",
    "ขนาด",
}


def resolve_reference(
    message: str,
    memory: ConversationMemory,
) -> Optional[str]:
    """
    ถ้าข้อความไม่มีรหัสสินค้า
    แต่เป็นคำถามต่อเนื่อง
    ให้คืน model ล่าสุด
    """

    models = memory.active_models

    if not models:
        return None

    if any(ch.isdigit() for ch in message):
        return None

    lowered = message.lower()

    for keyword in REFERENCE_KEYWORDS:
        if keyword.lower() in lowered:
            return models[0]

    return None