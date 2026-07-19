"""ทดสอบ Context Engine."""

from app.core.context_engine import (
    ContextEngine,
    ConversationContext,
    enrich_message,
    is_follow_up_message,
    update_context,
)
from app.core.search_executor import (
    SearchExecutionResult,
)
from app.search_planner import SearchPlan


def create_search_result() -> SearchExecutionResult:
    """สร้างผลค้นหาจำลองสำหรับรุ่น 5040."""

    return SearchExecutionResult(
        message=(
            "มีถ้วยคัพเค้กรุ่น 5040 ไหม"
        ),
        search_plan=SearchPlan(
            original_query=(
                "มีถ้วยคัพเค้กรุ่น 5040 ไหม"
            )
        ),
        products=[
            {
                "product_name": (
                    "ถ้วยคัพเค้ก 5040 "
                    "กระดาษคราฟท์สีน้ำตาล"
                ),
                "sku": "คัพเค้ก-5040 Brown",
            }
        ],
        summary={
            "count": 4,
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
        },
        searched_keywords=[
            "5040",
            "คัพเค้ก-5040",
        ],
    )


def main() -> None:
    """ตรวจการบันทึกและเติมบริบท."""

    assert is_follow_up_message(
        "แล้วสีขาวล่ะ"
    )

    assert is_follow_up_message(
        "ราคาเท่าไร"
    )

    assert not is_follow_up_message(
        "มีถ้วยคัพเค้กรุ่น 3830 ไหม"
    )

    context = ConversationContext()

    assert enrich_message(
        message="แล้วสีขาวล่ะ",
        context=context,
    ) == "แล้วสีขาวล่ะ"

    search_result = create_search_result()

    update_context(
        context=context,
        user_message=(
            "มีถ้วยคัพเค้กรุ่น 5040 ไหม"
        ),
        search_result=search_result,
    )

    assert context.has_product_context
    assert context.last_model == "5040"
    assert context.last_keywords[0] == "5040"
    assert context.last_summary[
        "pack_size"
    ] == "48-50 ใบ"

    enriched_color = enrich_message(
        message="แล้วสีขาวล่ะ",
        context=context,
    )

    assert enriched_color == (
        "รุ่น 5040 แล้วสีขาวล่ะ"
    )

    enriched_price = enrich_message(
        message="ราคาเท่าไร",
        context=context,
    )

    assert enriched_price == (
        "รุ่น 5040 ราคาเท่าไร"
    )

    explicit_model = enrich_message(
        message="รุ่น 5040 มีแบบไม่เคลือบไหม",
        context=context,
    )

    assert explicit_model == (
        "รุ่น 5040 มีแบบไม่เคลือบไหม"
    )

    new_product_question = enrich_message(
        message=(
            "มีถ้วยคัพเค้กรุ่น 3830 ไหม"
        ),
        context=context,
    )

    assert new_product_question == (
        "มีถ้วยคัพเค้กรุ่น 3830 ไหม"
    )

    engine = ContextEngine()

    engine.update(
        user_message=(
            "มีถ้วยคัพเค้กรุ่น 5040 ไหม"
        ),
        search_result=search_result,
    )

    assert engine.enrich(
        "แล้วแบบเคลือบล่ะ"
    ) == (
        "รุ่น 5040 แล้วแบบเคลือบล่ะ"
    )

    engine.clear()

    assert not (
        engine.context.has_product_context
    )

    assert engine.enrich(
        "ราคาเท่าไร"
    ) == "ราคาเท่าไร"

    print("=" * 60)
    print("Context Engine ผ่านการทดสอบทั้งหมด")
    print("=" * 60)

    print(
        "ตัวอย่าง:",
        enriched_color,
    )

    print(
        "ตัวอย่าง:",
        enriched_price,
    )

    print("=" * 60)


if __name__ == "__main__":
    main()