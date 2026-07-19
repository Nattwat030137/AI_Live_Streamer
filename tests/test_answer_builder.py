"""ทดสอบ Answer Builder."""

from app.core.answer_builder import (
    AnswerBuilder,
    build_category_answer,
    build_price_answer,
    build_shipping_answer,
    build_stock_answer,
    build_store_answer,
)
from app.core.search_executor import (
    SearchExecutionResult,
)
from app.intent_engine import Intent
from app.search_planner import SearchPlan


def create_search_result(
    found: bool = True,
) -> SearchExecutionResult:
    """สร้างผลค้นหาจำลอง."""

    search_plan = SearchPlan(
        original_query=(
            "มีถ้วยคัพเค้กรุ่น 5040 ไหม"
        )
    )

    if found:
        products = [
            {
                "product_name": (
                    "ถ้วยคัพเค้ก 5040"
                ),
                "sku": "5040",
            }
        ]

        summary = {
            "count": 1,
            "model": "5040",
            "colors": [
                "ขาว",
                "น้ำตาล",
            ],
            "finish": [
                "เคลือบ",
                "ไม่เคลือบ",
            ],
            "pack_size": "48-50 ใบ",
        }
    else:
        products = []
        summary = {
            "count": 0,
        }

    return SearchExecutionResult(
        message=(
            "มีถ้วยคัพเค้กรุ่น 5040 ไหม"
        ),
        search_plan=search_plan,
        products=products,
        summary=summary,
    )


def main() -> None:
    """ตรวจคำตอบทุกประเภท."""

    found_result = create_search_result(
        found=True
    )

    empty_result = create_search_result(
        found=False
    )

    knowledge = {
        "shipping": {
            "shipping_area": (
                "ทั่วประเทศไทย"
            ),
            "shipping_companies": [
                "Flash Express",
                "ไปรษณีย์ไทย",
            ],
            "delivery_time": (
                "ประมาณ 1–3 วันทำการ"
            ),
        },
        "store": {
            "store_name": "Bakery D'Ver",
            "business_type": (
                "ร้านจำหน่ายอุปกรณ์"
                "และบรรจุภัณฑ์เบเกอรี่"
            ),
            "country": "ประเทศไทย",
        },
        "categories": {
            "categories": [
                "ถ้วยคัพเค้ก",
                "กล่องเบเกอรี่",
                "ถุง",
                "อุปกรณ์ตกแต่ง",
                "พิมพ์อบ",
            ],
        },
    }

    price_answer = build_price_answer(
        found_result
    )

    assert "รุ่น 5040" in price_answer
    assert "แอดมิน" in price_answer
    assert "บาท" not in price_answer

    empty_price_answer = (
        build_price_answer(
            empty_result
        )
    )

    assert "ยังไม่พบสินค้า" in (
        empty_price_answer
    )

    stock_answer = build_stock_answer(
        found_result
    )

    assert "รุ่น 5040" in stock_answer
    assert "สต็อกล่าสุด" in stock_answer

    empty_stock_answer = (
        build_stock_answer(
            empty_result
        )
    )

    assert "ยังไม่พบสินค้า" in (
        empty_stock_answer
    )

    shipping_answer = (
        build_shipping_answer(
            knowledge
        )
    )

    assert "ทั่วประเทศไทย" in (
        shipping_answer
    )

    assert "Flash Express" in (
        shipping_answer
    )

    assert "1–3 วันทำการ" in (
        shipping_answer
    )

    store_answer = build_store_answer(
        knowledge
    )

    assert "Bakery D'Ver" in (
        store_answer
    )

    assert "ประเทศไทย" in (
        store_answer
    )

    category_answer = (
        build_category_answer(
            knowledge
        )
    )

    assert "ถ้วยคัพเค้ก" in (
        category_answer
    )

    assert "กล่องเบเกอรี่" in (
        category_answer
    )

    builder = AnswerBuilder()

    assert builder.supports(
        Intent.PRICE
    )

    assert builder.supports(
        Intent.STOCK
    )

    assert builder.supports(
        Intent.SHIPPING
    )

    assert builder.supports(
        Intent.STORE
    )

    assert builder.supports(
        Intent.CATEGORY
    )

    builder_price_answer = builder.build(
        intent=Intent.PRICE,
        search_result=found_result,
        knowledge=knowledge,
    )

    assert builder_price_answer == (
        price_answer
    )

    print("=" * 60)
    print("Answer Builder ผ่านการทดสอบทั้งหมด")
    print("=" * 60)

    print(
        "Price:",
        price_answer,
    )

    print(
        "Stock:",
        stock_answer,
    )

    print(
        "Shipping:",
        shipping_answer,
    )

    print("=" * 60)


if __name__ == "__main__":
    main()