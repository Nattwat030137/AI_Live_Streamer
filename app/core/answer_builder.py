"""สร้างคำตอบสำเร็จรูปตาม Intent โดยไม่เรียก OpenAI."""

from __future__ import annotations

from typing import Any

from app.core.prompt_builder import join_thai_items
from app.core.search_executor import SearchExecutionResult
from app.intent_engine import Intent


DEFAULT_STORE_NAME = "Bakery D'Ver"
DEFAULT_BUSINESS_TYPE = "ร้านจำหน่ายอุปกรณ์ทำเบเกอรี่"
DEFAULT_SHIPPING_AREA = "ทั่วประเทศไทย"


def build_price_answer(
    search_result: SearchExecutionResult,
) -> str:
    """สร้างคำตอบเรื่องราคาโดยไม่แต่งราคาขึ้นเอง."""

    if not search_result.found_products:
        return (
            "ขออภัยค่ะ ตอนนี้ยังไม่พบสินค้าที่ตรงกับคำค้นหา "
            "ขออนุญาตให้แอดมินตรวจสอบข้อมูลให้นะคะ"
        )

    model = search_result.summary.get(
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
        "ขออนุญาตให้แอดมินตรวจสอบราคาล่าสุดให้นะคะ"
    )


def build_stock_answer(
    search_result: SearchExecutionResult,
) -> str:
    """สร้างคำตอบเรื่องสต็อกโดยไม่เดาจำนวนสินค้า."""

    if not search_result.found_products:
        return (
            "ขออภัยค่ะ ตอนนี้ยังไม่พบสินค้าที่ตรงกับคำค้นหา "
            "ขออนุญาตให้แอดมินตรวจสอบข้อมูลให้นะคะ"
        )

    model = search_result.summary.get(
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
        f"ทางร้านพบข้อมูล{product_reference}ในระบบค่ะ "
        "แต่สต็อกอาจมีการเปลี่ยนแปลง "
        "ขออนุญาตให้แอดมินตรวจสอบสต็อกล่าสุดให้นะคะ"
    )


def build_shipping_answer(
    knowledge: dict[str, Any],
) -> str:
    """สร้างคำตอบจากข้อมูลการจัดส่ง."""

    shipping = knowledge.get(
        "shipping",
        {},
    )

    if not isinstance(
        shipping,
        dict,
    ):
        shipping = {}

    shipping_area = str(
        shipping.get(
            "shipping_area",
            DEFAULT_SHIPPING_AREA,
        )
    ).strip()

    if not shipping_area:
        shipping_area = (
            DEFAULT_SHIPPING_AREA
        )

    companies = shipping.get(
        "shipping_companies",
        [],
    )

    if not isinstance(
        companies,
        list,
    ):
        companies = []

    company_names = [
        str(company).strip()
        for company in companies
        if str(company).strip()
    ]

    delivery_time = str(
        shipping.get(
            "delivery_time",
            "",
        )
    ).strip()

    answer = (
        f"ทางร้านจัดส่ง{shipping_area}ค่ะ"
    )

    if company_names:
        answer += (
            " โดยใช้ "
            + join_thai_items(
                company_names
            )
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
    """สร้างคำตอบเกี่ยวกับร้านและการรับสินค้าเอง."""

    store = knowledge.get(
        "store",
        {},
    )

    if not isinstance(
        store,
        dict,
    ):
        store = {}

    store_name = str(
        store.get(
            "store_name",
            DEFAULT_STORE_NAME,
        )
    ).strip()

    if not store_name:
        store_name = DEFAULT_STORE_NAME

    business_type = str(
        store.get(
            "business_type",
            DEFAULT_BUSINESS_TYPE,
        )
    ).strip()

    if not business_type:
        business_type = (
            DEFAULT_BUSINESS_TYPE
        )

    country = str(
        store.get(
            "country",
            "ประเทศไทย",
        )
    ).strip()

    if not country:
        country = "ประเทศไทย"

    return (
        f"{store_name} เป็น{business_type}ค่ะ "
        f"ให้บริการลูกค้าใน{country} "
        "หากต้องการข้อมูลหน้าร้านหรือรับสินค้าเอง "
        "ขออนุญาตให้แอดมินตรวจสอบให้นะคะ"
    )


def build_category_answer(
    knowledge: dict[str, Any],
    limit: int = 5,
) -> str:
    """สร้างคำตอบเกี่ยวกับหมวดสินค้า."""

    categories_data = knowledge.get(
        "categories",
        {},
    )

    if not isinstance(
        categories_data,
        dict,
    ):
        categories_data = {}

    categories = categories_data.get(
        "categories",
        [],
    )

    if not isinstance(
        categories,
        list,
    ):
        categories = []

    category_names: list[str] = []

    for category in categories:
        category_name = str(
            category
        ).strip()

        if not category_name:
            continue

        if category_name in category_names:
            continue

        category_names.append(
            category_name
        )

    if not category_names:
        return (
            "ทางร้านจำหน่ายอุปกรณ์ทำเบเกอรี่"
            "และบรรจุภัณฑ์เบเกอรี่ค่ะ "
            "สนใจสินค้าแบบไหนสอบถามได้เลยนะคะ"
        )

    selected_categories = (
        category_names[:max(limit, 0)]
    )

    if not selected_categories:
        return (
            "ทางร้านมีสินค้าหลายหมวดค่ะ "
            "สนใจสินค้าแบบไหนสอบถามได้เลยนะคะ"
        )

    return (
        "ทางร้านมีสินค้าหลายหมวดค่ะ เช่น "
        f"{join_thai_items(selected_categories)} "
        "สนใจหมวดไหนสอบถามได้เลยนะคะ"
    )


class AnswerBuilder:
    """สร้างคำตอบสำเร็จรูปสำหรับ Intent ที่ไม่ต้องเรียก OpenAI."""

    SUPPORTED_INTENTS = {
        Intent.PRICE,
        Intent.STOCK,
        Intent.SHIPPING,
        Intent.STORE,
        Intent.CATEGORY,
    }

    def supports(
        self,
        intent: Intent,
    ) -> bool:
        """ตรวจว่า Intent นี้มีคำตอบสำเร็จรูปหรือไม่."""

        return intent in self.SUPPORTED_INTENTS

    def build(
        self,
        intent: Intent,
        search_result: SearchExecutionResult,
        knowledge: dict[str, Any],
    ) -> str | None:
        """สร้างคำตอบตาม Intent หรือคืน None เมื่อไม่รองรับ."""

        if intent == Intent.PRICE:
            return build_price_answer(
                search_result
            )

        if intent == Intent.STOCK:
            return build_stock_answer(
                search_result
            )

        if intent == Intent.SHIPPING:
            return build_shipping_answer(
                knowledge
            )

        if intent == Intent.STORE:
            return build_store_answer(
                knowledge
            )

        if intent == Intent.CATEGORY:
            return build_category_answer(
                knowledge
            )

        return None