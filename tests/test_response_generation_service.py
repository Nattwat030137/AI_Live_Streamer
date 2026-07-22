"""Tests for ResponseGenerationService."""

from app.llm.mock_provider import MockProvider
from app.services import (
    CommerceService,
    ResponseGenerationResult,
    ResponseGenerationService,
)


def generate_response(
    customer_message: str,
) -> ResponseGenerationResult:
    """Prepare commerce data and generate a mock response."""

    commerce = CommerceService()

    pipeline = commerce.prepare_pipeline(
        customer_message=customer_message,
        platform="shopee",
    )

    service = ResponseGenerationService(
        provider=MockProvider(),
    )

    return service.generate(
        customer_message=customer_message,
        platform="shopee",
        knowledge=pipeline.knowledge,
        search_plan=(
            pipeline.planning.resolved_search_plan
        ),
        conversation_context=(
            commerce.memory.build_context_text()
        ),
        product_attribute=(
            pipeline.product_attribute.value
        ),
        metadata={
            "test_source": "unit_test",
        },
    )


def test_generates_product_response() -> None:
    result = generate_response(
        "รุ่น5040"
    )

    assert isinstance(
        result,
        ResponseGenerationResult,
    )
    assert result.response.provider == "mock"
    assert result.response.matched_rule == (
        "PRODUCT_CATALOG"
    )
    assert "5040" in result.response.text
    assert "กระดาษ" in result.response.text

    assert result.prompt.has_knowledge is True
    assert result.prompt.product_count == 1


def test_generates_price_response() -> None:
    result = generate_response(
        "5040 ราคาเท่าไหร่"
    )

    assert result.response.matched_rule == (
        "PRICE_REQUEST"
    )
    assert "ราคา" in result.response.text
    assert result.request.customer_message == (
        "5040 ราคาเท่าไหร่"
    )


def test_request_contains_pipeline_metadata() -> None:
    result = generate_response(
        "ถาด5073 ใช้กับถุงซีลขนาดเท่าไหร่"
    )

    metadata = result.request.metadata

    assert metadata["test_source"] == "unit_test"
    assert metadata["platform"] == "shopee"
    assert metadata["knowledge"].found is True
    assert metadata["product_attribute"] == "bag"
    assert "search_plan" in metadata
    assert "prompt_builder" in metadata

    assert result.response.matched_rule == (
        "PRODUCT_CATALOG_COMPATIBLE_BAG"
    )