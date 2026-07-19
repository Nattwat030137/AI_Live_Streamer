"""AI Engine V2 สำหรับตอบลูกค้า พร้อม Intent และ Search Planner."""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from app.conversation_memory import ConversationMemory
from app.intent_engine import Intent, detect_intent
from app.knowledge_engine import load_all_knowledge
from app.product_intelligence import summarize_products
from app.product_search import (
    merge_product_results,
    search_products_any_term,
)
from app.prompt_loader import load_prompt
from app.search_planner import SearchPlan, create_search_plan
from config.settings import OPENAI_API_KEY


AI_MODEL = "gpt-5-mini"
PRODUCT_SEARCH_LIMIT = 10
SEARCH_TASK_LIMIT = 12
PER_TASK_PRODUCT_LIMIT = 10
SEARCH_PLAN_PROMPT_LIMIT = 8
PRODUCT_EXAMPLE_LIMIT = 3

SALES_PROMPT = load_prompt(
    "sales_prompt.txt"
)

memory = ConversationMemory(
    max_messages=10,
)


def create_client() -> OpenAI:
    """สร้าง OpenAI Client."""

    if not OPENAI_API_KEY:
        raise ValueError(
            "ไม่พบ OPENAI_API_KEY"
        )

    return OpenAI(
        api_key=OPENAI_API_KEY
    )


def join_thai_items(
    items: list[str],
) -> str:
    """รวมข้อความภาษาไทยให้อ่านเป็นธรรมชาติ."""

    cleaned_items = [
        str(item).strip()
        for item in items
        if str(item).strip()
    ]

    if not cleaned_items:
        return ""

    if len(cleaned_items) == 1:
        return cleaned_items[0]

    if len(cleaned_items) == 2:
        return (
            f"{cleaned_items[0]}"
            f"และ{cleaned_items[1]}"
        )

    return (
        ", ".join(cleaned_items[:-1])
        + f" และ{cleaned_items[-1]}"
    )


def format_product_summary(
    summary: dict[str, Any],
) -> str:
    """จัดข้อมูลสรุปสินค้าให้อยู่ในรูปแบบที่ AI อ่านง่าย."""

    if (
        not summary
        or summary.get("count", 0) == 0
    ):
        return "ไม่พบสินค้า"

    lines: list[str] = [
        (
            "จำนวนรายการที่เกี่ยวข้อง: "
            f"{summary.get('count', 0)}"
        )
    ]

    model = summary.get("model")
    colors = summary.get("colors", [])
    finish = summary.get("finish", [])
    pack_size = summary.get("pack_size")

    if model:
        lines.append(
            f"รุ่น: {model}"
        )

    if colors:
        lines.append(
            "สี: "
            + join_thai_items(colors)
        )

    if finish:
        lines.append(
            "รูปแบบ: "
            + join_thai_items(finish)
        )

    if pack_size:
        lines.append(
            f"บรรจุ: {pack_size}"
        )

    return "\n".join(lines)


def format_product_examples(
    products: list[dict[str, Any]],
    limit: int = PRODUCT_EXAMPLE_LIMIT,
) -> str:
    """จัดตัวอย่างสินค้าที่เกี่ยวข้องแบบกระชับ."""

    if not products:
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

        lines.append(
            f"{number}. {product_name}"
        )

        if sku:
            lines.append(
                f"   SKU: {sku}"
            )

    return "\n".join(lines)


def format_search_plan(
    search_plan: SearchPlan,
    limit: int = SEARCH_PLAN_PROMPT_LIMIT,
) -> str:
    """จัด Search Plan เป็นข้อความสำหรับ Prompt."""

    if not search_plan.tasks:
        return "ไม่มี Search Task"

    lines: list[str] = []

    for number, task in enumerate(
        search_plan.tasks[:limit],
        start=1,
    ):
        lines.append(
            f"{number}. {task.keyword} "
            f"(priority={task.priority}, "
            f"source={task.source}, "
            f"score={task.score})"
        )

    return "\n".join(lines)


def collect_products_from_plan(
    message: str,
    limit: int = PRODUCT_SEARCH_LIMIT,
) -> tuple[
    SearchPlan,
    list[dict[str, Any]],
]:
    """สร้าง Search Plan ค้นหลายคำ และรวมผลลัพธ์."""

    search_plan = create_search_plan(
        message=message,
        max_tasks=SEARCH_TASK_LIMIT,
        graph_limit_per_task=6,
    )

    result_groups: list[
        list[dict[str, Any]]
    ] = []

    for task in search_plan.tasks:
        task_results = search_products_any_term(
            search_terms=[
                task.keyword
            ],
            limit=PER_TASK_PRODUCT_LIMIT,
        )

        if task_results:
            result_groups.append(
                task_results
            )

    products = merge_product_results(
        result_groups=result_groups,
        limit=limit,
    )

    return (
        search_plan,
        products,
    )
