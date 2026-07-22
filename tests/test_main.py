"""Tests for the AI Live Streamer console entry point."""

import json

from app.live_controller import LiveCommerceController
from app.main import (
    create_live_controller,
    display_runtime_status,
    main,
    resolve_voice_enabled,
    run_console,
)
from app.runtime_config import RuntimeStatus


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

def test_voice_flag_parses_common_values() -> None:
    for disabled_value in (
        "0",
        "false",
        "NO",
        "off",
    ):
        assert resolve_voice_enabled(
            disabled_value
        ) is False

    for enabled_value in (
        "1",
        "true",
        "YES",
        "on",
    ):
        assert resolve_voice_enabled(
            enabled_value
        ) is True


def test_controller_can_be_created_without_voice() -> None:
    controller = create_live_controller(
        provider_name="mock",
        voice_enabled=False,
    )

    response = controller.process_message(
        "รุ่น 5040",
    )

    assert controller.voice_callback is None
    assert response.allowed is True
    assert "5040" in response.text

def test_runtime_status_display_hides_api_key() -> None:
    output_messages: list[str] = []
    status = RuntimeStatus(
        provider_name="openai",
        voice_enabled=True,
        api_key_configured=True,
        product_database_exists=True,
        audio_directory_exists=True,
    )

    display_runtime_status(
        status,
        output_callback=output_messages.append,
    )

    assert "LLM provider: openai" in output_messages
    assert "Voice: enabled" in output_messages
    assert (
        "API key: configured"
        in output_messages
    )
    assert all(
        "sk-" not in message
        for message in output_messages
    )


def test_mock_runtime_reports_api_key_not_required() -> None:
    """Report that an API key is unnecessary for mock-only runtime."""

    output_messages: list[str] = []
    status = RuntimeStatus(
        provider_name="mock",
        voice_enabled=False,
        api_key_configured=True,
        product_database_exists=True,
        audio_directory_exists=True,
    )

    display_runtime_status(
        status,
        output_callback=output_messages.append,
    )

    assert status.api_key_required is False
    assert (
        "API key: not required"
        in output_messages
    )


def test_main_check_exits_without_console(
    monkeypatch,
) -> None:
    output_messages: list[str] = []

    monkeypatch.setenv(
        "LLM_PROVIDER",
        "mock",
    )
    monkeypatch.setenv(
        "VOICE_ENABLED",
        "false",
    )

    exit_code = main(
        ["--check"],
        output_callback=output_messages.append,
    )

    assert exit_code == 0
    assert "LLM provider: mock" in output_messages
    assert "Voice: disabled" in output_messages


def test_main_check_returns_one_when_not_ready(
    monkeypatch,
) -> None:
    output_messages: list[str] = []

    runtime_status = RuntimeStatus(
        provider_name="mock",
        voice_enabled=False,
        api_key_configured=False,
        product_database_exists=False,
        audio_directory_exists=False,
        errors=(
            "Product database is missing.",
        ),
        warnings=(),
    )

    monkeypatch.setattr(
        "app.main.inspect_runtime_config",
        lambda: runtime_status,
    )

    exit_code = main(
        ["--check"],
        output_callback=output_messages.append,
    )

    assert exit_code == 1
    assert any(
        message.startswith("Error:")
        for message in output_messages
    )


def test_main_check_json_returns_machine_readable_status(
    monkeypatch,
) -> None:
    output_messages: list[str] = []

    monkeypatch.setenv(
        "LLM_PROVIDER",
        "mock",
    )
    monkeypatch.setenv(
        "VOICE_ENABLED",
        "false",
    )

    exit_code = main(
        ["--check-json"],
        output_callback=output_messages.append,
    )

    assert exit_code == 0
    assert len(output_messages) == 1

    status_data = json.loads(
        output_messages[0]
    )

    assert status_data["ready"] is True
    assert status_data["provider"] == "mock"
    assert status_data["voice_enabled"] is False
    assert status_data["api_key_required"] is False
    assert "api_key" not in status_data


def test_main_check_json_reports_not_ready(
    monkeypatch,
) -> None:
    output_messages: list[str] = []

    runtime_status = RuntimeStatus(
        provider_name="openai",
        voice_enabled=True,
        api_key_configured=False,
        product_database_exists=False,
        audio_directory_exists=True,
        errors=(
            "OpenAI API key is missing.",
            "Product database is missing.",
        ),
        warnings=(),
    )

    monkeypatch.setattr(
        "app.main.inspect_runtime_config",
        lambda: runtime_status,
    )

    exit_code = main(
        ["--check-json"],
        output_callback=output_messages.append,
    )

    assert exit_code == 1
    assert len(output_messages) == 1

    status_data = json.loads(
        output_messages[0]
    )

    assert status_data["ready"] is False
    assert status_data["provider"] == "openai"
    assert status_data["api_key_configured"] is False
    assert status_data["api_key_required"] is True
    assert len(status_data["errors"]) == 2
    assert "api_key" not in status_data


def test_main_help_skips_runtime_validation(
    monkeypatch,
) -> None:
    output_messages: list[str] = []

    def fail_runtime_validation():
        raise AssertionError(
            "Runtime validation should not run for --help."
        )

    monkeypatch.setattr(
        "app.main.inspect_runtime_config",
        fail_runtime_validation,
    )

    exit_code = main(
        ["--help"],
        output_callback=output_messages.append,
    )

    assert exit_code == 0
    assert any(
        message.startswith("Usage:")
        for message in output_messages
    )
    assert any(
        "--check" in message
        for message in output_messages
    )
    assert any(
        "--check-json" in message
        for message in output_messages
    )


def test_main_rejects_unknown_argument(
    monkeypatch,
) -> None:
    output_messages: list[str] = []

    def fail_runtime_validation():
        raise AssertionError(
            "Invalid arguments should fail before runtime validation."
        )

    monkeypatch.setattr(
        "app.main.inspect_runtime_config",
        fail_runtime_validation,
    )

    exit_code = main(
        ["--unknown"],
        output_callback=output_messages.append,
    )

    assert exit_code == 2
    assert (
        "Unknown argument: --unknown"
        in output_messages
    )
    assert any(
        message.startswith("Usage:")
        for message in output_messages
    )
