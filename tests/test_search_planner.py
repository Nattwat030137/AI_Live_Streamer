"""ทดสอบ Search Planner V2."""

from app.search_planner import (
    create_search_plan,
    print_search_plan,
)


def assert_task_exists(
    plan,
    keyword: str,
) -> None:
    """ตรวจว่ามี Keyword อยู่ใน Search Plan."""

    task_keywords = [
        task.keyword
        for task in plan.tasks
    ]

    assert keyword in task_keywords, (
        f"ไม่พบ keyword={keyword!r} "
        f"ใน {task_keywords}"
    )


def main() -> None:
    """ทดสอบข้อความหลายรูปแบบ."""

    test_messages = [
        "มีถ้วยคัพเค้กรุ่น 5040 ไหม",
        "ทำบราวนี่",
        "ห่อคุกกี้",
        "ใส่เค้กวันเกิด",
    ]

    plans = {}

    for message in test_messages:
        plan = create_search_plan(
            message=message,
            max_tasks=15,
            graph_limit_per_task=6,
        )

        plans[message] = plan

        print()
        print(f"ข้อความ: {message}")
        print_search_plan(plan)

    cupcake_plan = plans[
        "มีถ้วยคัพเค้กรุ่น 5040 ไหม"
    ]

    assert "5040" in cupcake_plan.extracted_models
    assert_task_exists(
        cupcake_plan,
        "5040",
    )

    brownie_plan = plans[
        "ทำบราวนี่"
    ]

    assert_task_exists(
        brownie_plan,
        "บราวนี่",
    )

    cookie_plan = plans[
        "ห่อคุกกี้"
    ]

    assert_task_exists(
        cookie_plan,
        "คุกกี้",
    )

    birthday_plan = plans[
        "ใส่เค้กวันเกิด"
    ]

    assert_task_exists(
        birthday_plan,
        "เค้กวันเกิด",
    )

    birthday_keywords = [
        task.keyword
        for task in birthday_plan.tasks
    ]

    assert "ใส" not in birthday_keywords

    print("=" * 60)
    print("Search Planner V2 ผ่านการทดสอบทั้งหมด")
    print("=" * 60)


if __name__ == "__main__":
    main()