"""สร้าง Prompt จากข้อมูลสินค้า บริบท และกลยุทธ์การขาย."""

from __future__ import annotations

import json
from typing import Any

from app.core.customer_intent_score import (
    CustomerIntentScore,
    get_sales_response_strategy,
)
from app.core.recommendation_search import (
    RecommendationSearchResult,
    format_recommendation_search,
)
from app.core.search_executor import (
    SearchExecutionResult,
)
from app.knowledge_engine import (
    load_all_knowledge,
)
from app.prompt_loader import load_prompt
from app.search_planner import SearchPlan


DEFAULT_PRODUCT_EXAMPLE_LIMIT = 3
DEFAULT_SEARCH_PLAN_LIMIT = 8
DEFAULT_RECOMMENDATION_ITEM_LIMIT = 3
DEFAULT_RECOMMENDATION_PRODUCT_LIMIT = 2

SALES_PROMPT = load_prompt(
    "sales_prompt.txt"
)


def join_thai_items(
    items: list[str],
) -> str:
    """รวมรายการภาษาไทยให้อ่านเป็นธรรมชาติ."""

    cleaned_items: list[str] = []

    for item in items:
        cleaned_item = str(
            item
        ).strip()

        if not cleaned_item:
            continue

        if cleaned_item in cleaned_items:
            continue

        cleaned_items.append(
            cleaned_item
        )

    if not cleaned_items:
        return ""

    if len(cleaned_items) == 1:
        return cleaned_items[0]

    if len(cleaned_items) == 2:
        return (
            f"{cleaned_items[0]} "
            f"และ{cleaned_items[1]}"
        )

    return (
        ", ".join(
            cleaned_items[:-1]
        )
        + f" และ{cleaned_items[-1]}"
    )


def format_product_summary(
    summary: dict[str, Any],
) -> str:
    """จัด Product Summary ให้ AI อ่านง่าย."""

    if (
        not summary
        or summary.get(
            "count",
            0,
        ) == 0
    ):
        return (
            "ไม่พบสินค้าที่ตรงกับคำค้นหา"
            "ในฐานข้อมูล"
        )

    count = int(
        summary.get(
            "count",
            0,
        )
    )

    model = summary.get(
        "model"
    )

    colors = summary.get(
        "colors",
        [],
    )

    finish = summary.get(
        "finish",
        [],
    )

    pack_size = summary.get(
        "pack_size"
    )

    lines: list[str] = [
        (
            "จำนวนรายการที่เกี่ยวข้อง: "
            f"{count}"
        )
    ]

    if model:
        lines.append(
            f"รุ่นสินค้า: {model}"
        )

    if (
        isinstance(
            colors,
            list,
        )
        and colors
    ):
        color_text = join_thai_items(
            [
                str(color)
                for color in colors
            ]
        )

        if color_text:
            lines.append(
                f"สีที่พบ: {color_text}"
            )

    if (
        isinstance(
            finish,
            list,
        )
        and finish
    ):
        finish_text = join_thai_items(
            [
                str(item)
                for item in finish
            ]
        )

        if finish_text:
            lines.append(
                f"รูปแบบที่พบ: {finish_text}"
            )

    if pack_size:
        lines.append(
            f"จำนวนบรรจุ: {pack_size} ต่อแพ็ก"
        )

    return "\n".join(
        lines
    )


def format_product_examples(
    products: list[dict[str, Any]],
    limit: int = DEFAULT_PRODUCT_EXAMPLE_LIMIT,
) -> str:
    """จัดตัวอย่างสินค้าจริงแบบกระชับ."""

    if (
        not products
        or limit <= 0
    ):
        return "ไม่มีตัวอย่างสินค้า"

    lines: list[str] = []

    for number, product in enumerate(
        products[:limit],
        start=1,
    ):
        product_name = str(
            product.get(
                "product_name",
                "",
            )
        ).strip()

        sku = str(
            product.get(
                "sku",
                "",
            )
        ).strip()

        description = str(
            product.get(
                "description",
                "",
            )
        ).strip()

        if not product_name:
            product_name = (
                "ไม่มีชื่อสินค้า"
            )

        lines.append(
            f"{number}. ชื่อสินค้า: "
            f"{product_name}"
        )

        if sku:
            lines.append(
                f"   SKU: {sku}"
            )

        if (
            description
            and description != "-"
        ):
            lines.append(
                f"   รายละเอียด: "
                f"{description}"
            )

    return "\n".join(
        lines
    )


