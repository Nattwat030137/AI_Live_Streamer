"""Tests for CommerceService."""

from app.llm.mock_provider import MockProvider
from app.policies.engine import GovernanceEngine
from app.services import (
    CommerceService,
    ResponseGenerationService,
)


def test_product_message_returns_product_intent() -> None:
    service = CommerceService()

    response = service.process_message(
        "มีถ้วย 5040 ไหม"
    )

    assert response.allowed is True
    assert response.metadata["intent"] == "product"
    assert response.metadata["product_attribute"] == "general"
    assert response.metadata["status"] == "intent_analyzed"


def test_price_message_returns_price_intent() -> None:
    service = CommerceService()

    response = service.process_message(
        "ราคาเท่าไหร่"
    )

    assert response.allowed is True
    assert response.metadata["intent"] == "price"
    assert response.metadata["status"] == "intent_analyzed"


def test_material_message_returns_material_attribute() -> None:
    service = CommerceService()

    response = service.process_message(
        "ทำจากวัสดุอะไร"
    )

    assert response.allowed is True
    assert response.metadata["product_attribute"] == "material"
def test_empty_message_is_rejected() -> None:
    service = CommerceService()

    response = service.process_message("   ")

    assert response.allowed is False
    assert response.metadata["status"] == "empty_message"
    assert response.metadata["platform"] == "shopee"
    assert service.memory.turns == []


def test_product_model_is_added_to_search_metadata() -> None:
    service = CommerceService()

    response = service.process_message(
        "มีถ้วย 5040 ไหม"
    )

    assert response.allowed is True
    assert response.metadata["search_status"] == "prepared"
    assert response.metadata["resolved_models"] == ["5040"]
    assert isinstance(
        response.metadata["search_plan"],
        dict,
    )
    assert response.metadata["search_plan"]


def test_customer_message_is_saved_in_memory() -> None:
    service = CommerceService()

    service.process_message(
        "มีถ้วย 5040 ไหม"
    )

    assert len(service.memory.turns) == 1
    assert (
        service.memory.latest_customer_message()
        == "มีถ้วย 5040 ไหม"
    )
    assert service.memory.active_models == ["5040"]
def test_follow_up_message_reuses_active_model() -> None:
    service = CommerceService()

    first_response = service.process_message(
        "มีถ้วย 5040 ไหม"
    )
    follow_up_response = service.process_message(
        "รุ่นนี้ทำจากวัสดุอะไร"
    )

    assert first_response.metadata[
        "resolved_models"
    ] == ["5040"]

    assert follow_up_response.metadata[
        "resolved_models"
    ] == ["5040"]

    assert follow_up_response.metadata[
        "product_attribute"
    ] == "material"

    assert service.memory.active_models == ["5040"]
    assert len(service.memory.turns) == 2
def test_product_knowledge_is_returned() -> None:
    service = CommerceService()

    response = service.process_message(
        "มีถ้วยคัพเค้กรุ่น 5040 ไหม"
    )

    assert response.metadata[
        "knowledge_found"
    ] is True

    assert response.metadata[
        "knowledge_status"
    ] == "found"

    primary_product = response.metadata[
        "primary_product"
    ]

    assert primary_product is not None
    assert primary_product["model"] == "5040"
    assert primary_product["material"] == "กระดาษ"

    assert response.metadata["knowledge"][
        "found"
    ] is True


def test_missing_product_has_no_primary_product() -> None:
    service = CommerceService()

    response = service.process_message(
        "มีสินค้ารุ่น 9999 ไหม"
    )

    assert response.metadata[
        "knowledge_found"
    ] is False

    assert response.metadata[
        "knowledge_status"
    ] == "not_found"

    assert response.metadata[
        "primary_product"
    ] is None

    assert response.metadata["knowledge"][
        "warnings"
    ]


def test_follow_up_reuses_product_knowledge() -> None:
    service = CommerceService()

    service.process_message(
        "มีถ้วยรุ่น 5040 ไหม"
    )

    response = service.process_message(
        "รุ่นนี้ทำจากวัสดุอะไร"
    )

    assert response.metadata[
        "resolved_models"
    ] == ["5040"]

    assert response.metadata[
        "knowledge_found"
    ] is True

    assert response.metadata[
        "primary_product"
    ]["model"] == "5040"

    assert response.metadata[
        "primary_product"
    ]["material"] == "กระดาษ"

def test_optional_generation_returns_real_reply() -> None:
    generation_service = ResponseGenerationService(
        provider=MockProvider(),
    )

    service = CommerceService(
        response_generation_service=(
            generation_service
        ),
    )

    response = service.process_message(
        "รุ่น5040"
    )

    assert response.text != (
        "CommerceService is ready."
    )
    assert "5040" in response.text
    assert "กระดาษ" in response.text

    assert response.metadata[
        "generation_status"
    ] == "generated"

    assert response.metadata[
        "status"
    ] == "response_generated"

    assert response.metadata[
        "governance_status"
    ] == "disabled"

    assert response.metadata[
        "governance"
    ] is None

    assert response.allowed is True
    assert response.risk_score == 0.0
    assert response.compliance_score == 100.0

    assert response.metadata[
        "llm"
    ]["matched_rule"] == "PRODUCT_CATALOG"

    assert (
        service.memory.latest_assistant_message()
        == response.text
    )


def test_default_generation_remains_disabled() -> None:
    service = CommerceService()

    response = service.process_message(
        "รุ่น5040"
    )

    assert response.text == (
        "CommerceService is ready."
    )

    assert response.metadata[
        "generation_status"
    ] == "disabled"

    assert response.metadata["llm"] is None
    assert response.metadata[
        "prompt_builder"
    ] is None

    assert (
        service.memory.latest_assistant_message()
        == ""
    )


def test_optional_governance_evaluates_generated_reply() -> None:
    generation_service = ResponseGenerationService(
        provider=MockProvider(),
    )

    service = CommerceService(
        response_generation_service=(
            generation_service
        ),
        governance_engine=GovernanceEngine(),
    )

    response = service.process_message(
        "รุ่น 5040"
    )

    assert response.allowed is True
    assert response.risk_score == 0.0
    assert response.compliance_score == 100.0

    assert response.metadata[
        "generation_status"
    ] == "generated"

    assert response.metadata[
        "governance_status"
    ] == "evaluated"

    assert response.metadata[
        "status"
    ] == "governance_evaluated"

    governance = response.metadata["governance"]

    assert governance is not None
    assert governance["allowed"] is True
    assert governance["risk_score"] == 0
    assert governance["compliance_score"] == 100
    assert governance["platform"] == "shopee"

    assert (
        governance["sanitized_reply"]
        == response.text
    )

    assert (
        service.memory.latest_assistant_message()
        == response.text
    )
