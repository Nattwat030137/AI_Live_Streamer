"""ระบบค้นหาสินค้าจากฐานข้อมูล SQLite."""

from __future__ import annotations

import sqlite3
from typing import Any

from app.nlp import (
    DEFAULT_STOP_WORDS,
    normalize_text,
    remove_duplicate,
    remove_stop_words,
    tokenize,
)
from config.settings import PROJECT_ROOT


DATABASE_FILE = (
    PROJECT_ROOT
    / "database"
    / "products.db"
)


SEARCH_COLUMNS = (
    "product_name",
    "sku",
    "connection_name",
    "description",
)


SEARCH_STOP_WORDS = DEFAULT_STOP_WORDS.union(
    {
        # คำเกี่ยวกับรุ่นและรหัส
        "รหัสสินค้า",
        "เอสเคยู",
        "โมเดล",
        "รุ่น",
        "รหัส",
        "sku",
        "เบอร์",

        # คำถามราคา
        "ราคาเท่าไหร่",
        "ราคาเท่าไร",
        "กี่บาท",
        "บาทละ",
        "บาท",

        # คำถามสต็อก
        "มีของไหม",
        "มีของมั้ย",
        "ของหมดไหม",
        "ของหมดหรือยัง",
        "มีสต็อกไหม",
        "มีสต๊อกไหม",
        "สต็อก",
        "สต๊อก",
        "เหลือไหม",
        "พร้อมส่งไหม",

        # คำทั่วไปเกี่ยวกับร้าน
        "ขาย",
        "หา",
        "ร้าน",
        "บ้าง",
    }
)


def clean_search_keyword(text: str) -> str:
    """ทำความสะอาดข้อความค้นหาด้วย NLP Core."""

    cleaned_text = remove_stop_words(
        text=text,
        stop_words=SEARCH_STOP_WORDS,
    )

    return normalize_text(
        cleaned_text
    )


def split_search_terms(text: str) -> list[str]:
    """
    แยกข้อความเป็นคำค้นสำหรับ SQLite

    ตัวอย่าง:
    มีถ้วยคัพเค้กรุ่น 5040 ไหม
    -> ["ถ้วยคัพเค้ก", "5040"]
    """

    cleaned_text = clean_search_keyword(
        text
    )

    if not cleaned_text:
        return []

    terms: list[str] = []

    for token in tokenize(
        cleaned_text
    ):
        normalized_token = normalize_text(
            token
        )

        if not normalized_token:
            continue

        if len(normalized_token) < 2:
            continue

        terms.append(
            normalized_token
        )

    # กรณี Tokenizer ไม่คืนค่า แต่ยังมีข้อความ
    if not terms and cleaned_text:
        terms.append(
            cleaned_text
        )

    return remove_duplicate(
        terms
    )


def normalize_product_key(
    value: Any,
) -> str:
    """ปรับค่าเพื่อใช้ตรวจรายการสินค้าซ้ำ."""

    return normalize_text(
        str(value or "")
    )


def build_unique_product_key(
    product: dict[str, Any],
) -> str:
    """สร้างคีย์สำหรับตรวจสินค้าซ้ำ."""

    sku = normalize_product_key(
        product.get("sku")
    )

    product_name = normalize_product_key(
        product.get("product_name")
    )

    connection_name = normalize_product_key(
        product.get("connection_name")
    )

    return (
        sku
        or connection_name
        or product_name
    )


