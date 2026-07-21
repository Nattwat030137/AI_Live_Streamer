"""Knowledge Retriever สำหรับ Bakery D'Ver Demo ที่ใช้ SQLite."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.catalog.sqlite_repository import (
    DEFAULT_DATABASE_PATH,
    ProductRecord,
    SQLiteProductRepository,
)
from app.search_planner import SearchPlan


@dataclass(frozen=True, slots=True)
class ProductKnowledge:
    """ข้อมูลสินค้าที่ค้นพบจาก Product Catalog."""

    model: str
    name: str
    category: str = ""
    compatible_bag: str = ""
    material: str = ""
    color: str = ""
    notes: str = ""
    source: str = "products.db"

    @classmethod
    def from_record(
        cls,
        record: ProductRecord,
    ) -> "ProductKnowledge":
        """สร้าง ProductKnowledge จาก ProductRecord."""

        return cls(
            model=record.model,
            name=record.name,
            category=record.category,
            compatible_bag=record.compatible_bag,
            material=record.material,
            color=record.color,
            notes=record.notes,
            source=record.source or "products.db",
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


@dataclass(slots=True)
class KnowledgeResult:
    """ผลลัพธ์จาก Knowledge Retriever."""

    found: bool = False
    products: list[ProductKnowledge] = field(
        default_factory=list
    )
    searched_models: list[str] = field(
        default_factory=list
    )
    matched_keywords: list[str] = field(
        default_factory=list
    )
    source: str = ""
    warnings: list[str] = field(
        default_factory=list
    )

    @property
    def primary_product(
        self,
    ) -> ProductKnowledge | None:
        """คืนสินค้ารายการแรกที่ค้นพบ."""

        if not self.products:
            return None

        return self.products[0]

    def to_dict(self) -> dict[str, Any]:
        """แปลงผลลัพธ์เป็น Dictionary."""

        return {
            "found": self.found,
            "products": [
                product.to_dict()
                for product in self.products
            ],
            "searched_models": list(
                self.searched_models
            ),
            "matched_keywords": list(
                self.matched_keywords
            ),
            "source": self.source,
            "warnings": list(
                self.warnings
            ),
        }


class ProductCatalogRetriever:
    """
    ค้นข้อมูลสินค้าจาก SQLite Product Repository.

    ใช้ชื่อคลาสเดิมเพื่อรักษาความเข้ากันได้กับ
    BakeryDemo และ MockLLM Regression Test.
    """

    def __init__(
        self,
        database_path: Path | str = (
            DEFAULT_DATABASE_PATH
        ),
        repository: SQLiteProductRepository | None = None,
    ) -> None:
        """สร้าง Retriever ด้วย SQLite Repository."""

        self.repository = (
            repository
            if repository is not None
            else SQLiteProductRepository(
                database_path
            )
        )

    def retrieve(
        self,
        plan: SearchPlan,
    ) -> KnowledgeResult:
        """ค้นข้อมูลสินค้าจาก Search Plan."""

        result = KnowledgeResult(
            searched_models=list(
                plan.extracted_models
            ),
            source=str(
                self.repository.database_path
            ),
        )

        seen_models: set[str] = set()

        for model in plan.extracted_models:
            product = self.repository.get_by_model(
                model
            )

            if product is None:
                continue

            self._append_product(
                result=result,
                product=product,
                matched_keyword=model,
                seen_models=seen_models,
            )

        if result.products:
            result.found = True
            return result

        if plan.extracted_models:
            result.warnings.append(
                "ไม่พบข้อมูลสินค้าตามรุ่นที่ระบุ"
            )
            return result

        for task in plan.tasks:
            keyword = task.keyword.strip()

            if not keyword:
                continue

            matches = self.repository.search(
                keyword,
                limit=10,
            )

            for product in matches:
                self._append_product(
                    result=result,
                    product=product,
                    matched_keyword=keyword,
                    seen_models=seen_models,
                )

        result.found = bool(
            result.products
        )

        if not result.found:
            result.warnings.append(
                "ไม่พบข้อมูลสินค้าที่ตรงกับ Search Plan"
            )

        return result

    @staticmethod
    def _append_product(
        *,
        result: KnowledgeResult,
        product: ProductRecord,
        matched_keyword: str,
        seen_models: set[str],
    ) -> None:
        """เพิ่มสินค้าโดยไม่ให้ Model ซ้ำ."""

        normalized_model = (
            product.model.strip().lower()
        )

        if normalized_model in seen_models:
            return

        seen_models.add(
            normalized_model
        )

        result.products.append(
            ProductKnowledge.from_record(
                product
            )
        )

        if matched_keyword not in (
            result.matched_keywords
        ):
            result.matched_keywords.append(
                matched_keyword
            )

    def to_dict(self) -> dict[str, Any]:
        """คืนข้อมูลสรุปของ Retriever."""

        return {
            "retriever": (
                "sqlite_product_catalog_retriever"
            ),
            "repository": (
                self.repository.to_dict()
            ),
        }
