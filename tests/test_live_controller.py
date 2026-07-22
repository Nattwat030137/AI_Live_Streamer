"""Tests for LiveCommerceController."""

import logging

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
    assert response.metadata[
        "voice_status"
    ] == "spoken"
    assert response.metadata[
        "voice_error"
    ] is None


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
    assert response.metadata[
        "voice_status"
    ] == "disabled"
    assert response.metadata[
        "voice_error"
    ] is None


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
    assert response.metadata[
        "voice_status"
    ] == "skipped"
    assert response.metadata[
        "voice_error"
    ] is None


def test_controller_keeps_response_when_voice_fails() -> None:
    def failing_voice(_: str) -> None:
        raise RuntimeError(
            "Speaker is unavailable."
        )

    controller = LiveCommerceController(
        provider_name="mock",
        voice_callback=failing_voice,
    )

    response = controller.process_message(
        "รุ่น 5040",
    )

    assert response.allowed is True
    assert "5040" in response.text
    assert response.metadata[
        "voice_status"
    ] == "failed"
    assert response.metadata[
        "voice_error"
    ] == "RuntimeError"


def test_controller_logs_safe_processing_summary(
    caplog,
) -> None:
    caplog.set_level(logging.INFO)

    controller = LiveCommerceController(
        provider_name="mock",
    )

    response = controller.process_message(
        "รุ่น 5040",
        speak_response=False,
    )

    log_text = "\n".join(
        caplog.messages
    )

    assert "Live commerce processed" in log_text
    assert "status=governance_evaluated" in log_text
    assert "voice_status=disabled" in log_text
    assert "รุ่น 5040" not in log_text
    assert response.text not in log_text
