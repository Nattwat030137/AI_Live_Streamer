"""Regression tests สำหรับ MockLLMProvider."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.search_planner import create_search_plan
from demo.knowledge_retriever import (
    KnowledgeResult,
    ProductCatalogRetriever,
)
from demo.mock_llm import (
    MockLLMProvider,
    MockLLMResponse,
)


@dataclass(frozen=True, slots=True)
class TestCase:
    """ข้อมูล Test Case หนึ่งรายการ."""

    name: str
    customer_message: str
    expected_rule: str
    use_knowledge: bool = False
    text_check: Callable[[str], bool] | None = None


def build_knowledge(
    customer_message: str,
) -> KnowledgeResult:
    """สร้าง KnowledgeResult จากข้อความลูกค้า."""

    plan = create_search_plan(
        customer_message,
        max_tasks=10,
        graph_limit_per_task=4,
    )

    retriever = ProductCatalogRetriever()

    return retriever.retrieve(
        plan
    )


def run_case(
    provider: MockLLMProvider,
    case: TestCase,
) -> MockLLMResponse:
    """รัน Test Case และตรวจผลลัพธ์."""

    knowledge = (
        build_knowledge(
            case.customer_message
        )
        if case.use_knowledge
        else None
    )

    response = provider.generate(
        prompt=(
            "System prompt มีคำว่า ราคา สต็อก "
            "ส่งฟรี และโปรโมชั่น"
        ),
        customer_message=(
            case.customer_message
        ),
        knowledge=knowledge,
    )

    assert response.matched_rule == (
        case.expected_rule
    ), (
        f"{case.name}: expected "
        f"{case.expected_rule!r}, "
        f"got {response.matched_rule!r}"
    )

    assert response.text.strip(), (
        f"{case.name}: response text "
        "ต้องไม่ว่าง"
    )

    assert response.model == (
        provider.MODEL_NAME
    ), (
        f"{case.name}: model ไม่ตรงกับ "
        "MockLLMProvider.MODEL_NAME"
    )

    if case.text_check is not None:
        assert case.text_check(
            response.text
        ), (
            f"{case.name}: response text "
            "ไม่ผ่านเงื่อนไข"
        )

    return response


def main() -> None:
    """รัน Regression Test ทั้งหมด."""

    provider = MockLLMProvider()

    cases = (
        TestCase(
            name="Greeting",
            customer_message="สวัสดีครับ",
            expected_rule="GREETING",
            text_check=lambda text: (
                "สวัสดี" in text
            ),
        ),
        TestCase(
            name="Price",
            customer_message=(
                "5040 ราคาเท่าไหร่"
            ),
            expected_rule="PRICE_REQUEST",
            text_check=lambda text: (
                "ราคา" in text
            ),
        ),
        TestCase(
            name="Stock",
            customer_message=(
                "5040 มีของไหม"
            ),
            expected_rule="STOCK_REQUEST",
            text_check=lambda text: (
                "สต็อก" in text
            ),
        ),
        TestCase(
            name="Shipping",
            customer_message="ส่งฟรีไหม",
            expected_rule="SHIPPING_REQUEST",
            text_check=lambda text: (
                "จัดส่ง" in text
                or "ส่งฟรี" in text
            ),
        ),
        TestCase(
            name="Thank You",
            customer_message="ขอบคุณครับ",
            expected_rule="THANK_YOU",
            text_check=lambda text: (
                "ยินดี" in text
            ),
        ),
        TestCase(
            name="Product",
            customer_message="รุ่น5040",
            expected_rule="PRODUCT_CATALOG",
            use_knowledge=True,
            text_check=lambda text: (
                "5040" in text
                and "กระดาษ" in text
            ),
        ),
        TestCase(
            name="Compatible Bag",
            customer_message=(
                "ถาด5073 ใช้กับถุงซีล"
                "ขนาดเท่าไหร่"
            ),
            expected_rule=(
                "PRODUCT_CATALOG_COMPATIBLE_BAG"
            ),
            use_knowledge=True,
            text_check=lambda text: (
                "5073" in text
                and "12 x 20" in text
            ),
        ),
        TestCase(
            name="Default",
            customer_message="asdfgh123",
            expected_rule="DEFAULT",
            text_check=lambda text: (
                "รายละเอียด" in text
            ),
        ),
    )

    passed = 0

    print("=" * 60)
    print("MockLLM Regression Test")
    print("=" * 60)

    for case in cases:
        response = run_case(
            provider,
            case,
        )

        passed += 1

        print(
            f"{case.name:.<35}"
            "PASS"
        )
        print(
            "  Rule: "
            f"{response.matched_rule}"
        )

    print("=" * 60)
    print(
        f"{passed} / {len(cases)} PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
