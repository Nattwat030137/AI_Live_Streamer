"""Intent Engine สำหรับจำแนกประเภทคำถามของลูกค้า."""

from __future__ import annotations

from enum import Enum


class Intent(str, Enum):
    PRODUCT = "product"
    PRICE = "price"
    STOCK = "stock"
    SHIPPING = "shipping"
    STORE = "store"
    CATEGORY = "category"
    GENERAL = "general"


INTENT_KEYWORDS = {
    Intent.PRICE: [
        "ราคา",
        "เท่าไร",
        "เท่าไหร่",
        "กี่บาท",
        "บาท",
    ],
    Intent.STOCK: [
        "มีของไหม",
        "มีของมั้ย",
        "สต๊อก",
        "สต็อก",
        "เหลือไหม",
        "พร้อมส่ง",
        "ของหมด",
    ],
    Intent.SHIPPING: [
        "ส่ง",
        "ขนส่ง",
        "จัดส่ง",
        "ค่าส่ง",
        "flash",
        "spx",
        "j&t",
        "lex",
    ],
    Intent.STORE: [
        "หน้าร้าน",
        "รับเอง",
        "เปิดกี่โมง",
        "ปิดกี่โมง",
        "ที่อยู่",
        "แผนที่",
    ],
    Intent.CATEGORY: [
        "มีหมวด",
        "หมวด",
        "ประเภทสินค้า",
        "ขายอะไร",
    ],
}


def detect_intent(message: str) -> Intent:
    """
    วิเคราะห์ Intent ของข้อความลูกค้า
    """

    text = message.lower().strip()

    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return intent

    return Intent.PRODUCT