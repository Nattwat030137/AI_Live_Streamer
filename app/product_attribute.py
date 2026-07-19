"""Product Attribute Classifier สำหรับ AI Commerce OS."""

from __future__ import annotations

from enum import Enum


class ProductAttribute(str, Enum):
    GENERAL = "general"
    COLOR = "color"
    MATERIAL = "material"
    BAG = "bag"
    CATEGORY = "category"
    NAME = "name"
    NOTE = "note"


ATTRIBUTE_KEYWORDS = {
    ProductAttribute.COLOR: [
        "สี",
        "สีอะไร",
        "สีไหน",
    ],
    ProductAttribute.MATERIAL: [
        "วัสดุ",
        "ทำจาก",
        "ผลิตจาก",
    ],
    ProductAttribute.BAG: [
        "ใช้ถุง",
        "ถุงอะไร",
        "ขนาดถุง",
        "ซีลถุง",
    ],
    ProductAttribute.CATEGORY: [
        "หมวด",
        "ประเภท",
        "หมวดสินค้า",
    ],
    ProductAttribute.NAME: [
        "ชื่อ",
        "ชื่อเต็ม",
    ],
    ProductAttribute.NOTE: [
        "หมายเหตุ",
        "ข้อควรระวัง",
        "คำแนะนำ",
    ],
}


def detect_product_attribute(
    message: str,
) -> ProductAttribute:
    """ตรวจสอบว่าลูกค้าถามคุณสมบัติสินค้าอะไร"""

    text = message.lower().strip()

    for attribute, keywords in ATTRIBUTE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return attribute

    return ProductAttribute.GENERAL

