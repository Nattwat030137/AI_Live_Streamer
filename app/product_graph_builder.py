"""สร้าง Product Graph จากฐานข้อมูลสินค้า."""

from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict
from datetime import datetime
from typing import Any

from config.settings import PROJECT_ROOT


DATABASE_PATH = (
    PROJECT_ROOT
    / "database"
    / "products.db"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "knowledge"
    / "product_graph.json"
)


def normalize_text(text: Any) -> str:
    """ปรับข้อความให้อยู่ในรูปแบบเดียวกัน."""

    normalized_text = str(
        text or ""
    ).strip().lower()

    normalized_text = re.sub(
        r"[^\wก-๙\s\-–/]+",
        " ",
        normalized_text,
    )

    normalized_text = re.sub(
        r"\s+",
        " ",
        normalized_text,
    )

    return normalized_text.strip()


def split_keywords(text: Any) -> list[str]:
    """แยกคำสำคัญจากข้อความสินค้า."""

    normalized_text = normalize_text(
        text
    )

    if not normalized_text:
        return []

    keywords: list[str] = []

    for word in normalized_text.split():
        cleaned_word = word.strip(
            "-–/"
        )

        if len(cleaned_word) < 2:
            continue

        if cleaned_word not in keywords:
            keywords.append(
                cleaned_word
            )

    return keywords


def extract_models(text: Any) -> list[str]:
    """ค้นหาเลขรุ่นสินค้าจากข้อความ."""

    normalized_text = normalize_text(
        text
    )

    models = re.findall(
        r"(?<!\d)(\d{3,6})(?!\d)",
        normalized_text,
    )

    return list(
        dict.fromkeys(models)
    )


def load_products() -> list[dict[str, Any]]:
    """อ่านข้อมูลสินค้าทั้งหมดจาก SQLite."""

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"ไม่พบฐานข้อมูลสินค้า: {DATABASE_PATH}"
        )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            """
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
                updated_at,
                created_at
            FROM product_listings
            ORDER BY id ASC
            """
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def create_empty_graph() -> dict[str, Any]:
    """สร้างโครงสร้าง Product Graph เริ่มต้น."""

    return {
        "graph_version": "1.0",
        "generated_at": datetime.now().isoformat(
            timespec="seconds"
        ),
        "statistics": {
            "source_products": 0,
            "unique_products": 0,
            "keyword_count": 0,
            "model_count": 0,
            "product_type_count": 0,
        },
        "products": {},
        "keywords": defaultdict(list),
        "models": defaultdict(list),
        "product_types": defaultdict(list),
    }
def build_product_key(product: dict[str, Any]) -> str:
    """สร้างคีย์สินค้าเพื่อรวมรายการซ้ำจากหลายช่องทาง."""

    sku = normalize_text(
        product.get("sku", "")
    )

    product_name = normalize_text(
        product.get("product_name", "")
    )

    connection_name = normalize_text(
        product.get("connection_name", "")
    )

    return sku or connection_name or product_name


def append_unique(
    mapping: defaultdict[str, list[str]],
    key: str,
    value: str,
) -> None:
    """เพิ่มค่าเข้า Mapping โดยไม่ให้ซ้ำ."""

    if not key or not value:
        return

    if value not in mapping[key]:
        mapping[key].append(value)


