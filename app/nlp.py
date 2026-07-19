"""NLP Core สำหรับ AI Live Streamer."""

from __future__ import annotations

import re
from typing import Iterable


# --------------------------------------------------
# Normalization
# --------------------------------------------------

def normalize_text(text: str) -> str:
    """ทำข้อความให้อยู่ในรูปแบบมาตรฐาน."""

    if text is None:
        return ""

    text = str(text)

    text = text.strip().lower()

    text = text.replace(
        "\n",
        " ",
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text


# --------------------------------------------------
# Duplicate
# --------------------------------------------------

def remove_duplicate(
    values: Iterable[str],
) -> list[str]:
    """ลบข้อมูลซ้ำ โดยคงลำดับเดิม."""

    result: list[str] = []

    seen: set[str] = set()

    for value in values:

        if not value:
            continue

        if value in seen:
            continue

        seen.add(value)

        result.append(value)

    return result


# --------------------------------------------------
# Model
# --------------------------------------------------

_MODEL_PATTERN = re.compile(
    r"(?<!\d)(\d{3,6})(?!\d)"
)


def extract_models(
    text: str,
) -> list[str]:
    """ดึงเลขรุ่นสินค้า."""

    normalized = normalize_text(
        text
    )

    return remove_duplicate(
        _MODEL_PATTERN.findall(
            normalized
        )
    )
# --------------------------------------------------
# Tokenization
# --------------------------------------------------

_THAI_ENGLISH_NUMBER_PATTERN = re.compile(
    r"[ก-๙]+|[a-z]+|\d+(?:[./-]\d+)*",
    flags=re.IGNORECASE,
)


def tokenize(
    text: str,
) -> list[str]:
    """
    แยกข้อความเป็น Token แบบพื้นฐาน

    รองรับ:
    - ภาษาไทย
    - ภาษาอังกฤษ
    - ตัวเลข
    - ตัวเลขที่มี / - .
    """

    normalized = normalize_text(
        text
    )

    if not normalized:
        return []

    tokens = _THAI_ENGLISH_NUMBER_PATTERN.findall(
        normalized
    )

    cleaned_tokens = [
        token.strip()
        for token in tokens
        if token.strip()
    ]

    return remove_duplicate(
        cleaned_tokens
    )


def extract_thai_words(
    text: str,
) -> list[str]:
    """ดึงเฉพาะกลุ่มอักษรภาษาไทยจากข้อความ."""

    normalized = normalize_text(
        text
    )

    thai_words = re.findall(
        r"[ก-๙]+",
        normalized,
    )

    return remove_duplicate(
        thai_words
    )


# --------------------------------------------------
# Whole word matching
# --------------------------------------------------

def contains_whole_word(
    text: str,
    keyword: str,
) -> bool:
    """
    ตรวจว่าข้อความมี Keyword แบบคำเต็มหรือไม่

    ป้องกันกรณี:
    ใส่เค้กวันเกิด
    ไม่ควรตรงกับ
    ใส
    """

    normalized_text = normalize_text(
        text
    )

    normalized_keyword = normalize_text(
        keyword
    )

    if not normalized_text or not normalized_keyword:
        return False

    if normalized_text == normalized_keyword:
        return True

    text_tokens = tokenize(
        normalized_text
    )

    keyword_tokens = tokenize(
        normalized_keyword
    )

    if not keyword_tokens:
        return False

    if len(keyword_tokens) == 1:
        return keyword_tokens[0] in text_tokens

    keyword_length = len(
        keyword_tokens
    )

    for start_index in range(
        len(text_tokens) - keyword_length + 1
    ):
        token_window = text_tokens[
            start_index:
            start_index + keyword_length
        ]

        if token_window == keyword_tokens:
            return True

    return False


def phrase_match_score(
    text: str,
    keyword: str,
) -> int:
    """
    ให้คะแนนความตรงกันระหว่างข้อความกับ Keyword

    คะแนน:
    100 = ตรงกันพอดี
    90  = Keyword เป็นวลีเต็มในข้อความ
    75  = ทุก Token ของ Keyword อยู่ในข้อความ
    0   = ไม่ตรง
    """

    normalized_text = normalize_text(
        text
    )

    normalized_keyword = normalize_text(
        keyword
    )

    if not normalized_text or not normalized_keyword:
        return 0

    if normalized_text == normalized_keyword:
        return 100

    if contains_whole_word(
        normalized_text,
        normalized_keyword,
    ):
        return 90

    text_tokens = set(
        tokenize(normalized_text)
    )

    keyword_tokens = set(
        tokenize(normalized_keyword)
    )

    if (
        keyword_tokens
        and keyword_tokens.issubset(
            text_tokens
        )
    ):
        return 75

    return 0
# --------------------------------------------------
# Stop words
# --------------------------------------------------

DEFAULT_STOP_WORDS = {
    "หรือเปล่า",
    "ราคาเท่าไหร่",
    "ราคาเท่าไร",
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
    "นะครับ",
    "นะคะ",
    "นะ",
    "ขอ",
    "หน่อย",
    "ช่วย",
}


def remove_stop_words(
    text: str,
    stop_words: set[str] | None = None,
) -> str:
    """ลบคำทั่วไปออกจากข้อความ โดยเริ่มจากคำที่ยาวที่สุด."""

    cleaned_text = normalize_text(
        text
    )

    if not cleaned_text:
        return ""

    selected_stop_words = (
        stop_words
        if stop_words is not None
        else DEFAULT_STOP_WORDS
    )

    for stop_word in sorted(
        selected_stop_words,
        key=len,
        reverse=True,
    ):
        normalized_stop_word = normalize_text(
            stop_word
        )

        if not normalized_stop_word:
            continue

        cleaned_text = cleaned_text.replace(
            normalized_stop_word,
            " ",
        )

    cleaned_text = re.sub(
        r"\s+",
        " ",
        cleaned_text,
    )

    return cleaned_text.strip()


# --------------------------------------------------
# Keyword scoring
# --------------------------------------------------

def keyword_score(
    query: str,
    candidate: str,
) -> int:
    """
    ให้คะแนนความเกี่ยวข้องของคำค้น

    คะแนนโดยประมาณ:
    100 = ตรงกันทั้งหมด
    90  = Candidate เป็นคำเต็มใน Query
    85  = Query เป็นคำเต็มใน Candidate
    75  = Token ตรงกันทั้งหมด
    60  = มีเลขรุ่นเดียวกัน
    0   = ไม่เกี่ยวข้อง
    """

    normalized_query = normalize_text(
        query
    )

    normalized_candidate = normalize_text(
        candidate
    )

    if not normalized_query or not normalized_candidate:
        return 0

    if normalized_query == normalized_candidate:
        return 100

    if contains_whole_word(
        normalized_query,
        normalized_candidate,
    ):
        return 90

    if contains_whole_word(
        normalized_candidate,
        normalized_query,
    ):
        return 85

    phrase_score = phrase_match_score(
        normalized_query,
        normalized_candidate,
    )

    if phrase_score:
        return phrase_score

    query_models = set(
        extract_models(normalized_query)
    )

    candidate_models = set(
        extract_models(normalized_candidate)
    )

    if (
        query_models
        and candidate_models
        and query_models.intersection(
            candidate_models
        )
    ):
        return 60

    return 0


def rank_keywords(
    query: str,
    candidates: Iterable[str],
    limit: int = 20,
) -> list[tuple[str, int]]:
    """จัดอันดับ Candidate Keyword ตามคะแนนความเกี่ยวข้อง."""

    if limit <= 0:
        return []

    ranked_items: list[
        tuple[str, int]
    ] = []

    for candidate in candidates:
        cleaned_candidate = normalize_text(
            candidate
        )

        if not cleaned_candidate:
            continue

        score = keyword_score(
            query=query,
            candidate=cleaned_candidate,
        )

        if score <= 0:
            continue

        ranked_items.append(
            (
                cleaned_candidate,
                score,
            )
        )

    ranked_items.sort(
        key=lambda item: (
            -item[1],
            len(item[0]),
            item[0],
        )
    )

    unique_results: list[
        tuple[str, int]
    ] = []

    seen_keywords: set[str] = set()

    for keyword, score in ranked_items:
        if keyword in seen_keywords:
            continue

        seen_keywords.add(keyword)

        unique_results.append(
            (
                keyword,
                score,
            )
        )

        if len(unique_results) >= limit:
            break

    return unique_results


# --------------------------------------------------
# Manual test
# --------------------------------------------------

def main() -> None:
    """ทดสอบฟังก์ชันหลักของ NLP Core."""

    test_text = (
        "มีถ้วยคัพเค้กรุ่น 5040 ไหม"
    )

    print("=" * 60)
    print("NLP Core Test")
    print("=" * 60)

    print(
        "ข้อความ:",
        test_text,
    )

    print(
        "Normalize:",
        normalize_text(test_text),
    )

    print(
        "Remove stop words:",
        remove_stop_words(test_text),
    )

    print(
        "Tokens:",
        tokenize(test_text),
    )

    print(
        "Models:",
        extract_models(test_text),
    )

    print("-" * 60)

    print(
        "ใส่เค้กวันเกิด ตรงกับ ใส:",
        contains_whole_word(
            "ใส่เค้กวันเกิด",
            "ใส",
        ),
    )

    print(
        "5040 ตรงกับรุ่น 5040:",
        keyword_score(
            "รุ่น 5040",
            "5040",
        ),
    )

    print("=" * 60)


if __name__ == "__main__":
    main()