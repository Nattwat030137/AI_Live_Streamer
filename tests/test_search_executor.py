"""ทดสอบ Search Executor."""

from app.core.search_executor import (
    SearchExecutor,
    execute_search,
)


def main() -> None:
    """ตรวจ Search Plan ผลค้นหา และ Product Summary."""

    cupcake_result = execute_search(
        message="มีถ้วยคัพเค้กรุ่น 5040 ไหม",
        product_limit=10,
        task_limit=12,
    )

    assert cupcake_result.message == (
        "มีถ้วยคัพเค้กรุ่น 5040 ไหม"
    )

    assert cupcake_result.task_count > 0

    assert cupcake_result.found_products

    assert cupcake_result.product_count <= 10

    assert cupcake_result.summary.get(
        "model"
    ) == "5040"

    assert cupcake_result.summary.get(
        "count",
        0,
    ) > 0

    assert "5040" in (
        cupcake_result.searched_keywords
    )

    brownie_result = execute_search(
        message="ทำบราวนี่",
        product_limit=5,
        task_limit=10,
    )

    brownie_tasks = [
        task.keyword
        for task
        in brownie_result.search_plan.tasks
    ]

    assert "บราวนี่" in brownie_tasks

    empty_result = execute_search(
        message="   "
    )

    assert empty_result.product_count == 0
    assert not empty_result.found_products

    executor = SearchExecutor(
        product_limit=5,
        task_limit=10,
    )

    executor_result = executor.search(
        "ห่อคุกกี้"
    )

    cookie_tasks = [
        task.keyword
        for task
        in executor_result.search_plan.tasks
    ]

    assert "คุกกี้" in cookie_tasks

    print("=" * 60)
    print("Search Executor ผ่านการทดสอบทั้งหมด")
    print("=" * 60)

    print(
        "รุ่น:",
        cupcake_result.summary.get(
            "model"
        ),
    )

    print(
        "จำนวนสินค้า:",
        cupcake_result.product_count,
    )

    print(
        "Keywords:",
        cupcake_result.searched_keywords,
    )

    print("=" * 60)


if __name__ == "__main__":
    main()
    