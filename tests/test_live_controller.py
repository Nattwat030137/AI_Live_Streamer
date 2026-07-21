"""Tests for LiveCommerceController."""

from app.live_controller import LiveCommerceController


def test_controller_processes_and_speaks_reply() -> None:
    spoken_messages: list[str] = []
    controller = LiveCommerceController(
        provider_name="mock",
        voice_callback=spoken_messages.append,
    )

    response = controller.process_message(
        "รุ่น 5040",
        platform="shopee",
    )

    assert response.allowed is True
    assert response.metadata[
        "status"
    ] == "governance_evaluated"
    assert "5040" in response.text
    assert spoken_messages == [response.text]


def test_controller_can_disable_voice() -> None:
    spoken_messages: list[str] = []
    controller = LiveCommerceController(
        provider_name="mock",
        voice_callback=spoken_messages.append,
    )

    response = controller.process_message(
        "รุ่น 5040",
        speak_response=False,
    )

    assert response.allowed is True
    assert spoken_messages == []


def test_controller_rejects_empty_message_without_voice() -> None:
    spoken_messages: list[str] = []
    controller = LiveCommerceController(
        provider_name="mock",
        voice_callback=spoken_messages.append,
    )

    response = controller.process_message(
        "   ",
    )

    assert response.allowed is False
    assert response.metadata[
        "status"
    ] == "empty_message"
    assert spoken_messages == []
    assert controller.commerce_service.memory.turns == []
