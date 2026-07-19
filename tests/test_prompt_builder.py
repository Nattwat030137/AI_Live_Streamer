"""Regression tests สำหรับ CommercePromptBuilder."""

from app.prompt.builder import CommercePromptBuilder, PromptBuildResult
from app.search_planner import create_search_plan
from demo.knowledge_retriever import ProductCatalogRetriever


def main() -> None:
    print("=" * 60)
    print("Commerce Prompt Builder Regression Test")
    print("=" * 60)

    passed = 0
    total = 6

    builder = CommercePromptBuilder()
    retriever = ProductCatalogRetriever()

    message = "รุ่น5040คืออะไร"
    plan = create_search_plan(message)
    knowledge = retriever.retrieve(plan)

    result = builder.build(
        customer_message=message,
        platform="shopee",
        knowledge=knowledge,
        search_plan=plan,
    )

    assert isinstance(result, PromptBuildResult)
    assert result.has_knowledge is True
    assert result.product_count >= 1
    passed += 1
    print("Build result........................PASS")

    assert "รหัสสินค้า: 5040" in result.prompt
    assert "ชื่อสินค้า: ถ้วยคัพเค้ก รุ่น 5040" in result.prompt
    assert "วัสดุ: กระดาษ" in result.prompt
    assert "สี: ขาวและน้ำตาล" in result.prompt
    passed += 1
    print("Knowledge injection.................PASS")

    assert message in result.prompt
    assert "แพลตฟอร์ม: shopee" in result.prompt
    passed += 1
    print("Customer context....................PASS")

    assert "ห้ามเดาราคา" in result.prompt
    assert "ห้ามแต่งข้อมูล" in result.prompt
    assert "Bakery D'Ver" in result.prompt
    passed += 1
    print("Policy section......................PASS")

    unknown = "สินค้ารุ่นที่ไม่มีในระบบ"
    unknown_plan = create_search_plan(unknown)
    unknown_knowledge = retriever.retrieve(unknown_plan)

    unknown_result = builder.build(
        customer_message=unknown,
        platform="line",
        knowledge=unknown_knowledge,
        search_plan=unknown_plan,
    )

    assert unknown_result.has_knowledge is False
    assert unknown_result.product_count == 0
    assert "ไม่พบข้อมูลสินค้าที่ตรงกับคำถาม" in unknown_result.prompt
    passed += 1
    print("No knowledge fallback...............PASS")

    try:
        builder.build(
            customer_message="   ",
            platform="shopee",
            knowledge=unknown_knowledge,
            search_plan=unknown_plan,
        )
    except ValueError as error:
        assert "customer_message" in str(error)
    else:
        raise AssertionError("ข้อความว่างต้องเกิด ValueError")

    passed += 1
    print("Input validation....................PASS")

    print("=" * 60)
    print(f"{passed} / {total} PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
