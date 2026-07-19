"""Recommendation Engine สำหรับสร้างคำค้นสินค้าที่เกี่ยวข้อง."""

from __future__ import annotations

import re
from typing import Any

from app.knowledge_engine import load_all_knowledge


STOP_WORDS = {
    "หรือเปล่า",
    "ราคาเท่าไหร่",
    "ราคาเท่าไร",
    "มีของไหม",
    "มีสต็อกไหม",
    "มีสต๊อกไหม",
    "ช่วยแนะนำ",
    "อยากได้",
    "ต้องการ",
    "เท่าไหร่",
    "เท่าไร",
    "ทางร้าน",
    "สินค้า",
    "ราคา",
    "มี",
    "ไหม",
    "มั้ย",
    "หรือ",
    "ครับ",
    "ค่ะ",
    "คะ",
    "นะคะ",
    "นะ",
    "ขอ",
    "หน่อย",
    "ช่วย",
}


def normalize_text(text: str) -> str:
    """ปรับข้อความให้อยู่ในรูปแบบเดียวกัน."""

    normalized_text = text.lower().strip()

    normalized_text = re.sub(
        r"""[?!.,:;'"()[\]{}<>/\\]""",
        " ",
        normalized_text,
    )

    normalized_text = re.sub(
        r"\s+",
        " ",
        normalized_text,
    )

    return normalized_text.strip()


def remove_stop_words(text: str) -> str:
    """ลบคำทั่วไปออกจากประโยคภาษาไทย."""

    cleaned_text = text

    for word in sorted(
        STOP_WORDS,
        key=len,
        reverse=True,
    ):
        cleaned_text = cleaned_text.replace(
            word,
            " ",
        )

    cleaned_text = re.sub(
        r"\s+",
        " ",
        cleaned_text,
    )

    return cleaned_text.strip()


def extract_keywords(message: str) -> list[str]:
    """ดึงคำค้นหลักจากข้อความของลูกค้า."""

    normalized_message = normalize_text(
        message
    )

    cleaned_message = remove_stop_words(
        normalized_message
    )

    if not cleaned_message:
        return []

    keywords: list[str] = []

    # เก็บประโยคที่ทำความสะอาดแล้วเป็นคำค้นหลัก
    keywords.append(cleaned_message)

    # หากมีช่องว่าง ให้เก็บคำย่อยไว้ค้นเพิ่มเติม
    for word in cleaned_message.split():
        cleaned_word = word.strip()

        if len(cleaned_word) < 2:
            continue

        if cleaned_word not in keywords:
            keywords.append(cleaned_word)

    return keywords


def get_category_names() -> list[str]:
    """อ่านรายชื่อหมวดสินค้าจากฐานความรู้."""

    knowledge = load_all_knowledge()

    categories_data: Any = knowledge.get(
        "categories",
        {},
    )

    if not isinstance(categories_data, dict):
        return []

    categories = categories_data.get(
        "categories",
        [],
    )

    if not isinstance(categories, list):
        return []

    return [
        str(category).strip()
        for category in categories
        if str(category).strip()
    ]


def expand_keywords(
    keywords: list[str],
) -> list[str]:
    """ขยายคำค้นด้วยชื่อหมวดสินค้าที่เกี่ยวข้อง."""

    expanded_keywords = list(keywords)
    category_names = get_category_names()

    for keyword in keywords:
        for category_name in category_names:
            if (
                keyword in category_name
                or category_name in keyword
            ):
                if category_name not in expanded_keywords:
                    expanded_keywords.append(
                        category_name
                    )

    return expanded_keywords


def build_search_keywords(
    message: str,
) -> list[str]:
    """สร้างรายการคำค้นหลักและคำค้นเพิ่มเติม."""

    keywords = extract_keywords(
        message
    )

    return expand_keywords(
        keywords
    )