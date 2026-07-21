"""Integration tests สำหรับ Bakery Demo ที่ใช้ SQLite Runtime."""

from __future__ import annotations

from unittest.mock import Mock

from demo.bakery_demo import BakeryDemo
from demo.sample_data import DemoScenario


def assert_common_report(
    report,
) -> None:
    """ตรวจค่าพื้นฐานที่ทุก Scenario ต้องมี."""

    assert report.customer_message.strip()
    assert report.platform.strip()
    assert report.llm_reply.strip()
    assert report.final_reply.strip()

    assert report.governance_allowed is True
    assert report.risk_score == 0
    assert report.compliance_score == 100

    assert report.execution_time_ms >= 0

    governance_data = (
        report.metadata.get(
            "governance",
            {},
        )
    )

    assert isinstance(
        governance_data,
        dict,
    )


def test_commerce_dependencies_are_shared(
    demo: BakeryDemo,
) -> None:
    assert (
        demo.commerce_service
        .response_generation_service
        is demo.response_generation
    )

    assert (
        demo.commerce_service.governance_engine
        is demo.governance
    )


def test_prepared_context_preserves_pipeline(
    demo: BakeryDemo,
) -> None:
    scenario = DemoScenario(
        scenario_id="prepared-context-test",
        title="Prepared Context Test",
        customer_message="รุ่น 5040",
        platform="shopee",
        expected_rule="PRODUCT_CATALOG",
    )

    prepared = demo._prepare_context(
        scenario
    )

    assert prepared.pipeline.customer_message == (
        "รุ่น 5040"
    )
    assert prepared.pipeline.platform == "shopee"
    assert (
        prepared.knowledge_result
        is prepared.pipeline.knowledge
    )


def test_run_scenario_uses_commerce_response(
    demo: BakeryDemo,
) -> None:
    original_process = (
        demo.commerce_service
        .process_prepared_pipeline
    )
    process_spy = Mock(
        wraps=original_process,
    )
    demo.commerce_service.process_prepared_pipeline = (
        process_spy
    )

    scenario = DemoScenario(
        scenario_id="commerce-response-test",
        title="Commerce Response Test",
        customer_message="รุ่น 5040",
        platform="shopee",
        expected_rule="PRODUCT_CATALOG",
    )

    report = demo.run_scenario(
        scenario
    )

    process_spy.assert_called_once()
    assert report.matched_rule == "PRODUCT_CATALOG"
    assert report.governance_allowed is True


def test_product_5040(
    demo: BakeryDemo,
) -> None:
    """ทดสอบข้อมูลสินค้ารุ่น 5040 ผ่าน Pipeline จริง."""

    scenario = DemoScenario(
        scenario_id="sqlite-product-5040",
        title="SQLite Product 5040",
        customer_message="รุ่น5040",
        platform="shopee",
        expected_rule="PRODUCT_CATALOG",
    )

    report = demo.run_scenario(
        scenario
    )

    assert len(demo.memory.turns) == 2

    assert [
        turn.role
        for turn in demo.memory.turns
    ] == [
        "customer",
        "assistant",
    ]

    assert (
        demo.memory.latest_assistant_message()
        == report.llm_reply
    )

    assert_common_report(
        report
    )

    assert report.matched_rule == (
        "PRODUCT_CATALOG"
    )

    assert report.intent == (
        "product_information"
    )

    assert report.strategy == (
        "answer_product_information"
    )

    assert "5040" in report.final_reply
    assert "กระดาษ" in report.final_reply

    search_plan = report.metadata[
        "search_plan"
    ]

    assert "5040" in search_plan[
        "extracted_models"
    ]


def test_compatible_bag_5073(
    demo: BakeryDemo,
) -> None:
    """ทดสอบขนาดถุงของรุ่น 5073 ผ่าน Pipeline จริง."""

    scenario = DemoScenario(
        scenario_id="sqlite-bag-5073",
        title="SQLite Compatible Bag 5073",
        customer_message=(
            "ถาด5073 ใช้กับถุงซีล"
            "ขนาดเท่าไหร่"
        ),
        platform="shopee",
        expected_rule=(
            "PRODUCT_CATALOG_COMPATIBLE_BAG"
        ),
    )

    report = demo.run_scenario(
        scenario
    )

    assert_common_report(
        report
    )

    assert report.matched_rule == (
        "PRODUCT_CATALOG_COMPATIBLE_BAG"
    )

    assert report.intent == (
        "product_information"
    )

    assert report.strategy == (
        "answer_compatible_packaging"
    )

    assert "5073" in report.final_reply
    assert "12 x 20" in report.final_reply

    search_plan = report.metadata[
        "search_plan"
    ]

    assert "5073" in search_plan[
        "extracted_models"
    ]