def build_product_node(
    product_key: str,
    product_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """รวมหลาย Listing ให้เป็น Product Node เดียว."""

    product_names: list[str] = []
    skus: list[str] = []
    product_types: list[str] = []
    channels: list[str] = []
    models: list[str] = []
    keywords: list[str] = []

    total_sold_count = 0
    latest_updated_at = ""

    for product in product_rows:
        product_name = str(
            product.get("product_name", "")
        ).strip()

        sku = str(
            product.get("sku", "")
        ).strip()

        product_type = str(
            product.get("product_type", "")
        ).strip()

        channel = str(
            product.get("channel", "")
        ).strip()

        updated_at = str(
            product.get("updated_at", "")
        ).strip()

        sold_count = product.get(
            "sold_count",
            0,
        )

        try:
            total_sold_count += int(
                sold_count or 0
            )
        except (TypeError, ValueError):
            pass

        if product_name and product_name not in product_names:
            product_names.append(product_name)

        if sku and sku not in skus:
            skus.append(sku)

        if product_type and product_type not in product_types:
            product_types.append(product_type)

        if channel and channel not in channels:
            channels.append(channel)

        if updated_at > latest_updated_at:
            latest_updated_at = updated_at

        combined_text = " ".join(
            [
                product_name,
                sku,
                product_type,
                str(
                    product.get(
                        "connection_name",
                        "",
                    )
                ),
                str(
                    product.get(
                        "description",
                        "",
                    )
                ),
            ]
        )

        for model in extract_models(
            combined_text
        ):
            if model not in models:
                models.append(model)

        for keyword in split_keywords(
            combined_text
        ):
            if keyword not in keywords:
                keywords.append(keyword)

    return {
        "product_key": product_key,
        "product_names": product_names,
        "skus": skus,
        "product_types": product_types,
        "channels": channels,
        "models": models,
        "keywords": keywords,
        "listing_count": len(product_rows),
        "total_sold_count": total_sold_count,
        "latest_updated_at": latest_updated_at,
    }


def group_products(
    products: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """จัดกลุ่ม Listing ที่เป็นสินค้ารายการเดียวกัน."""

    grouped_products: defaultdict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(list)

    for product in products:
        product_key = build_product_key(
            product
        )

        if not product_key:
            continue

        grouped_products[product_key].append(
            product
        )

    return dict(grouped_products)


def build_graph(
    products: list[dict[str, Any]],
) -> dict[str, Any]:
    """สร้าง Product Graph จากข้อมูลสินค้าทั้งหมด."""

    graph = create_empty_graph()

    grouped_products = group_products(
        products
    )

    graph["statistics"][
        "source_products"
    ] = len(products)

    graph["statistics"][
        "unique_products"
    ] = len(grouped_products)

    for product_key, product_rows in grouped_products.items():
        product_node = build_product_node(
            product_key,
            product_rows,
        )

        graph["products"][
            product_key
        ] = product_node

        for keyword in product_node["keywords"]:
            append_unique(
                graph["keywords"],
                keyword,
                product_key,
            )

        for model in product_node["models"]:
            append_unique(
                graph["models"],
                model,
                product_key,
            )

        for product_type in product_node[
            "product_types"
        ]:
            normalized_type = normalize_text(
                product_type
            )

            append_unique(
                graph["product_types"],
                normalized_type,
                product_key,
            )

    graph["statistics"][
        "keyword_count"
    ] = len(graph["keywords"])

    graph["statistics"][
        "model_count"
    ] = len(graph["models"])

    graph["statistics"][
        "product_type_count"
    ] = len(graph["product_types"])

    return graph
def save_graph(
    graph: dict[str, Any],
) -> None:
    """บันทึก Product Graph เป็นไฟล์ JSON."""

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    serializable_graph = {
        "graph_version": graph["graph_version"],
        "generated_at": graph["generated_at"],
        "statistics": graph["statistics"],
        "products": graph["products"],
        "keywords": dict(graph["keywords"]),
        "models": dict(graph["models"]),
        "product_types": dict(
            graph["product_types"]
        ),
    }

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            serializable_graph,
            file,
            ensure_ascii=False,
            indent=2,
        )


def main() -> None:
    """สร้าง Product Graph."""

    print("=" * 60)
    print("กำลังสร้าง Product Graph...")
    print("=" * 60)

    products = load_products()

    print(
        f"อ่านข้อมูลสินค้า {len(products):,} รายการ"
    )

    graph = build_graph(
        products
    )

    save_graph(
        graph
    )

    statistics = graph["statistics"]

    print("-" * 60)

    print(
        "จำนวน Listing :",
        f"{statistics['source_products']:,}",
    )

    print(
        "จำนวนสินค้า :",
        f"{statistics['unique_products']:,}",
    )

    print(
        "จำนวน Keyword :",
        f"{statistics['keyword_count']:,}",
    )

    print(
        "จำนวน Model :",
        f"{statistics['model_count']:,}",
    )

    print(
        "จำนวน Product Type :",
        f"{statistics['product_type_count']:,}",
    )

    print("-" * 60)

    print(
        "บันทึกไฟล์สำเร็จ"
    )

    print(
        OUTPUT_PATH
    )

    print("=" * 60)


if __name__ == "__main__":
    main()