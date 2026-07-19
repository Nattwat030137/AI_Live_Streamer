"""ค้นสินค้าจริงจากคำแนะนำของ Sales Brain."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.sales_brain import SalesSuggestion
from app.core.search_executor import (
    SearchExecutionResult,
    SearchExecutor,
)


DEFAULT_KEYWORD_LIMIT = 3
DEFAULT_PRODUCT_LIMIT_PER_KEYWORD = 5
DEFAULT_RESULT_LIMIT = 3


@dataclass(slots=True)
class RecommendationItem:
    """ผลค้นหาสินค้าสำหรับคำแนะนำหนึ่งคำ."""

    keyword: str
    score: int
    products: list[dict[str, Any]] = field(
        default_factory=list
    )
    summary: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def product_count(self) -> int:
        """คืนจำนวนสินค้าที่ค้นพบ."""

        return len(
            self.products
        )

    @property
    def found_products(self) -> bool:
        """คืน True เมื่อพบสินค้าอย่างน้อยหนึ่งรายการ."""

        return bool(
            self.products
        )


@dataclass(slots=True)
class RecommendationSearchResult:
    """ผลรวมจากการค้นสินค้าที่ Sales Brain แนะนำ."""

    source_trigger: str = ""
    items: list[RecommendationItem] = field(
        default_factory=list
    )

    @property
    def found_recommendations(self) -> bool:
        """คืน True เมื่อพบสินค้าแนะนำจริง."""

        return any(
            item.found_products
            for item in self.items
        )

    @property
    def total_product_count(self) -> int:
        """คืนจำนวนสินค้าที่พบจากทุกคำแนะนำ."""

        return sum(
            item.product_count
            for item in self.items
        )

    def top_items(
        self,
        limit: int = DEFAULT_RESULT_LIMIT,
    ) -> list[RecommendationItem]:
        """คืนคำแนะนำอันดับสูงสุดที่พบสินค้าจริง."""

        if limit <= 0:
            return []

        available_items = [
            item
            for item in self.items
            if item.found_products
        ]

        return sorted(
            available_items,
            key=lambda item: (
                item.score,
                item.product_count,
            ),
            reverse=True,
        )[:limit]


def calculate_recommendation_score(
    position: int,
    product_count: int,
) -> int:
    """
    คำนวณคะแนนคำแนะนำ.

    คำแนะนำลำดับแรกมีคะแนนพื้นฐานสูงกว่า
    และเพิ่มคะแนนเล็กน้อยเมื่อพบสินค้าจริงหลายรายการ
    """

    safe_position = max(
        position,
        0,
    )

    safe_product_count = max(
        product_count,
        0,
    )

    base_score = (
        95
        - safe_position * 10
    )

    availability_bonus = min(
        safe_product_count,
        5,
    )

    return max(
        0,
        min(
            100,
            base_score
            + availability_bonus,
        ),
    )


def create_keyword_executor(
    product_limit: int,
) -> SearchExecutor:
    """สร้าง Search Executor สำหรับค้นคำแนะนำหนึ่งคำ."""

    return SearchExecutor(
        product_limit=max(
            product_limit,
            0,
        ),
        task_limit=6,
        graph_limit_per_task=4,
        product_limit_per_task=max(
            product_limit,
            0,
        ),
    )


def search_recommendation_keyword(
    keyword: str,
    position: int,
    product_limit: int = (
        DEFAULT_PRODUCT_LIMIT_PER_KEYWORD
    ),
    executor: SearchExecutor | None = None,
) -> RecommendationItem:
    """ค้นสินค้าจริงสำหรับคำแนะนำหนึ่งคำ."""

    cleaned_keyword = (
        keyword.strip()
    )

    if not cleaned_keyword:
        return RecommendationItem(
            keyword="",
            score=0,
        )

    selected_executor = (
        executor
        if executor is not None
        else create_keyword_executor(
            product_limit
        )
    )

    search_result: SearchExecutionResult = (
        selected_executor.search(
            cleaned_keyword
        )
    )

    score = calculate_recommendation_score(
        position=position,
        product_count=(
            search_result.product_count
        ),
    )

    return RecommendationItem(
        keyword=cleaned_keyword,
        score=score,
        products=list(
            search_result.products
        ),
        summary=dict(
            search_result.summary
        ),
    )


def search_sales_recommendations(
    suggestion: SalesSuggestion,
    keyword_limit: int = DEFAULT_KEYWORD_LIMIT,
    product_limit_per_keyword: int = (
        DEFAULT_PRODUCT_LIMIT_PER_KEYWORD
    ),
) -> RecommendationSearchResult:
    """ค้นสินค้าจริงจากรายการคำแนะนำของ Sales Brain."""

    if (
        not suggestion.has_result
        or keyword_limit <= 0
        or product_limit_per_keyword <= 0
    ):
        return RecommendationSearchResult(
            source_trigger=(
                suggestion.trigger
            ),
        )

    selected_keywords = (
        suggestion.keywords[
            :keyword_limit
        ]
    )

    executor = create_keyword_executor(
        product_limit_per_keyword
    )

    items: list[
        RecommendationItem
    ] = []

    seen_keywords: set[str] = set()

    for position, keyword in enumerate(
        selected_keywords
    ):
        cleaned_keyword = (
            keyword.strip()
        )

        if not cleaned_keyword:
            continue

        normalized_keyword = (
            cleaned_keyword.lower()
        )

        if normalized_keyword in seen_keywords:
            continue

        seen_keywords.add(
            normalized_keyword
        )

        item = search_recommendation_keyword(
            keyword=cleaned_keyword,
            position=position,
            product_limit=(
                product_limit_per_keyword
            ),
            executor=executor,
        )

        items.append(
            item
        )

    return RecommendationSearchResult(
        source_trigger=suggestion.trigger,
        items=items,
    )


def format_recommendation_search(
    result: RecommendationSearchResult,
    item_limit: int = DEFAULT_RESULT_LIMIT,
    product_limit: int = 2,
) -> str:
    """จัดผลค้นหาสินค้าแนะนำเป็นข้อความสำหรับ Prompt."""

    top_items = result.top_items(
        limit=item_limit
    )

    if not top_items:
        return (
            "ไม่พบสินค้าแนะนำเพิ่มเติม"
            "ในฐานข้อมูล"
        )

    lines: list[str] = [
        (
            "คำหลักที่ใช้สร้างคำแนะนำ: "
            f"{result.source_trigger}"
        ),
        "สินค้าแนะนำที่พบจริง:",
    ]

    for item_number, item in enumerate(
        top_items,
        start=1,
    ):
        lines.append(
            f"{item_number}. "
            f"{item.keyword} "
            f"(score={item.score}, "
            f"พบ {item.product_count} รายการ)"
        )

        for product in item.products[
            :max(product_limit, 0)
        ]:
            product_name = str(
                product.get(
                    "product_name",
                    "",
                )
            ).strip()

            if product_name:
                lines.append(
                    f"   - {product_name}"
                )

    return "\n".join(
        lines
    )


class RecommendationSearch:
    """Facade สำหรับค้นสินค้าจากคำแนะนำของ Sales Brain."""

    def __init__(
        self,
        keyword_limit: int = (
            DEFAULT_KEYWORD_LIMIT
        ),
        product_limit_per_keyword: int = (
            DEFAULT_PRODUCT_LIMIT_PER_KEYWORD
        ),
        result_limit: int = (
            DEFAULT_RESULT_LIMIT
        ),
    ) -> None:
        self.keyword_limit = (
            keyword_limit
        )

        self.product_limit_per_keyword = (
            product_limit_per_keyword
        )

        self.result_limit = (
            result_limit
        )

    def search(
        self,
        suggestion: SalesSuggestion,
    ) -> RecommendationSearchResult:
        """ค้นสินค้าจริงจาก Sales Suggestion."""

        return search_sales_recommendations(
            suggestion=suggestion,
            keyword_limit=self.keyword_limit,
            product_limit_per_keyword=(
                self.product_limit_per_keyword
            ),
        )

    def format(
        self,
        result: RecommendationSearchResult,
    ) -> str:
        """จัดผลค้นหาเพื่อส่งเข้า Prompt."""

        return format_recommendation_search(
            result=result,
            item_limit=self.result_limit,
        )