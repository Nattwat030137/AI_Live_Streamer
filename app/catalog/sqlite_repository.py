"""SQLite repository สำหรับ Product Catalog."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "products.db"
)


@dataclass(frozen=True, slots=True)
class ProductRecord:
    """ข้อมูลสินค้าหนึ่งรายการจาก Product Catalog."""

    model: str
    name: str
    category: str = ""
    compatible_bag: str = ""
    material: str = ""
    color: str = ""
    notes: str = ""
    source: str = ""

    @classmethod
    def from_row(
        cls,
        row: sqlite3.Row,
    ) -> "ProductRecord":
        """สร้าง ProductRecord จาก sqlite3.Row."""

        return cls(
            model=str(row["model"]),
            name=str(row["name"]),
            category=str(row["category"]),
            compatible_bag=str(
                row["compatible_bag"]
            ),
            material=str(row["material"]),
            color=str(row["color"]),
            notes=str(row["notes"]),
            source=str(row["source"]),
        )

    def to_dict(self) -> dict[str, Any]:
        """แปลงข้อมูลสินค้าเป็น Dictionary."""

        return {
            "model": self.model,
            "name": self.name,
            "category": self.category,
            "compatible_bag": self.compatible_bag,
            "material": self.material,
            "color": self.color,
            "notes": self.notes,
            "source": self.source,
        }


class SQLiteProductRepository:
    """อ่านข้อมูล Product Catalog จาก SQLite."""

    def __init__(
        self,
        database_path: Path | str = (
            DEFAULT_DATABASE_PATH
        ),
    ) -> None:
        """กำหนดตำแหน่งฐานข้อมูล."""

        self.database_path = Path(
            database_path
        )

    def connect(
        self,
    ) -> sqlite3.Connection:
        """
        เปิด SQLite Connection.

        ผู้เรียกต้องใช้ผ่าน with statement
        เพื่อให้ Connection ถูกปิดอัตโนมัติ
        """

        if not self.database_path.exists():
            raise FileNotFoundError(
                "ไม่พบฐานข้อมูล Product Catalog: "
                f"{self.database_path}"
            )

        connection = sqlite3.connect(
            self.database_path
        )

        connection.row_factory = sqlite3.Row

        return connection

    def count(self) -> int:
        """คืนจำนวนสินค้าทั้งหมด."""

        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM products
                """
            ).fetchone()

        if row is None:
            return 0

        return int(
            row["total"]
        )

    def get_by_model(
        self,
        model: str,
    ) -> ProductRecord | None:
        """ค้นสินค้าจาก Model แบบตรงตัว."""

        normalized_model = (
            model.strip()
        )

        if not normalized_model:
            return None

        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    model,
                    name,
                    category,
                    compatible_bag,
                    material,
                    color,
                    notes,
                    source
                FROM products
                WHERE LOWER(model) = LOWER(?)
                LIMIT 1
                """,
                (
                    normalized_model,
                ),
            ).fetchone()

        if row is None:
            return None

        return ProductRecord.from_row(
            row
        )

    def search(
        self,
        query: str,
        *,
        limit: int = 20,
    ) -> list[ProductRecord]:
        """
        ค้นสินค้าจาก Model, Name, Category,
        Material, Color และ Compatible Bag.
        """

        normalized_query = (
            query.strip()
        )

        normalized_limit = max(
            int(limit),
            0,
        )

        if (
            not normalized_query
            or normalized_limit == 0
        ):
            return []

        search_pattern = (
            f"%{normalized_query}%"
        )

        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    model,
                    name,
                    category,
                    compatible_bag,
                    material,
                    color,
                    notes,
                    source
                FROM products
                WHERE
                    model LIKE ? COLLATE NOCASE
                    OR name LIKE ? COLLATE NOCASE
                    OR category LIKE ? COLLATE NOCASE
                    OR compatible_bag LIKE ? COLLATE NOCASE
                    OR material LIKE ? COLLATE NOCASE
                    OR color LIKE ? COLLATE NOCASE
                    OR notes LIKE ? COLLATE NOCASE
                ORDER BY
                    CASE
                        WHEN LOWER(model) = LOWER(?)
                        THEN 0
                        WHEN model LIKE ? COLLATE NOCASE
                        THEN 1
                        WHEN name LIKE ? COLLATE NOCASE
                        THEN 2
                        ELSE 3
                    END,
                    model ASC
                LIMIT ?
                """,
                (
                    search_pattern,
                    search_pattern,
                    search_pattern,
                    search_pattern,
                    search_pattern,
                    search_pattern,
                    search_pattern,
                    normalized_query,
                    search_pattern,
                    search_pattern,
                    normalized_limit,
                ),
            ).fetchall()

        return [
            ProductRecord.from_row(
                row
            )
            for row in rows
        ]

    def list_all(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[ProductRecord]:
        """คืนสินค้าทั้งหมดเรียงตาม Model."""

        normalized_offset = max(
            int(offset),
            0,
        )

        sql = """
            SELECT
                model,
                name,
                category,
                compatible_bag,
                material,
                color,
                notes,
                source
            FROM products
            ORDER BY model ASC
        """

        parameters: tuple[Any, ...]

        if limit is None:
            sql += " LIMIT -1 OFFSET ?"
            parameters = (
                normalized_offset,
            )

        else:
            normalized_limit = max(
                int(limit),
                0,
            )

            if normalized_limit == 0:
                return []

            sql += " LIMIT ? OFFSET ?"
            parameters = (
                normalized_limit,
                normalized_offset,
            )

        with self.connect() as connection:
            rows = connection.execute(
                sql,
                parameters,
            ).fetchall()

        return [
            ProductRecord.from_row(
                row
            )
            for row in rows
        ]

    def get_many_by_models(
        self,
        models: Iterable[str],
    ) -> list[ProductRecord]:
        """ค้นสินค้าหลาย Model โดยรักษาลำดับ Input."""

        normalized_models = [
            model.strip()
            for model in models
            if model.strip()
        ]

        if not normalized_models:
            return []

        products_by_model: dict[
            str,
            ProductRecord,
        ] = {}

        for model in normalized_models:
            product = self.get_by_model(
                model
            )

            if product is not None:
                products_by_model[
                    model.lower()
                ] = product

        return [
            products_by_model[
                model.lower()
            ]
            for model in normalized_models
            if model.lower()
            in products_by_model
        ]

    def exists(
        self,
        model: str,
    ) -> bool:
        """ตรวจว่ามี Model อยู่ในฐานข้อมูลหรือไม่."""

        return (
            self.get_by_model(
                model
            )
            is not None
        )

    def to_dict(self) -> dict[str, Any]:
        """คืนข้อมูลสรุปของ Repository."""

        return {
            "repository": (
                "sqlite_product_repository"
            ),
            "database_path": str(
                self.database_path
            ),
            "database_exists": (
                self.database_path.exists()
            ),
            "product_count": (
                self.count()
                if self.database_path.exists()
                else 0
            ),
        }


def main() -> None:
    """ทดสอบ Repository แบบ Command Line."""

    repository = (
        SQLiteProductRepository()
    )

    print("=" * 60)
    print("SQLite Product Repository")
    print("=" * 60)
    print(
        f"Database: {repository.database_path}"
    )
    print(
        f"Product count: {repository.count()}"
    )
    print("-" * 60)

    for product in repository.list_all():
        print(
            f"{product.model}: "
            f"{product.name}"
        )

    print("=" * 60)


if __name__ == "__main__":
    main()
