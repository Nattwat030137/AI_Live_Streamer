"""Regression tests for MockLLMProvider."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pytest

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
class MockLLMCase:
    """One Mock LLM regression case."""

    name: str
    customer_message: str
    expected_rule: str
    use_knowledge: bool = False
    text_check: Callable[[str], bool] | None = None


def build_knowledge(
    customer_message: str,
) -> KnowledgeResult:
    """Build product knowledge from a customer message."""

    plan = create_search_plan(
        customer_message,
        max_tasks=10,
        graph_limit_per_task=4,
    )

    return ProductCatalogRetriever().retrieve(
        plan
    )


def run_case(
    provider: MockLLMProvider,
    case: MockLLMCase,
) -> MockLLMResponse:
    """Run and validate one regression case."""

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
        customer_message=case.customer_message,
        knowledge=knowledge,
    )

    assert response.matched_rule == (
        case.expected_rule
    ), (
        f"{case.name}: expected "
        f"{case.expected_rule!r}, "
        f"got {response.matched_rule!r}"
    )

    assert response.text.strip()
    assert response.model == provider.MODEL_NAME

    if case.text_check is not None:
        assert case.text_check(
            response.text
        )

    return response
CASES = (
    MockLLMCase(
        name="Greeting",
        customer_message="สวัสดีครับ",
        expected_rule="GREETING",
        text_check=lambda text: (
            "สวัสดี" in text
        ),
    ),
    MockLLMCase(
        name="Price",
        customer_message="5040 ราคาเท่าไหร่",
        expected_rule="PRICE_REQUEST",
        text_check=lambda text: (
            "ราคา" in text
        ),
    ),
    MockLLMCase(
        name="Stock",
        customer_message="5040 มีของไหม",
        expected_rule="STOCK_REQUEST",
        text_check=lambda text: (
            "สต็อก" in text
        ),
    ),
    MockLLMCase(
        name="Shipping",
        customer_message="ส่งฟรีไหม",
        expected_rule="SHIPPING_REQUEST",
        text_check=lambda text: (
            "จัดส่ง" in text
            or "ส่งฟรี" in text
        ),
    ),
    MockLLMCase(
        name="Thank You",
        customer_message="ขอบคุณครับ",
        expected_rule="THANK_YOU",
        text_check=lambda text: (
            "ยินดี" in text
        ),
    ),
        MockLLMCase(
        name="Product",
        customer_message="รุ่น5040",
        expected_rule="PRODUCT_CATALOG",
        use_knowledge=True,
        text_check=lambda text: (
            "5040" in text
            and "กระดาษ" in text
        ),
    ),
    MockLLMCase(
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
    MockLLMCase(
        name="Default",
        customer_message="asdfgh123",
        expected_rule="DEFAULT",
        text_check=lambda text: (
            "รายละเอียด" in text
        ),
    ),
)


@pytest.mark.parametrize(
    "case",
    CASES,
    ids=[
        case.name
        for case in CASES
    ],
)
def test_mock_llm_case(
    case: MockLLMCase,
) -> None:
    """Expose every regression case to pytest."""

    run_case(
        MockLLMProvider(),
        case,
    )


def test_missing_model_returns_specific_not_found_response() -> None:
    """Return a direct answer when a requested model is missing."""

    customer_message = "มีสินค้ารุ่น 9999 ไหม"
    knowledge = build_knowledge(
        customer_message
    )

    response = MockLLMProvider().generate(
        prompt="",
        customer_message=customer_message,
        knowledge=knowledge,
    )

    assert knowledge.found is False
    assert knowledge.searched_models == [
        "9999"
    ]
    assert response.matched_rule == (
        "PRODUCT_NOT_FOUND"
    )
    assert response.response_type == (
        "knowledge_product_not_found"
    )
    assert "ไม่พบ" in response.text
    assert "9999" in response.text


def main() -> None:
    """Run the regression cases as a console script."""

    provider = MockLLMProvider()
    passed = 0

    print("=" * 60)
    print("MockLLM Regression Test")
    print("=" * 60)

    for case in CASES:
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
        f"{passed} / {len(CASES)} PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()