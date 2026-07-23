"""Tests for the YouTube Live Chat connector."""

from unittest.mock import MagicMock

from app.youtube_live import YouTubeLiveChatConnector


def test_finds_active_live_chat_id() -> None:
    """Return the live chat ID for the active broadcast."""

    youtube = MagicMock()
    execute = (
        youtube.liveBroadcasts
        .return_value
        .list
        .return_value
        .execute
    )
    execute.return_value = {
        "items": [
            {
                "snippet": {
                    "liveChatId": (
                        "chat-123"
                    ),
                },
            },
        ],
    }

    connector = YouTubeLiveChatConnector(
        youtube=youtube,
    )

    live_chat_id = (
        connector.find_active_live_chat_id()
    )

    assert live_chat_id == "chat-123"

    (
        youtube.liveBroadcasts
        .return_value
        .list
        .assert_called_once_with(
            part="snippet",
           broadcastStatus="active",
           broadcastType="all",
           maxResults=1,
        )
    )


def test_returns_none_without_active_broadcast() -> None:
    """Return None when the channel has no active broadcast."""

    youtube = MagicMock()
    execute = (
        youtube.liveBroadcasts
        .return_value
        .list
        .return_value
        .execute
    )
    execute.return_value = {
        "items": [],
    }

    connector = YouTubeLiveChatConnector(
        youtube=youtube,
    )

    assert (
        connector.find_active_live_chat_id()
        is None
    )


def test_lists_new_viewer_messages_once() -> None:
    """Read viewer messages without processing duplicates or owner replies."""

    youtube = MagicMock()
    execute = (
        youtube.liveChatMessages
        .return_value
        .list
        .return_value
        .execute
    )
    execute.return_value = {
        "items": [
            {
                "id": "message-1",
                "snippet": {
                    "type": "textMessageEvent",
                    "textMessageDetails": {
                        "messageText": (
                            "มีรุ่น 5040 ไหม"
                        ),
                    },
                },
                "authorDetails": {
                    "channelId": "viewer-1",
                    "displayName": "Viewer",
                    "isChatOwner": False,
                },
            },
            {
                "id": "message-owner",
                "snippet": {
                    "type": "textMessageEvent",
                    "textMessageDetails": {
                        "messageText": (
                            "ข้อความจากเจ้าของช่อง"
                        ),
                    },
                },
                "authorDetails": {
                    "channelId": "owner",
                    "displayName": "Owner",
                    "isChatOwner": True,
                },
            },
            {
                "id": "membership-1",
                "snippet": {
                    "type": "newSponsorEvent",
                },
                "authorDetails": {
                    "channelId": "viewer-2",
                    "displayName": "Member",
                    "isChatOwner": False,
                },
            },
        ],
        "nextPageToken": "next-token",
        "pollingIntervalMillis": 1500,
    }

    connector = YouTubeLiveChatConnector(
        youtube=youtube,
    )

    first_page = connector.list_messages(
        "chat-123",
    )
    second_page = connector.list_messages(
        "chat-123",
        page_token=(
            first_page.next_page_token
        ),
    )

    assert len(first_page.messages) == 1

    message = first_page.messages[0]

    assert message.message_id == "message-1"
    assert message.text == "มีรุ่น 5040 ไหม"
    assert message.author_channel_id == "viewer-1"
    assert message.author_name == "Viewer"
    assert first_page.next_page_token == "next-token"
    assert (
        first_page.polling_interval_seconds
        == 1.5
    )
    assert second_page.messages == ()


def test_sends_text_message_to_live_chat() -> None:
    """Send a text reply through the YouTube Live Chat API."""

    youtube = MagicMock()
    connector = YouTubeLiveChatConnector(
        youtube=youtube,
    )

    connector.send_message(
        live_chat_id="chat-123",
        text="พบสินค้ารุ่น 5040 ค่ะ",
    )

    (
        youtube.liveChatMessages
        .return_value
        .insert
        .assert_called_once_with(
            part="snippet",
            body={
                "snippet": {
                    "liveChatId": "chat-123",
                    "type": "textMessageEvent",
                    "textMessageDetails": {
                        "messageText": (
                            "พบสินค้ารุ่น 5040 ค่ะ"
                        ),
                    },
                },
            },
        )
    )

    (
        youtube.liveChatMessages
        .return_value
        .insert
        .return_value
        .execute
        .assert_called_once_with()
    )
