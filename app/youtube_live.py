"""YouTube Live Chat integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(
    frozen=True,
    slots=True,
)
class YouTubeChatMessage:
    """One normalized viewer chat message."""

    message_id: str
    text: str
    author_channel_id: str
    author_name: str


@dataclass(
    frozen=True,
    slots=True,
)
class YouTubeChatPage:
    """One page returned by the Live Chat API."""

    messages: tuple[
        YouTubeChatMessage,
        ...,
    ]
    next_page_token: str | None
    polling_interval_seconds: float


class YouTubeLiveChatConnector:
    """Read and write an active YouTube Live Chat."""

    def __init__(
        self,
        *,
        youtube: Any,
    ) -> None:
        """Initialize the connector with a YouTube API client."""

        self.youtube = youtube
        self._seen_message_ids: set[str] = set()

    def find_active_live_chat_id(
        self,
    ) -> str | None:
        """Return the active live chat ID for this channel."""

        response = (
            self.youtube
            .liveBroadcasts()
            .list(
                part="snippet",
                broadcastStatus="active",
                broadcastType="all",
                maxResults=1,
            )
            .execute()
        )

        items = response.get(
            "items",
            [],
        )

        if not items:
            return None

        snippet = items[0].get(
            "snippet",
            {},
        )
        live_chat_id = snippet.get(
            "liveChatId"
        )

        if not live_chat_id:
            return None

        return str(live_chat_id)

    def list_messages(
        self,
        live_chat_id: str,
        *,
        page_token: str | None = None,
    ) -> YouTubeChatPage:
        """Return unseen text messages from viewers."""

        normalized_chat_id = (
            live_chat_id.strip()
        )

        if not normalized_chat_id:
            raise ValueError(
                "live_chat_id is required"
            )

        request_arguments: dict[
            str,
            Any,
        ] = {
            "part": (
                "id,snippet,authorDetails"
            ),
            "liveChatId": (
                normalized_chat_id
            ),
            "maxResults": 200,
        }

        if page_token:
            request_arguments[
                "pageToken"
            ] = page_token

        response = (
            self.youtube
            .liveChatMessages()
            .list(
                **request_arguments
            )
            .execute()
        )

        messages: list[
            YouTubeChatMessage
        ] = []

        for item in response.get(
            "items",
            [],
        ):
            message_id = str(
                item.get(
                    "id",
                    "",
                )
            ).strip()

            if (
                not message_id
                or message_id
                in self._seen_message_ids
            ):
                continue

            self._seen_message_ids.add(
                message_id
            )

            snippet = item.get(
                "snippet",
                {},
            )

            if (
                snippet.get("type")
                != "textMessageEvent"
            ):
                continue

            author = item.get(
                "authorDetails",
                {},
            )

            if author.get(
                "isChatOwner",
                False,
            ):
                continue

            text = str(
                snippet.get(
                    "textMessageDetails",
                    {},
                ).get(
                    "messageText",
                    "",
                )
            ).strip()

            if not text:
                continue

            messages.append(
                YouTubeChatMessage(
                    message_id=message_id,
                    text=text,
                    author_channel_id=str(
                        author.get(
                            "channelId",
                            "",
                        )
                    ),
                    author_name=str(
                        author.get(
                            "displayName",
                            "",
                        )
                    ),
                )
            )

        next_page_token = response.get(
            "nextPageToken"
        )
        polling_interval_ms = float(
            response.get(
                "pollingIntervalMillis",
                2000,
            )
        )

        return YouTubeChatPage(
            messages=tuple(messages),
            next_page_token=(
                str(next_page_token)
                if next_page_token
                else None
            ),
            polling_interval_seconds=max(
                polling_interval_ms
                / 1000.0,
                0.1,
            ),
        )

    def send_message(
        self,
        *,
        live_chat_id: str,
        text: str,
    ) -> None:
        """Send one text reply to the active live chat."""

        normalized_chat_id = (
            live_chat_id.strip()
        )
        normalized_text = text.strip()

        if not normalized_chat_id:
            raise ValueError(
                "live_chat_id is required"
            )

        if not normalized_text:
            raise ValueError(
                "text is required"
            )

        if len(normalized_text) > 200:
            raise ValueError(
                "YouTube chat text exceeds "
                "200 characters"
            )

        (
            self.youtube
            .liveChatMessages()
            .insert(
                part="snippet",
                body={
                    "snippet": {
                        "liveChatId": (
                            normalized_chat_id
                        ),
                        "type": (
                            "textMessageEvent"
                        ),
                        "textMessageDetails": {
                            "messageText": (
                                normalized_text
                            ),
                        },
                    },
                },
            )
            .execute()
        )