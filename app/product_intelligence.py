"""สรุปข้อมูลสินค้าจากผลค้นหา เพื่อให้ AI ตอบแบบพนักงานขาย."""

from __future__ import annotations

import re
from typing import Any


COLOR_KEYWORDS = {
    "Brown": "น้ำตาล",
    "White": "ขาว",
    "Black": "ดำ",
    "Red": "แดง",
    "Blue": "น้ำเงิน",
    "Pink": "ชมพู",
    "Green": "เขียว",
    "Yellow": "เหลือง",
    "Purple": "ม่วง",
    "Orange": "ส้ม",
    "Coffee": "กาแฟ",
    "Cream": "ครีม",
    "Clear": "ใส",
    "Transparent": "ใส",
    "Gold": "ทอง",
    "Silver": "เงิน",
}


def extract_model(text: str) -> str | None:
    """ค้นหาเลขรุ่นสินค้าจากข้อความ."""

    match = re.search(
        r"\b(\d{3,6})\b",
        text,
    )

    if match:
        return match.group(1)

    return None


def extract_pack_size(text: str) -> str | None:
    """ค้นหาจำนวนบรรจุต่อแพ็กจากชื่อสินค้า."""

    range_match = re.search(
        r"(\d+)\s*[-–]\s*(\d+)\s*ใบ",
        text,
    )

    if range_match:
        minimum = range_match.group(1)
        maximum = range_match.group(2)

        return f"{minimum}-{maximum} ใบ"

    single_match = re.search(
        r"(?:แพค|แพ็ก|บรรจุ)\s*(?:ละ)?\s*(\d+)\s*ใบ",
        text,
        flags=re.IGNORECASE,
    )

    if single_match:
        quantity = single_match.group(1)

        return f"{quantity} ใบ"

    return None


def extract_colors(text: str) -> set[str]:
    """ค้นหาสีที่ปรากฏในชื่อสินค้า."""

    found_colors: set[str] = set()
    lowered_text = text.lower()

    for english_color, thai_color in COLOR_KEYWORDS.items():
        if english_color.lower() in lowered_text:
            found_colors.add(thai_color)

    return found_colors


def summarize_products(
    products: list[dict[str, Any]],
) -> dict[str, Any]:
    """สรุปรุ่น สี ลักษณะผิว และจำนวนบรรจุของสินค้า."""

    summary: dict[str, Any] = {
        "model": None,
        "colors": [],
        "finish": [],
        "pack_size": None,
        "count": len(products),
    }

    colors: set[str] = set()

    found_uncoated = False
    found_regular = False

    for product in products:
        product_name = str(
            product.get("product_name", "")
        ).strip()

        sku = str(
            product.get("sku", "")
        ).strip()

        combined_text = f"{product_name} {sku}"

        if summary["model"] is None:
            model = extract_model(combined_text)

            if model:
                summary["model"] = model

        if summary["pack_size"] is None:
            pack_size = extract_pack_size(combined_text)

            if pack_size:
                summary["pack_size"] = pack_size

        colors.update(
            extract_colors(combined_text)
        )

        if "ไม่เคลือบ" in combined_text:
            found_uncoated = True
        else:
            found_regular = True

    finish: list[str] = []

    if found_regular:
        finish.append("เคลือบ")

    if found_uncoated:
        finish.append("ไม่เคลือบ")

    summary["colors"] = sorted(colors)
    summary["finish"] = finish

    return summary