def format_search_plan(
    search_plan: SearchPlan,
    limit: int = DEFAULT_SEARCH_PLAN_LIMIT,
) -> str:
    """จัด Search Plan เป็นข้อความสำหรับ AI."""

    if (
        not search_plan.tasks
        or limit <= 0
    ):
        return "ไม่มี Search Task"

    lines: list[str] = []

    for number, task in enumerate(
        search_plan.tasks[:limit],
        start=1,
    ):
        lines.append(
            f"{number}. "
            f"keyword={task.keyword!r}, "
            f"priority={task.priority}, "
            f"score={task.score}, "
            f"source={task.source}"
        )

    return "\n".join(
        lines
    )


def format_knowledge(
    knowledge: dict[str, Any],
) -> str:
    """แปลง Knowledge เป็น JSON ภาษาไทยที่อ่านง่าย."""

    return json.dumps(
        knowledge,
        ensure_ascii=False,
        indent=2,
    )


def build_recommendation_context(
    recommendation_result: (
        RecommendationSearchResult | None
    ),
) -> str:
    """จัดข้อมูลสินค้าแนะนำจริงสำหรับ Prompt."""

    if recommendation_result is None:
        return (
            "ยังไม่ได้วิเคราะห์"
            "สินค้าแนะนำเพิ่มเติม"
        )

    return format_recommendation_search(
        result=recommendation_result,
        item_limit=(
            DEFAULT_RECOMMENDATION_ITEM_LIMIT
        ),
        product_limit=(
            DEFAULT_RECOMMENDATION_PRODUCT_LIMIT
        ),
    )


def build_customer_intent_context(
    customer_intent: (
        CustomerIntentScore | None
    ),
) -> str:
    """จัดสถานะลูกค้าและกลยุทธ์การตอบสำหรับ Prompt."""

    if customer_intent is None:
        return (
            "ยังไม่ได้วิเคราะห์"
            "ระดับความตั้งใจของลูกค้า"
        )

    matched_keywords = (
        ", ".join(
            customer_intent.matched_keywords
        )
        if customer_intent.matched_keywords
        else "ไม่พบคำที่ตรง"
    )

    strategy = get_sales_response_strategy(
        customer_intent
    )

    return "\n".join(
        [
            (
                "Customer Stage: "
                f"{customer_intent.stage.value}"
            ),
            (
                "Intent Score: "
                f"{customer_intent.score}"
            ),
            (
                "Matched Keywords: "
                f"{matched_keywords}"
            ),
            (
                "Reason: "
                f"{customer_intent.reason}"
            ),
            (
                "Sales Response Strategy: "
                f"{strategy}"
            ),
        ]
    )


