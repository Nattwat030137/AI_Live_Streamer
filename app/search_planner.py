"""Search Planner V2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.nlp import (
    extract_models,
    remove_stop_words,
    tokenize,
)

from app.product_graph_reader import (
    rank_related_keywords,
)


# --------------------------------------------------
# Data Classes
# --------------------------------------------------

@dataclass(slots=True)
class SearchTask:
    """งานค้นหาแต่ละรายการ."""

    keyword: str

    priority: int

    source: str

    score: int = 0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(slots=True)
class SearchPlan:
    """ผลลัพธ์ของ Search Planner."""

    original_query: str

    extracted_models: list[str] = field(
        default_factory=list
    )

    extracted_tokens: list[str] = field(
        default_factory=list
    )

    tasks: list[SearchTask] = field(
        default_factory=list
    )


# --------------------------------------------------
# Utilities
# --------------------------------------------------

def add_task(
    plan: SearchPlan,
    keyword: str,
    priority: int,
    source: str,
    score: int = 0,
    metadata: dict[str, Any] | None = None,
) -> None:
    """เพิ่ม Search Task โดยไม่ให้ Keyword ซ้ำ."""

    keyword = keyword.strip()

    if not keyword:
        return

    for task in plan.tasks:

        if task.keyword == keyword:

            if priority > task.priority:
                task.priority = priority

            if score > task.score:
                task.score = score

            return

    plan.tasks.append(
        SearchTask(
            keyword=keyword,
            priority=priority,
            source=source,
            score=score,
            metadata=metadata or {},
        )
    )
    # --------------------------------------------------
# Query analysis
# --------------------------------------------------

ACTION_PREFIXES = (
    "ทำ",
    "ห่อ",
    "ใส่",
    "ใส่ใน",
    "ใช้กับ",
    "สำหรับ",
    "ต้องการ",
    "อยากได้",
)


def extract_action_keywords(
    cleaned_query: str,
) -> list[str]:
    """
    ดึงคำหลักออกจากประโยคภาษาไทยที่มีคำกริยานำหน้า

    ตัวอย่าง:
    ทำบราวนี่ -> บราวนี่
    ห่อคุกกี้ -> คุกกี้
    ใส่เค้กวันเกิด -> เค้กวันเกิด
    """

    keywords: list[str] = []

    for prefix in sorted(
        ACTION_PREFIXES,
        key=len,
        reverse=True,
    ):
        if not cleaned_query.startswith(prefix):
            continue

        remainder = cleaned_query[
            len(prefix):
        ].strip()

        if remainder:
            keywords.append(remainder)

        break

    return keywords


def extract_query_tokens(
    cleaned_query: str,
) -> list[str]:
    """สร้าง Token ที่เหมาะสำหรับใช้ค้นสินค้า."""

    tokens = tokenize(
        cleaned_query
    )

    useful_tokens: list[str] = []

    for token in tokens:
        cleaned_token = token.strip()

        if not cleaned_token:
            continue

        if len(cleaned_token) < 2:
            continue

        if cleaned_token in useful_tokens:
            continue

        useful_tokens.append(
            cleaned_token
        )

    return useful_tokens


def add_question_tasks(
    plan: SearchPlan,
    cleaned_query: str,
) -> None:
    """เพิ่มงานค้นหาจากข้อความต้นฉบับและคำหลัก."""

    if cleaned_query:
        add_task(
            plan=plan,
            keyword=cleaned_query,
            priority=100,
            source="question",
            score=100,
            metadata={
                "reason": "cleaned_query",
            },
        )

    action_keywords = extract_action_keywords(
        cleaned_query
    )

    action_priority = 98

    for keyword in action_keywords:
        add_task(
            plan=plan,
            keyword=keyword,
            priority=action_priority,
            source="action",
            score=95,
            metadata={
                "reason": "action_prefix_removed",
            },
        )

        action_priority -= 3


def add_model_tasks(
    plan: SearchPlan,
) -> None:
    """เพิ่มงานค้นหาจากเลขรุ่นที่พบในคำถาม."""

    priority = 97

    for model in plan.extracted_models:
        add_task(
            plan=plan,
            keyword=model,
            priority=priority,
            source="model",
            score=100,
            metadata={
                "reason": "model_detected",
            },
        )

        priority -= 2


def add_token_tasks(
    plan: SearchPlan,
) -> None:
    """เพิ่มงานค้นหาจาก Token ที่แยกได้."""

    priority = 92

    for token in plan.extracted_tokens:
        if token in plan.extracted_models:
            continue

        add_task(
            plan=plan,
            keyword=token,
            priority=priority,
            source="token",
            score=90,
            metadata={
                "reason": "query_token",
            },
        )

        priority -= 3


def add_graph_tasks(
    plan: SearchPlan,
    graph_limit_per_task: int = 6,
) -> None:
    """ขยายงานค้นหาด้วย Keyword จาก Product Graph."""

    base_tasks = list(
        plan.tasks
    )

    for task in base_tasks:
        if task.source == "graph":
            continue

        ranked_keywords = rank_related_keywords(
            query=task.keyword,
            limit=graph_limit_per_task,
            minimum_score=60,
        )

        graph_priority = max(
            task.priority - 10,
            20,
        )

        for graph_keyword, graph_score in ranked_keywords:
            if graph_keyword == task.keyword:
                continue

            add_task(
                plan=plan,
                keyword=graph_keyword,
                priority=graph_priority,
                source="graph",
                score=graph_score,
                metadata={
                    "reason": "product_graph_match",
                    "parent_keyword": task.keyword,
                },
            )

            graph_priority = max(
                graph_priority - 3,
                20,
            )


def sort_and_limit_tasks(
    plan: SearchPlan,
    max_tasks: int,
) -> None:
    """เรียง Search Task และจำกัดจำนวนรายการ."""

    plan.tasks.sort(
        key=lambda task: (
            -task.priority,
            -task.score,
            len(task.keyword),
            task.keyword,
        )
    )

    if max_tasks <= 0:
        plan.tasks = []
        return

    plan.tasks = plan.tasks[
        :max_tasks
    ]
    # --------------------------------------------------
# Search plan builder
# --------------------------------------------------

def create_search_plan(
    message: str,
    max_tasks: int = 15,
    graph_limit_per_task: int = 6,
) -> SearchPlan:
    """สร้าง Search Plan จากข้อความของลูกค้า."""

    original_query = message.strip()

    plan = SearchPlan(
        original_query=original_query
    )

    if not original_query:
        return plan

    cleaned_query = remove_stop_words(
        original_query
    )

    plan.extracted_models = extract_models(
        cleaned_query
    )

    plan.extracted_tokens = extract_query_tokens(
        cleaned_query
    )

    add_question_tasks(
        plan=plan,
        cleaned_query=cleaned_query,
    )

    add_model_tasks(
        plan
    )

    add_token_tasks(
        plan
    )

    add_graph_tasks(
        plan=plan,
        graph_limit_per_task=graph_limit_per_task,
    )

    sort_and_limit_tasks(
        plan=plan,
        max_tasks=max_tasks,
    )

    return plan
def clone_search_plan_with_models(
    plan: SearchPlan,
    models: list[str],
    max_tasks: int = 15,
    graph_limit_per_task: int = 6,
) -> SearchPlan:
    """
    สร้าง SearchPlan ใหม่โดยใช้ Model ที่ Resolve จาก Memory
    โดยไม่แก้ไข SearchPlan เดิม
    """

    cleaned_query = remove_stop_words(
        plan.original_query
    )

    new_plan = SearchPlan(
        original_query=plan.original_query,
        extracted_models=list(models),
        extracted_tokens=list(
            plan.extracted_tokens
        ),
    )

    add_question_tasks(
        plan=new_plan,
        cleaned_query=cleaned_query,
    )

    add_model_tasks(
        new_plan
    )

    add_token_tasks(
        new_plan
    )

    add_graph_tasks(
        plan=new_plan,
        graph_limit_per_task=(
            graph_limit_per_task
        ),
    )

    sort_and_limit_tasks(
        plan=new_plan,
        max_tasks=max_tasks,
    )

    return new_plan


def search_plan_to_dict(
    plan: SearchPlan,
) -> dict[str, Any]:
    """แปลง Search Plan เป็น Dictionary."""

    return {
        "original_query": plan.original_query,
        "extracted_models": plan.extracted_models,
        "extracted_tokens": plan.extracted_tokens,
        "tasks": [
            {
                "keyword": task.keyword,
                "priority": task.priority,
                "source": task.source,
                "score": task.score,
                "metadata": task.metadata,
            }
            for task in plan.tasks
        ],
    }


def print_search_plan(
    plan: SearchPlan,
) -> None:
    """แสดง Search Plan สำหรับตรวจสอบ."""

    print("=" * 60)
    print("Search Plan V2")
    print("=" * 60)

    print(
        "Original Query:",
        plan.original_query,
    )

    print(
        "Models:",
        plan.extracted_models,
    )

    print(
        "Tokens:",
        plan.extracted_tokens,
    )

    print("-" * 60)

    if not plan.tasks:
        print("ไม่พบ Search Task")
        print("=" * 60)
        return

    for number, task in enumerate(
        plan.tasks,
        start=1,
    ):
        print(
            f"{number}. "
            f"keyword={task.keyword!r} | "
            f"priority={task.priority} | "
            f"score={task.score} | "
            f"source={task.source}"
        )

    print("=" * 60)


def main() -> None:
    """ทดสอบ Search Planner V2 แบบรับข้อความจากผู้ใช้."""

    message = input(
        "ข้อความสำหรับวางแผนค้นหา: "
    ).strip()

    plan = create_search_plan(
        message=message,
        max_tasks=15,
        graph_limit_per_task=6,
    )

    print_search_plan(
        plan
    )


if __name__ == "__main__":
    main()