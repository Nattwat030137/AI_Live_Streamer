"""Tests for CommerceService."""

from app.services import CommerceService


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