def build_prompt(
    products: list[dict[str, Any]],
    summary: dict[str, Any],
    search_plan: SearchPlan,
) -> str:
    """สร้าง Prompt จากข้อมูลร้าน สินค้า และแผนค้นหา."""

    knowledge = load_all_knowledge()

    knowledge_text = json.dumps(
        knowledge,
        ensure_ascii=False,
        indent=2,
    )

    summary_text = format_product_summary(
        summary
    )

    product_examples_text = format_product_examples(
        products=products,
        limit=PRODUCT_EXAMPLE_LIMIT,
    )

    search_plan_text = format_search_plan(
        search_plan=search_plan,
        limit=SEARCH_PLAN_PROMPT_LIMIT,
    )

    return f"""
{SALES_PROMPT}

ข้อมูลร้านและความรู้ของระบบ

{knowledge_text}

แผนการค้นหาที่ระบบสร้าง

{search_plan_text}

ข้อมูลสินค้าที่สรุปแล้ว

{summary_text}

ตัวอย่างสินค้าจริงที่เกี่ยวข้อง

{product_examples_text}

กฎเพิ่มเติม

1. ใช้ข้อมูลสินค้าและข้อมูลร้านที่ให้มาเท่านั้น
2. ห้ามเดาข้อมูลที่ไม่มีอยู่ในระบบ
3. ห้ามแต่งราคา โปรโมชั่น หรือสต็อก
4. ห้ามแจ้งจำนวนขายของสินค้า
5. ห้ามอ่านข้อความชื่อสินค้ายาวทั้งหมด
6. ให้สรุปข้อมูลสินค้าเป็นภาษาที่ลูกค้าเข้าใจง่าย
7. ตอบไม่เกิน 2 ถึง 3 ประโยค
8. หากไม่พบสินค้า ห้ามบอกว่าทางร้านมีสินค้า
9. หากข้อมูลไม่เพียงพอ ให้ขออนุญาตให้แอดมินตรวจสอบ
10. ใช้คำว่า ค่ะ คะ และนะคะให้ถูกต้อง
""".strip()


def build_price_answer(
    products: list[dict[str, Any]],
    summary: dict[str, Any],
) -> str:
    """สร้างคำตอบเมื่อลูกค้าถามราคา."""

    if not products:
        return (
            "ขออภัยค่ะ ตอนนี้ยังไม่พบสินค้า"
            "ที่ตรงกับคำค้นหา "
            "ขออนุญาตให้แอดมินตรวจสอบให้นะคะ"
        )

    model = summary.get(
        "model"
    )

    if model:
        product_reference = (
            f"รุ่น {model}"
        )
    else:
        product_reference = (
            "สินค้าที่สนใจ"
        )

    return (
        f"ทางร้านมี{product_reference}หลายแบบค่ะ "
        "ราคาจะแตกต่างกันตามรุ่น ขนาด และรูปแบบ "
        "ขออนุญาตให้แอดมินตรวจสอบราคาล่าสุด"
        "ของแบบที่สนใจให้นะคะ"
    )


def build_stock_answer(
    products: list[dict[str, Any]],
    summary: dict[str, Any],
) -> str:
    """สร้างคำตอบเมื่อลูกค้าถามสต็อก."""

    if not products:
        return (
            "ขออภัยค่ะ ตอนนี้ยังไม่พบสินค้า"
            "ที่ตรงกับคำค้นหา "
            "ขออนุญาตให้แอดมินตรวจสอบให้นะคะ"
        )

    model = summary.get(
        "model"
    )

    if model:
        product_reference = (
            f"รุ่น {model}"
        )
    else:
        product_reference = (
            "สินค้าที่สนใจ"
        )

    return (
        f"ทางร้านพบข้อมูล{product_reference}"
        "ในระบบค่ะ "
        "แต่สต็อกอาจมีการเปลี่ยนแปลง "
        "ขออนุญาตให้แอดมินตรวจสอบ"
        "สต็อกล่าสุดให้นะคะ"
    )


