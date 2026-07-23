"""Tests for the YouTube Live Chat command."""

import json
from unittest.mock import MagicMock

import httplib2
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError

from app.youtube_chat import (
    _format_youtube_error,
    _normalize_youtube_reply,
    build_argument_parser,
    main,
    run_auto_reply,
    run_read_only,
)
from app.youtube_live import (
    YouTubeChatMessage,
    YouTubeChatPage,
)


def test_read_only_requires_active_chat() -> None:
    """Return failure when no live broadcast is active."""

    connector = MagicMock()
    connector.find_active_live_chat_id.return_value = (
        None
    )
    output_messages: list[str] = []

    exit_code = run_read_only(
        connector=connector,
        output_callback=output_messages.append,
        max_polls=1,
    )

    assert exit_code == 1
    assert output_messages == [
        "No active YouTube Live Chat was found.",
    ]
    connector.list_messages.assert_not_called()


def test_read_only_displays_viewer_message() -> None:
    """Display messages without sending any reply."""

    connector = MagicMock()
    connector.find_active_live_chat_id.return_value = (
        "chat-123"
    )
    connector.list_messages.return_value = (
        YouTubeChatPage(
            messages=(
                YouTubeChatMessage(
                    message_id="message-1",
                    text="มีรุ่น 5040 ไหม",
                    author_channel_id=(
                        "viewer-1"
                    ),
                    author_name="Viewer",
                ),
            ),
            next_page_token="next-token",
            polling_interval_seconds=1.5,
        )
    )
    output_messages: list[str] = []

    exit_code = run_read_only(
        connector=connector,
        output_callback=output_messages.append,
        sleep_callback=MagicMock(),
        max_polls=1,
    )

    assert exit_code == 0
    assert output_messages == [
        "Connected to YouTube Live Chat.",
        "YouTube Viewer: มีรุ่น 5040 ไหม",
    ]
    connector.send_message.assert_not_called()

def test_auto_reply_skips_existing_messages() -> None:
    """Skip chat history and reply only to a new message."""

    connector = MagicMock()
    controller = MagicMock()
    connector.find_active_live_chat_id.return_value = (
        "chat-123"
    )

    existing_page = YouTubeChatPage(
        messages=(
            YouTubeChatMessage(
                message_id="message-old",
                text="ข้อความก่อนเริ่มโปรแกรม",
                author_channel_id="viewer-old",
                author_name="Old Viewer",
            ),
        ),
        next_page_token="token-1",
        polling_interval_seconds=1.0,
    )
    new_page = YouTubeChatPage(
        messages=(
            YouTubeChatMessage(
                message_id="message-new",
                text="มีรุ่น 5040 ไหม",
                author_channel_id="viewer-1",
                author_name="Viewer",
            ),
        ),
        next_page_token="token-2",
        polling_interval_seconds=1.0,
    )
    connector.list_messages.side_effect = [
        existing_page,
        new_page,
    ]

    controller.process_message.return_value = (
        MagicMock(
            allowed=True,
            text="พบสินค้ารุ่น 5040 ค่ะ",
        )
    )
    output_messages: list[str] = []

    exit_code = run_auto_reply(
        connector=connector,
        controller=controller,
        output_callback=output_messages.append,
        sleep_callback=MagicMock(),
        max_polls=1,
    )

    assert exit_code == 0

    controller.process_message.assert_called_once_with(
        "มีรุ่น 5040 ไหม",
        platform="youtube",
        speak_response=False,
        metadata={
            "youtube_message_id": (
                "message-new"
            ),
            "youtube_author_channel_id": (
                "viewer-1"
            ),
        },
    )

    connector.send_message.assert_called_once_with(
        live_chat_id="chat-123",
        text="พบสินค้ารุ่น 5040 ค่ะ",
    )

    assert all(
        "message-old" not in message
        for message in output_messages
    )


def test_cli_accepts_auto_reply_mode() -> None:
    """Accept an explicit auto-reply command mode."""

    parser = build_argument_parser()

    arguments = parser.parse_args(
        [
            "--credentials",
            "client.json",
            "--token",
            "token.json",
            "--auto-reply",
        ]
    )

    assert arguments.auto_reply is True
    assert arguments.read_only is False


def test_youtube_reply_is_limited_to_200_characters() -> None:
    """Limit generated replies before sending them to YouTube."""

    reply = _normalize_youtube_reply(
        "ก" * 250
    )

    assert len(reply) == 200
    assert reply.endswith("...")


def test_formats_quota_error_safely() -> None:
    """Return a safe message when YouTube quota is exhausted."""

    response = httplib2.Response(
        {
            "status": "403",
            "reason": "Forbidden",
        }
    )
    content = json.dumps(
        {
            "error": {
                "code": 403,
                "message": (
                    "internal quota detail"
                ),
                "errors": [
                    {
                        "reason": (
                            "quotaExceeded"
                        ),
                    },
                ],
            },
        }
    ).encode("utf-8")
    error = HttpError(
        response,
        content,
    )

    message = _format_youtube_error(
        error
    )

    assert message == (
        "YouTube API quota has been reached. "
        "Try again after the quota resets."
    )
    assert (
        "internal quota detail"
        not in message
    )


def test_main_handles_expired_authorization(
    monkeypatch,
    capsys,
) -> None:
    """Stop safely when OAuth authorization has expired."""

    authorization_error = RefreshError(
        "internal invalid grant detail"
    )
    failing_service = MagicMock(
        side_effect=authorization_error,
    )
    monkeypatch.setattr(
        "app.youtube_chat."
        "build_youtube_service",
        failing_service,
    )

    exit_code = main(
        [
            "--credentials",
            "client.json",
            "--token",
            "token.json",
            "--read-only",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 2
    assert (
        "YouTube authorization expired. "
        "Authorize the application again."
        in output
    )
    assert (
        "internal invalid grant detail"
        not in output
    )