def remove_duplicate_products(
    products: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """ตัดสินค้าที่มีคีย์เดียวกันออก."""

    unique_products: list[
        dict[str, Any]
    ] = []

    seen_keys: set[str] = set()

    for product in products:
        unique_key = build_unique_product_key(
            product
        )

        if not unique_key:
            continue

        if unique_key in seen_keys:
            continue

        seen_keys.add(
            unique_key
        )

        unique_products.append(
            product
        )

    return unique_products
def build_search_condition(
    term_count: int,
) -> str:
    """สร้างเงื่อนไข SQL สำหรับคำค้นหลายคำ."""

    if term_count <= 0:
        return "1 = 0"

    term_conditions: list[str] = []

    for _ in range(term_count):
        column_conditions = [
            f"LOWER({column}) LIKE ?"
            for column in SEARCH_COLUMNS
        ]

        term_conditions.append(
            "("
            + " OR ".join(column_conditions)
            + ")"
        )

    return " AND ".join(
        term_conditions
    )


def build_search_parameters(
    search_terms: list[str],
) -> list[str]:
    """สร้าง Parameter สำหรับ SQL Query."""

    parameters: list[str] = []

    for term in search_terms:
        normalized_term = normalize_text(
            term
        )

        search_pattern = (
            f"%{normalized_term}%"
        )

        for _ in SEARCH_COLUMNS:
            parameters.append(
                search_pattern
            )

    return parameters


def calculate_fetch_limit(
    requested_limit: int,
    term_count: int,
) -> int:
    """คำนวณจำนวนแถวที่ต้องดึงก่อนตัดสินค้าซ้ำ."""

    multiplier = max(
        20,
        term_count * 10,
    )

    return max(
        requested_limit * multiplier,
        requested_limit,
    )


def execute_product_search(
    search_terms: list[str],
    fetch_limit: int,
) -> list[dict[str, Any]]:
    """ค้นสินค้าใน SQLite จากคำค้นแบบ AND."""

    if not search_terms:
        return []

    if not DATABASE_FILE.exists():
        raise FileNotFoundError(
            f"ไม่พบฐานข้อมูลสินค้า: {DATABASE_FILE}"
        )

    where_clause = build_search_condition(
        len(search_terms)
    )

    parameters: list[Any] = (
        build_search_parameters(
            search_terms
        )
    )

    parameters.append(
        fetch_limit
    )

    query = f"""
        SELECT
            id,
            connection_name,
            channel,
            channel_store_name,
            product_name,
            sku,
            sold_count,
            description,
            product_type,
            updated_at
        FROM product_listings
        WHERE {where_clause}
        ORDER BY
            sold_count DESC,
            product_name ASC
        LIMIT ?
    """

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            query,
            parameters,
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def search_products_by_terms(
    search_terms: list[str],
    limit: int = 10,
) -> list[dict[str, Any]]:
    """ค้นสินค้าจากคำค้นที่เตรียมไว้แล้ว."""

    if limit <= 0:
        return []

    normalized_terms = remove_duplicate(
        [
            normalize_text(term)
            for term in search_terms
            if normalize_text(term)
        ]
    )

    if not normalized_terms:
        return []

    fetch_limit = calculate_fetch_limit(
        requested_limit=limit,
        term_count=len(normalized_terms),
    )

    raw_products = execute_product_search(
        search_terms=normalized_terms,
        fetch_limit=fetch_limit,
    )

    unique_products = remove_duplicate_products(
        raw_products
    )

    return unique_products[:limit]
def search_products(
    keyword: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    ค้นสินค้าจากข้อความของลูกค้า

    ขั้นตอน:
    1. ทำความสะอาดข้อความด้วย NLP Core
    2. แยกคำค้น
    3. ค้น SQLite แบบ AND
    4. ตัดสินค้าซ้ำ
    """

    search_terms = split_search_terms(
        keyword
    )

    if not search_terms:
        return []

    return search_products_by_terms(
        search_terms=search_terms,
        limit=limit,
    )


def search_products_any_term(
    search_terms: list[str],
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    ค้นสินค้าโดยให้ตรงกับคำค้นอย่างน้อยหนึ่งคำ

    เหมาะสำหรับ Search Planner V2 ซึ่งส่งคำค้นหลาย Task
    แล้วต้องรวมผลลัพธ์จากแต่ละคำค้น
    """

    if limit <= 0:
        return []

    normalized_terms = remove_duplicate(
        [
            normalize_text(term)
            for term in search_terms
            if normalize_text(term)
        ]
    )

    if not normalized_terms:
        return []

    result_groups: list[
        list[dict[str, Any]]
    ] = []

    per_term_limit = max(
        limit,
        10,
    )

    for term in normalized_terms:
        term_results = search_products_by_terms(
            search_terms=[term],
            limit=per_term_limit,
        )

        result_groups.append(
            term_results
        )

    return merge_product_results(
        result_groups=result_groups,
        limit=limit,
    )


def merge_product_results(
    result_groups: list[
        list[dict[str, Any]]
    ],
    limit: int = 10,
) -> list[dict[str, Any]]:
    """รวมผลค้นหาหลายชุดและตัดสินค้าซ้ำ."""

    if limit <= 0:
        return []

    combined_products: list[
        dict[str, Any]
    ] = []

    for result_group in result_groups:
        combined_products.extend(
            result_group
        )

    unique_products = remove_duplicate_products(
        combined_products
    )

    return unique_products[:limit]


def main() -> None:
    """ทดสอบ Product Search แบบรับข้อความจากผู้ใช้."""

    keyword = input(
        "ค้นหาสินค้า: "
    ).strip()

    search_terms = split_search_terms(
        keyword
    )

    print("=" * 60)
    print(
        "คำค้นหลังทำความสะอาด:",
        search_terms,
    )
    print("=" * 60)

    products = search_products(
        keyword=keyword,
        limit=10,
    )

    print(
        f"พบสินค้า {len(products)} รายการ"
    )
    print("=" * 60)

    for number, product in enumerate(
        products,
        start=1,
    ):
        print(
            f"{number}. "
            f"{product.get('product_name', '')}"
        )

        print(
            "   SKU:",
            product.get(
                "sku",
                "",
            ),
        )

        print(
            "   ช่องทาง:",
            product.get(
                "channel",
                "",
            ),
        )

        print("-" * 60)


if __name__ == "__main__":
    main()