def build_shipping_answer(
    knowledge: dict[str, Any],
) -> str:
    """สร้างคำตอบจากข้อมูลการจัดส่ง."""

    shipping = knowledge.get(
        "shipping",
        {},
    )

    shipping_area = str(
        shipping.get(
            "shipping_area",
            "ทั่วประเทศไทย",
        )
    ).strip()

    companies = shipping.get(
        "shipping_companies",
        [],
    )

    delivery_time = str(
        shipping.get(
            "delivery_time",
            "",
        )
    ).strip()

    company_names = [
        str(company).strip()
        for company in companies
        if str(company).strip()
    ]

    if company_names:
        company_text = join_thai_items(
            company_names
        )

        answer = (
            f"ทางร้านจัดส่ง{shipping_area}ค่ะ "
            f"โดยใช้ {company_text}"
        )
    else:
        answer = (
            f"ทางร้านจัดส่ง{shipping_area}ค่ะ"
        )

    if delivery_time:
        answer += (
            f" ระยะเวลาจัดส่ง"
            f"{delivery_time}นะคะ"
        )

    return answer
def build_store_answer(
    knowledge: dict[str, Any],
) -> str:
    """สร้างคำตอบเกี่ยวกับข้อมูลร้าน."""

    store = knowledge.get(
        "store",
        {},
    )

    store_name = str(
        store.get(
            "store_name",
            "Bakery D'Ver",
        )
    ).strip()

    business_type = str(
        store.get(
            "business_type",
            "ร้านจำหน่ายอุปกรณ์ทำเบเกอรี่",
        )
    ).strip()

    country = str(
        store.get(
            "country",
            "Thailand",
        )
    ).strip()

    return (
        f"{store_name} เป็น{business_type}ค่ะ "
        f"ให้บริการลูกค้าใน{country} "
        "หากต้องการข้อมูลหน้าร้านหรือการรับสินค้าเอง "
        "ขออนุญาตให้แอดมินตรวจสอบให้นะคะ"
    )


def build_category_answer(
    knowledge: dict[str, Any],
) -> str:
    """สร้างคำตอบเกี่ยวกับหมวดสินค้า."""

    categories_data = knowledge.get(
        "categories",
        {},
    )

    categories = categories_data.get(
        "categories",
        [],
    )

    category_names = [
        str(category).strip()
        for category in categories
        if str(category).strip()
    ]

    if not category_names:
        return (
            "ทางร้านจำหน่ายอุปกรณ์ทำเบเกอรี่"
            "และบรรจุภัณฑ์เบเกอรี่ค่ะ"
        )

    selected_categories = (
        category_names[:5]
    )

    return (
        "ทางร้านมีสินค้าหลายหมวดค่ะ เช่น "
        f"{join_thai_items(selected_categories)} "
        "หากสนใจหมวดไหน แจ้งได้เลยนะคะ"
    )


def save_to_memory(
    user_message: str,
    assistant_message: str,
) -> None:
    """บันทึกข้อความผู้ใช้และคำตอบไว้ในความจำ."""

    memory.add_user_message(
        user_message
    )

    memory.add_assistant_message(
        assistant_message
    )


def ask_openai(
    message: str,
    products: list[dict[str, Any]],
    summary: dict[str, Any],
    search_plan: SearchPlan,
) -> str:
    """ส่งข้อความพร้อมบริบทให้ OpenAI ตอบ."""

    client = create_client()

    conversation = (
        memory.get_messages()
    )

    conversation.append(
        {
            "role": "user",
            "content": message,
        }
    )

    response = client.responses.create(
        model=AI_MODEL,
        instructions=build_prompt(
            products=products,
            summary=summary,
            search_plan=search_plan,
        ),
        input=conversation,
    )

    answer = (
        response.output_text.strip()
    )

    if not answer:
        return (
            "ขออนุญาตให้แอดมิน"
            "ตรวจสอบข้อมูลให้ค่ะ"
        )

    return answer


def build_product_context(
    message: str,
) -> tuple[
    SearchPlan,
    list[dict[str, Any]],
    dict[str, Any],
]:
    """
    สร้างบริบทสินค้าสำหรับ AI Engine

    คืนค่า:
    - Search Plan
    - ผลการค้นหาสินค้า
    - Product Summary
    """

    search_plan, products = (
        collect_products_from_plan(
            message=message,
            limit=PRODUCT_SEARCH_LIMIT,
        )
    )

    summary = summarize_products(
        products
    )

    return (
        search_plan,
        products,
        summary,
    )
