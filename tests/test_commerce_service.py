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