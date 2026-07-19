"""ดำเนินการ Search Plan และสรุปผลการค้นหาสินค้า."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.product_intelligence import summarize_products
from app.product_search import (
    merge_product_results,
    search_products_any_term,
)
from app.search_planner import (
    SearchPlan,
    SearchTask,
    create_search_plan,
)


DEFAULT_PRODUCT_LIMIT = 10
DEFAULT_TASK_LIMIT = 12
DEFAULT_GRAPH_LIMIT_PER_TASK = 6
DEFAULT_PRODUCT_LIMIT_PER_TASK = 10


@dataclass(slots=True)
class SearchExecutionResult:
    """ผลลัพธ์ทั้งหมดจากกระบวนการค้นหาสินค้า."""

    message: str
    search_plan: SearchPlan
    products: list[dict[str, Any]] = field(
        default_factory=list
    )
    summary: dict[str, Any] = field(
        default_factory=dict
    )
    searched_keywords: list[str] = field(
        default_factory=list
    )

    @property
    def product_count(self) -> int:
        """คืนจำนวนสินค้าที่ค้นพบ."""

        return len(self.products)

    @property
    def task_count(self) -> int:
        """คืนจำนวน Search Task."""

        return len(
            self.search_plan.tasks
        )

    @property
    def found_products(self) -> bool:
        """คืน True เมื่อพบสินค้าอย่างน้อยหนึ่งรายการ."""

        return bool(self.products)


def _select_tasks(
    search_plan: SearchPlan,
    task_limit: int,
) -> list[SearchTask]:
    """เลือก Search Task ตามลำดับ Priority."""

    if task_limit <= 0:
        return []

    return search_plan.tasks[
        :task_limit
    ]


def _search_task(
    task: SearchTask,
    product_limit: int,
) -> list[dict[str, Any]]:
    """ค้นสินค้าสำหรับ Search Task หนึ่งรายการ."""

    if product_limit <= 0:
        return []

    keyword = task.keyword.strip()

    if not keyword:
        return []

    return search_products_any_term(
        search_terms=[
            keyword
        ],
        limit=product_limit,
    )


def execute_search(
    message: str,
    product_limit: int = DEFAULT_PRODUCT_LIMIT,
    task_limit: int = DEFAULT_TASK_LIMIT,
    graph_limit_per_task: int = (
        DEFAULT_GRAPH_LIMIT_PER_TASK
    ),
    product_limit_per_task: int = (
        DEFAULT_PRODUCT_LIMIT_PER_TASK
    ),
) -> SearchExecutionResult:
    """
    สร้าง Search Plan ค้นหลายคำ รวมผล และสรุปสินค้า.

    ขั้นตอน:
    1. สร้าง Search Plan
    2. ค้นสินค้าตาม Task
    3. รวมและตัดรายการซ้ำ
    4. สรุปข้อมูลด้วย Product Intelligence
    """

    cleaned_message = message.strip()

    search_plan = create_search_plan(
        message=cleaned_message,
        max_tasks=max(
            task_limit,
            0,
        ),
        graph_limit_per_task=max(
            graph_limit_per_task,
            0,
        ),
    )

    if (
        not cleaned_message
        or product_limit <= 0
        or task_limit <= 0
    ):
        return SearchExecutionResult(
            message=cleaned_message,
            search_plan=search_plan,
            summary=summarize_products(
                []
            ),
        )

    result_groups: list[
        list[dict[str, Any]]
    ] = []

    searched_keywords: list[str] = []

    selected_tasks = _select_tasks(
        search_plan=search_plan,
        task_limit=task_limit,
    )

    for task in selected_tasks:
        keyword = task.keyword.strip()

        if not keyword:
            continue

        searched_keywords.append(
            keyword
        )

        task_products = _search_task(
            task=task,
            product_limit=product_limit_per_task,
        )

        if task_products:
            result_groups.append(
                task_products
            )

    products = merge_product_results(
        result_groups=result_groups,
        limit=product_limit,
    )

    summary = summarize_products(
        products
    )

    return SearchExecutionResult(
        message=cleaned_message,
        search_plan=search_plan,
        products=products,
        summary=summary,
        searched_keywords=searched_keywords,
    )


class SearchExecutor:
    """Facade สำหรับเรียกกระบวนการค้นหาสินค้า."""

    def __init__(
        self,
        product_limit: int = DEFAULT_PRODUCT_LIMIT,
        task_limit: int = DEFAULT_TASK_LIMIT,
        graph_limit_per_task: int = (
            DEFAULT_GRAPH_LIMIT_PER_TASK
        ),
        product_limit_per_task: int = (
            DEFAULT_PRODUCT_LIMIT_PER_TASK
        ),
    ) -> None:
        self.product_limit = (
            product_limit
        )

        self.task_limit = (
            task_limit
        )

        self.graph_limit_per_task = (
            graph_limit_per_task
        )

        self.product_limit_per_task = (
            product_limit_per_task
        )

    def search(
        self,
        message: str,
    ) -> SearchExecutionResult:
        """ค้นและสรุปสินค้าจากข้อความลูกค้า."""

        return execute_search(
            message=message,
            product_limit=self.product_limit,
            task_limit=self.task_limit,
            graph_limit_per_task=(
                self.graph_limit_per_task
            ),
            product_limit_per_task=(
                self.product_limit_per_task
            ),
        )


def print_search_result(
    result: SearchExecutionResult,
) -> None:
    """แสดงผลสำหรับ Developer Mode."""

    print("=" * 60)
    print("Search Executor")
    print("=" * 60)

    print(
        "ข้อความ:",
        result.message,
    )

    print(
        "Search Tasks:",
        result.task_count,
    )

    print(
        "Keywords:",
        result.searched_keywords,
    )

    print(
        "Products:",
        result.product_count,
    )

    print(
        "Summary:",
        result.summary,
    )

    print("=" * 60)


def main() -> None:
    """ทดสอบ Search Executor แบบรับข้อความ."""

    message = input(
        "ข้อความสำหรับค้นหาสินค้า: "
    ).strip()

    result = execute_search(
        message
    )

    print_search_result(
        result
    )


if __name__ == "__main__":
    main()
    