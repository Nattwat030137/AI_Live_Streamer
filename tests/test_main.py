"""Tests for the AI Live Streamer console entry point."""

from app.live_controller import LiveCommerceController
from app.main import run_console


def test_console_routes_message_through_controller() -> None:
    input_values = iter([
        "รุ่น 5040",
        "exit",
    ])
    output_messages: list[str] = []
    spoken_messages: list[str] = []

    controller = LiveCommerceController(
        provider_name="mock",
        voice_callback=spoken_messages.append,
    )

    run_console(
        controller,
        input_callback=lambda _: next(
            input_values
        ),
        output_callback=output_messages.append,
    )

    assert any(
        message.startswith("AI: ")
        and "5040" in message
        for message in output_messages
    )
    assert len(spoken_messages) == 1
    assert "5040" in spoken_messages[0]
    assert len(
        controller.commerce_service.memory.turns
    ) == 2


def test_console_skips_empty_message() -> None:
    input_values = iter([
        "   ",
        "q",
    ])
    output_messages: list[str] = []

    controller = LiveCommerceController(
        provider_name="mock",
    )

    run_console(
        controller,
        input_callback=lambda _: next(
            input_values
        ),
        output_callback=output_messages.append,
    )

    assert (
        "AI: กรุณาพิมพ์ข้อความก่อนนะคะ"
        in output_messages
    )
    assert controller.commerce_service.memory.turns == []
