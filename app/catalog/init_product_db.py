"""สร้าง SQLite Product Catalog จากไฟล์ JSON."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_JSON_PATH = (
    PROJECT_ROOT
    / "data"
    / "bakery_products.json"
)

DEFAULT_DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "products.db"
)


CREATE_PRODUCTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    compatible_bag TEXT NOT NULL DEFAULT '',
    material TEXT NOT NULL DEFAULT '',
    color TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT 'bakery_products.json',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


CREATE_MODEL_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_products_model
ON products(model);
"""


CREATE_CATEGORY_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_products_category
ON products(category);
"""


UPSERT_PRODUCT_SQL = """
INSERT INTO products (
    model,
    name,
    category,
    compatible_bag,
    material,
    color,
    notes,
    source
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(model) DO UPDATE SET
    name = excluded.name,
    category = excluded.category,
    compatible_bag = excluded.compatible_bag,
    material = excluded.material,
    color = excluded.color,
    notes = excluded.notes,
    source = excluded.source,
    updated_at = CURRENT_TIMESTAMP;
"""


def load_json_products(
    json_path: Path,
) -> list[dict[str, Any]]:
    """โหลดและตรวจข้อมูลสินค้าจาก JSON."""

    if not json_path.exists():
        raise FileNotFoundError(
            f"ไม่พบไฟล์ Product Catalog: {json_path}"
        )

    raw_text = json_path.read_text(
        encoding="utf-8"
    )

    raw_data = json.loads(
        raw_text
    )

    if not isinstance(
        raw_data,
        list,
    ):
        raise ValueError(
            "Product Catalog ต้องเป็น JSON List"
        )

    products: list[dict[str, Any]] = []

    for index, item in enumerate(
        raw_data,
        start=1,
    ):
        if not isinstance(
            item,
            dict,
        ):
            raise ValueError(
                f"ข้อมูลสินค้าลำดับที่ {index} "
                "ต้องเป็น JSON Object"
            )

        model = str(
            item.get(
                "model",
                "",
            )
        ).strip()

        name = str(
            item.get(
                "name",
                "",
            )
        ).strip()

        if not model:
            raise ValueError(
                f"สินค้าลำดับที่ {index} ไม่มี model"
            )

        if not name:
            raise ValueError(
                f"สินค้าลำดับที่ {index} ไม่มี name"
            )

        products.append(
            {
                "model": model,
                "name": name,
                "category": str(
                    item.get(
                        "category",
                        "",
                    )
                ).strip(),
                "compatible_bag": str(
                    item.get(
                        "compatible_bag",
                        "",
                    )
                ).strip(),
                "material": str(
                    item.get(
                        "material",
                        "",
                    )
                ).strip(),
                "color": str(
                    item.get(
                        "color",
                        "",
                    )
                ).strip(),
                "notes": str(
                    item.get(
                        "notes",
                        "",
                    )
                ).strip(),
                "source": json_path.name,
            }
        )

    return products


def initialize_database(
    *,
    json_path: Path = DEFAULT_JSON_PATH,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> int:
    """
    สร้างฐานข้อมูลและนำเข้าสินค้าจาก JSON.

    Returns:
        จำนวนสินค้าที่นำเข้า
    """

    products = load_json_products(
        json_path
    )

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        connection.execute(
            CREATE_PRODUCTS_TABLE_SQL
        )

        connection.execute(
            CREATE_MODEL_INDEX_SQL
        )

        connection.execute(
            CREATE_CATEGORY_INDEX_SQL
        )

        for product in products:
            connection.execute(
                UPSERT_PRODUCT_SQL,
                (
                    product["model"],
                    product["name"],
                    product["category"],
                    product["compatible_bag"],
                    product["material"],
                    product["color"],
                    product["notes"],
                    product["source"],
                ),
            )

        connection.commit()

    return len(
        products
    )


def read_database_summary(
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> list[tuple[str, str]]:
    """อ่าน Model และชื่อสินค้าจากฐานข้อมูล."""

    if not database_path.exists():
        raise FileNotFoundError(
            f"ไม่พบฐานข้อมูล: {database_path}"
        )

    with sqlite3.connect(
        database_path
    ) as connection:
        rows = connection.execute(
            """
            SELECT model, name
            FROM products
            ORDER BY model
            """
        ).fetchall()

    return [
        (
            str(row[0]),
            str(row[1]),
        )
        for row in rows
    ]


def main() -> None:
    """สร้างฐานข้อมูลและแสดงผลสรุป."""

    imported_count = initialize_database()

    rows = read_database_summary()

    print("=" * 60)
    print("SQLite Product Catalog")
    print("=" * 60)
    print(
        f"Database: {DEFAULT_DATABASE_PATH}"
    )
    print(
        f"Imported: {imported_count}"
    )
    print(
        f"Products in database: {len(rows)}"
    )
    print("-" * 60)

    for model, name in rows:
        print(
            f"{model}: {name}"
        )

    print("=" * 60)


if __name__ == "__main__":
    main()