def build_prompt(
    search_result: SearchExecutionResult,
    knowledge: dict[str, Any] | None = None,
    recommendation_result: (
        RecommendationSearchResult | None
    ) = None,
    customer_intent: (
        CustomerIntentScore | None
    ) = None,
) -> str:
    """สร้างคำสั่งหลักสำหรับ OpenAI."""

    selected_knowledge = (
        knowledge
        if knowledge is not None
        else load_all_knowledge()
    )

    knowledge_text = format_knowledge(
        selected_knowledge
    )

    search_plan_text = format_search_plan(
        search_plan=(
            search_result.search_plan
        ),
        limit=DEFAULT_SEARCH_PLAN_LIMIT,
    )

    summary_text = (
        format_product_summary(
            search_result.summary
        )
    )

    examples_text = (
        format_product_examples(
            products=(
                search_result.products
            ),
            limit=(
                DEFAULT_PRODUCT_EXAMPLE_LIMIT
            ),
        )
    )

    recommendation_text = (
        build_recommendation_context(
            recommendation_result
        )
    )

    customer_intent_text = (
        build_customer_intent_context(
            customer_intent
        )
    )

    return f"""
{SALES_PROMPT}

ข้อมูลคำถามของลูกค้า

{search_result.message}

สถานะและระดับความตั้งใจของลูกค้า

{customer_intent_text}

แผนการค้นหาที่ระบบสร้าง

{search_plan_text}

ข้อมูลสินค้าหลักที่ระบบสรุปแล้ว

{summary_text}

ตัวอย่างสินค้าหลักที่เกี่ยวข้อง

{examples_text}

ข้อมูลสินค้าแนะนำเพิ่มเติมที่พบจริง

{recommendation_text}

ข้อมูลร้านและความรู้ของระบบ

{knowledge_text}

กฎสำคัญเพิ่มเติม

1. ตอบจากข้อมูลที่ได้รับเท่านั้น
2. ห้ามเดาราคา โปรโมชั่น สต็อก หรือคุณสมบัติสินค้า
3. ห้ามแจ้งจำนวนขาย เพราะเป็นข้อมูลภายใน
4. ห้ามอ่านข้อความชื่อสินค้ายาวทั้งหมด
5. สรุปชื่อสินค้าให้อยู่ในรูปแบบที่ลูกค้าเข้าใจง่าย
6. ตอบไม่เกิน 2 ถึง 3 ประโยค
7. ปรับสำนวนตาม Customer Stage และ Sales Response Strategy
8. ถ้าลูกค้าพร้อมซื้อ ให้ตอบกระชับและบอกขั้นตอนถัดไป
9. ถ้าลูกค้ากำลังเปรียบเทียบ ให้สรุปความแตกต่างอย่างเป็นกลาง
10. ถ้าลูกค้าลังเล ให้ช่วยลดข้อกังวลโดยไม่กดดัน
11. ถ้าลูกค้าเพียงสอบถามข้อมูล ให้ตอบตรงคำถามก่อน
12. หากพบหลายสี ให้รวมเป็นประโยคเดียว
13. หากพบทั้งแบบเคลือบและไม่เคลือบ ให้แจ้งว่ามีทั้งสองแบบ
14. หากไม่พบสินค้าหลัก ห้ามบอกว่าทางร้านมีสินค้าหลัก
15. แนะนำสินค้าเพิ่มเติมเฉพาะรายการที่พบจริงในฐานข้อมูล
16. แนะนำสินค้าเพิ่มเติมไม่เกิน 2 รายการต่อคำตอบ
17. ห้ามบังคับขายหรือพูดเร่งรัดลูกค้า
18. หากข้อมูลไม่เพียงพอ ให้ขออนุญาตให้แอดมินตรวจสอบ
19. ไม่ต้องพูดชื่อช่องทางขาย เว้นแต่ลูกค้าถาม
20. ไม่ต้องพูด SKU เว้นแต่ลูกค้าถามหารหัสสินค้า
21. ใช้คำว่า ค่ะ คะ และนะคะให้ถูกประเภท
""".strip()


class PromptBuilder:
    """Facade สำหรับสร้าง Prompt ของ AI Engine."""

    def __init__(
        self,
        knowledge: (
            dict[str, Any] | None
        ) = None,
    ) -> None:
        self.knowledge = knowledge

    def build(
        self,
        search_result: SearchExecutionResult,
        recommendation_result: (
            RecommendationSearchResult | None
        ) = None,
        customer_intent: (
            CustomerIntentScore | None
        ) = None,
    ) -> str:
        """สร้าง Prompt พร้อมสินค้าแนะนำและ Intent Score."""

        return build_prompt(
            search_result=search_result,
            knowledge=self.knowledge,
            recommendation_result=(
                recommendation_result
            ),
            customer_intent=(
                customer_intent
            ),
        )