def test_price_priority(
    demo: BakeryDemo,
) -> None:
    """ทดสอบว่า Price Intent มาก่อน Product Knowledge."""

    scenario = DemoScenario(
        scenario_id="sqlite-price-priority",
        title="SQLite Price Priority",
        customer_message=(
            "5040 ราคาเท่าไหร่"
        ),
        platform="shopee",
        expected_rule="PRICE_REQUEST",
    )

    report = demo.run_scenario(
        scenario
    )

    assert_common_report(
        report
    )

    assert report.matched_rule == (
        "PRICE_REQUEST"
    )

    assert report.strategy == (
        "human_handoff_for_price"
    )

    assert "ราคา" in report.final_reply


def test_stock_priority(
    demo: BakeryDemo,
) -> None:
    """ทดสอบว่า Stock Intent มาก่อน Product Knowledge."""

    scenario = DemoScenario(
        scenario_id="sqlite-stock-priority",
        title="SQLite Stock Priority",
        customer_message="5040 มีของไหม",
        platform="shopee",
        expected_rule="STOCK_REQUEST",
    )

    report = demo.run_scenario(
        scenario
    )

    assert_common_report(
        report
    )

    assert report.matched_rule == (
        "STOCK_REQUEST"
    )

    assert report.strategy == (
        "human_handoff_for_stock"
    )

    assert "สต็อก" in report.final_reply


def test_greeting(
    demo: BakeryDemo,
) -> None:
    """ทดสอบ Greeting ไม่ถูก Prompt ปนเป็น Price Intent."""

    scenario = DemoScenario(
        scenario_id="sqlite-greeting",
        title="SQLite Greeting",
        customer_message="สวัสดีครับ",
        platform="shopee",
        expected_rule="GREETING",
    )

    report = demo.run_scenario(
        scenario
    )

    assert_common_report(
        report
    )

    assert report.matched_rule == (
        "GREETING"
    )

    assert "สวัสดี" in report.final_reply

def test_demo_and_commerce_share_memory(
    demo: BakeryDemo,
) -> None:
    """ยืนยันว่า Demo และ CommerceService ใช้ Memory เดียวกัน."""

    assert (
        demo.commerce_service.memory
        is demo.memory
    )


def test_knowledge_is_retrieved_once(
    demo: BakeryDemo,
    monkeypatch,
) -> None:
    """ยืนยันว่า Scenario หนึ่งรายการค้น Knowledge ครั้งเดียว."""

    retriever = (
        demo.commerce_service.knowledge_retriever
    )
    original_retrieve = retriever.retrieve
    call_count = 0

    def counting_retrieve(plan):
        nonlocal call_count

        call_count += 1

        return original_retrieve(
            plan
        )

    monkeypatch.setattr(
        retriever,
        "retrieve",
        counting_retrieve,
    )

    scenario = DemoScenario(
        scenario_id="single-retrieval-5040",
        title="Single Knowledge Retrieval",
        customer_message="รุ่น5040",
        platform="shopee",
        expected_rule="PRODUCT_CATALOG",
    )

    report = demo.run_scenario(
        scenario
    )

    assert report.matched_rule == (
        "PRODUCT_CATALOG"
    )
    assert call_count == 1

def test_response_is_generated_once(
    demo: BakeryDemo,
    monkeypatch,
) -> None:
    """ยืนยันว่า Scenario หนึ่งรายการสร้างคำตอบครั้งเดียว."""

    service = demo.response_generation
    original_generate = service.generate
    call_count = 0

    def counting_generate(**kwargs):
        nonlocal call_count

        call_count += 1

        return original_generate(
            **kwargs
        )

    monkeypatch.setattr(
        service,
        "generate",
        counting_generate,
    )

    scenario = DemoScenario(
        scenario_id="single-response-generation",
        title="Single Response Generation",
        customer_message="สวัสดีครับ",
        platform="shopee",
        expected_rule="GREETING",
    )

    report = demo.run_scenario(
        scenario
    )

    assert report.matched_rule == "GREETING"
    assert call_count == 1
    assert service.provider is demo.llm


def main() -> None:
    """รัน Bakery Demo SQLite Integration Tests."""

    demo = BakeryDemo()

    tests = (
        (
            "Product 5040",
            test_product_5040,
        ),
        (
            "Compatible Bag 5073",
            test_compatible_bag_5073,
        ),
        (
            "Price Priority",
            test_price_priority,
        ),
        (
            "Stock Priority",
            test_stock_priority,
        ),
        (
            "Greeting",
            test_greeting,
        ),
    )

    passed = 0

    print("=" * 60)
    print(
        "Bakery Demo SQLite Integration Test"
    )
    print("=" * 60)

    for name, test_function in tests:
        test_function(
            demo
        )

        passed += 1

        print(
            f"{name:.<38}"
            "PASS"
        )

    print("=" * 60)
    print(
        f"{passed} / {len(tests)} PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
